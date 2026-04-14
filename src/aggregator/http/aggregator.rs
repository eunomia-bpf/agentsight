//! HTTP Connection Aggregator - correlates HTTP requests with responses
//
//! This module implements the HTTP Aggregator specification for correlating
//! parsed HTTP requests and responses into complete request/response pairs.

use std::num::NonZeroUsize;
use lru::LruCache;
use crate::config::DEFAULT_CONNECTION_CAPACITY;
use crate::probes::sslsniff::SslEvent;
use crate::parser::http::{ParsedRequest, ParsedResponse};
use crate::parser::sse::ParsedSseEvent;
use super::response::AggregatedResponse;
use super::pair::HttpPair;
use super::super::result::AggregatedResult;

/// Connection identifier - uniquely identifies an SSL connection
#[derive(Debug, Clone, Copy, Hash, Eq, PartialEq)]
pub struct ConnectionId {
    pub pid: u32,
    pub ssl_ptr: u64,
}

impl ConnectionId {
    /// Create from SslEvent
    pub fn from_ssl_event(event: &SslEvent) -> Self {
        ConnectionId {
            pid: event.pid,
            ssl_ptr: event.ssl_ptr,
        }
    }
}

/// Connection state machine
#[derive(Debug, Clone)]
pub enum ConnectionState {
    /// Idle - waiting for request
    Idle,
    /// Request pending - waiting for response
    RequestPending {
        request: ParsedRequest,
    },
    /// SSE active - response headers received, body streaming
    SseActive {
        request: Option<ParsedRequest>,
        response_headers: ParsedResponse,
        sse_events: Vec<ParsedSseEvent>,
    },
}

/// HTTP Connection Aggregator
#[derive(Debug)]
pub struct HttpConnectionAggregator {
    connections: LruCache<ConnectionId, ConnectionState>,
}

impl Default for HttpConnectionAggregator {
    fn default() -> Self {
        Self::new()
    }
}

impl HttpConnectionAggregator {
    /// Create a new aggregator with default capacity
    pub fn new() -> Self {
        HttpConnectionAggregator {
            connections: LruCache::new(NonZeroUsize::new(DEFAULT_CONNECTION_CAPACITY).unwrap()),
        }
    }

    /// Create a new aggregator with custom capacity
    pub fn with_capacity(capacity: usize) -> Self {
        HttpConnectionAggregator {
            connections: LruCache::new(NonZeroUsize::new(capacity).unwrap()),
        }
    }

    /// Insert connection state, logging if an unrelated entry is evicted by LRU
    fn insert(&mut self, key: ConnectionId, state: ConnectionState) {
        if let Some((evicted_key, evicted_state)) = self.connections.push(key, state) {
            if evicted_key != key {
                log::warn!(
                    "[HttpAggregator] LRU evicted conn={:?} state={} | capacity={}",
                    evicted_key,
                    match evicted_state {
                        ConnectionState::Idle => "Idle",
                        ConnectionState::RequestPending { .. } => "RequestPending",
                        ConnectionState::SseActive { .. } => "SseActive",
                    },
                    self.connections.cap(),
                );
            }
        }
    }

    /// Process HTTP Request (from HTTP Parser)
    pub fn process_request(&mut self, request: ParsedRequest) {
        let connection_id = ConnectionId::from_ssl_event(&request.source_event);

        log::trace!(
            "[HttpAggregator] State transition: -> RequestPending | conn={:?} | method={} | path={}",
            connection_id,
            request.method,
            request.path,
        );

        self.insert(
            connection_id,
            ConnectionState::RequestPending {
                request,
            },
        );
    }

    /// Process HTTP Response (from HTTP Parser)
    /// Returns completed HttpPair or SSE started signal
    pub fn process_response(
        &mut self,
        response: ParsedResponse,
    ) -> Option<AggregatedResult> {
        let connection_id = ConnectionId::from_ssl_event(&response.source_event);
        
        let state = self.connections.pop(&connection_id)?;
        
        match state {
            ConnectionState::RequestPending { request } => {
                if response.is_sse() {
                    log::trace!(
                        "[HttpAggregator] State transition: RequestPending -> SseActive | conn={:?} | status={}",
                        connection_id,
                        response.status_code,
                    );
                    // Transition to SSE active state, wait for SSE events
                    self.insert(
                        connection_id,
                        ConnectionState::SseActive {
                            request: Some(request),
                            response_headers: response,
                            sse_events: Vec::new(),
                        },
                    );
                    
                    // Don't return HttpPair yet, wait for SSE events to complete
                    None
                } else {
                    log::trace!(
                        "[HttpAggregator] State transition: RequestPending -> Complete | conn={:?} | status={}",
                        connection_id,
                        response.status_code,
                    );
                    let pair = HttpPair::from_parsed(
                        connection_id,
                        request,
                        response,
                    );
                    Some(AggregatedResult::HttpComplete(pair))
                }
            }
            ConnectionState::Idle => {
                if response.is_sse() {
                    // SSE response without prior request - still need to wait for SSE events
                    log::trace!(
                        "[HttpAggregator] State transition: Idle -> SseActive (no request) | conn={:?} | status={}",
                        connection_id,
                        response.status_code
                    );
                    self.insert(
                        connection_id,
                        ConnectionState::SseActive {
                            request: None,
                            response_headers: response,
                            sse_events: Vec::new(),
                        },
                    );
                    None
                } else {
                    log::trace!(
                        "[HttpAggregator] State transition: Idle -> ResponseOnly | conn={:?} | status={}",
                        connection_id,
                        response.status_code
                    );
                    let aggregated_response = AggregatedResponse::from_parsed(response);
                    Some(AggregatedResult::ResponseOnly {
                        connection_id,
                        response: aggregated_response,
                    })
                }
            }
            ConnectionState::SseActive { .. } => {
                log::trace!(
                    "[HttpAggregator] State transition: SseActive (unexpected response) | conn={:?}",
                    connection_id
                );
                // Response on SSE connection - shouldn't happen normally
                // Restore state and return None
                self.insert(connection_id, state);
                None
            }
        }
    }

    /// Process SSE Event (from SSE Parser)
    /// Only valid when connection is in SseActive state
    pub fn process_sse_event(
        &mut self,
        connection_id: &ConnectionId,
        sse_event: ParsedSseEvent,
    ) -> Option<AggregatedResult> {
        let state = self.connections.pop(connection_id)?;
        
        match state {
            ConnectionState::SseActive {
                request,
                response_headers,
                mut sse_events,
            } => {
                // Check if stream is done before processing
                let is_done = sse_event.is_done();

                log::trace!(
                    "[HttpAggregator] SSE event in SseActive | conn={:?} | is_done={}",
                    connection_id,
                    is_done,
                );

                // Add SSE event to the list
                sse_events.push(sse_event);

                if is_done {
                    log::trace!(
                        "[HttpAggregator] State transition: SseActive -> Complete | conn={:?}",
                        connection_id,
                    );
                    
                    // Build aggregated response with SSE events
                    let mut response = AggregatedResponse::from_parsed(response_headers);
                    response.set_sse_events(sse_events);
                    
                    // Return appropriate result based on whether request exists
                    if let Some(req) = request {
                        let parsed = response.parsed.clone();
                        let mut pair = HttpPair::from_parsed(*connection_id, req, parsed);
                        pair.response = response;
                        Some(AggregatedResult::SseComplete(pair))
                    } else {
                        Some(AggregatedResult::ResponseOnly {
                            connection_id: *connection_id,
                            response,
                        })
                    }
                } else {
                    // Continue SSE active state
                    self.insert(
                        *connection_id,
                        ConnectionState::SseActive {
                            request,
                            response_headers,
                            sse_events,
                        },
                    );
                    
                    None
                }
            }
            _ => {
                log::trace!(
                    "[HttpAggregator] SSE event in unexpected state | conn={:?}",
                    connection_id
                );
                // Not in SSE active state, restore state
                self.insert(*connection_id, state);
                None
            }
        }
    }

    /// Get active connection count
    pub fn active_connections(&self) -> usize {
        self.connections.len()
    }

    /// Check if connection has pending request
    pub fn has_pending_request(&self, connection_id: &ConnectionId) -> bool {
        matches!(
            self.connections.peek(connection_id),
            Some(ConnectionState::RequestPending { .. })
        )
    }

    /// Check if connection is SSE active
    pub fn is_sse_active(&self, connection_id: &ConnectionId) -> bool {
        matches!(
            self.connections.peek(connection_id),
            Some(ConnectionState::SseActive { .. })
        )
    }

    /// Check if there are any pending connections
    pub fn has_pending(&self) -> bool {
        !self.connections.is_empty()
    }

    /// Clear all connections
    pub fn clear(&mut self) {
        self.connections.clear();
    }

    /// Drain all connections (for force complete)
    pub fn drain_connections(&mut self) -> Vec<(ConnectionId, ConnectionState)> {
        self.connections.iter_mut()
            .map(|(k, v)| (*k, v.clone()))
            .collect::<Vec<_>>()
            .into_iter()
            .map(|(k, _)| (k, self.connections.pop(&k).unwrap()))
            .collect()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::rc::Rc;
    use std::collections::HashMap;

    fn create_mock_ssl_event(pid: u32, ssl_ptr: u64) -> Rc<SslEvent> {
        Rc::new(SslEvent {
            source: 0,
            timestamp_ns: 1000,
            delta_ns: 0,
            pid,
            tid: 1,
            uid: 0,
            len: 0,
            rw: 0,
            comm: String::new(),
            buf: Vec::new(),
            is_handshake: false,
            ssl_ptr,
        })
    }

    #[test]
    fn test_connection_id() {
        let id = ConnectionId { pid: 1234, ssl_ptr: 0x1000 };
        assert_eq!(id.pid, 1234);
        assert_eq!(id.ssl_ptr, 0x1000);
    }

    #[test]
    fn test_process_request_response_pair() {
        let mut aggregator = HttpConnectionAggregator::new();
        let event = create_mock_ssl_event(1234, 0x1000);
        
        // Process request
        let request = ParsedRequest {
            method: "GET".to_string(),
            path: "/api/test".to_string(),
            version: 11,
            headers: HashMap::new(),
            body_offset: 0,
            body_len: 0,
            source_event: event.clone(),
        };
        aggregator.process_request(request);
        
        assert!(aggregator.has_pending_request(&ConnectionId { pid: 1234, ssl_ptr: 0x1000 }));
        
        // Process response
        let response = ParsedResponse {
            version: 11,
            status_code: 200,
            reason: "OK".to_string(),
            headers: HashMap::new(),
            body_offset: 0,
            body_len: 0,
            source_event: event,
        };
        
        let result = aggregator.process_response(response);
        assert!(result.is_some());
        
        if let Some(AggregatedResult::HttpComplete(pair)) = result {
            assert_eq!(pair.request.method, "GET");
            assert_eq!(pair.response.status_code(), 200);
            assert!(pair.response.sse_events.is_empty());
        } else {
            panic!("Expected HttpComplete result");
        }
    }

    #[test]
    fn test_sse_detection() {
        let mut aggregator = HttpConnectionAggregator::new();
        let event = create_mock_ssl_event(1234, 0x1000);
        
        // Process request
        let request = ParsedRequest {
            method: "GET".to_string(),
            path: "/stream".to_string(),
            version: 11,
            headers: HashMap::new(),
            body_offset: 0,
            body_len: 0,
            source_event: event.clone(),
        };
        aggregator.process_request(request);
        
        // Process SSE response
        let mut headers = HashMap::new();
        headers.insert("content-type".to_string(), "text/event-stream".to_string());
        
        let response = ParsedResponse {
            version: 11,
            status_code: 200,
            reason: "OK".to_string(),
            headers,
            body_offset: 0,
            body_len: 0,
            source_event: event,
        };
        
        let result = aggregator.process_response(response);
        
        // SSE response should not return result immediately, but should activate SSE state
        assert!(result.is_none());
        assert!(aggregator.is_sse_active(&ConnectionId { pid: 1234, ssl_ptr: 0x1000 }));
    }
}
