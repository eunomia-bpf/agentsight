//! HTTP Request/Response Pair
//
//! This module defines the `HttpPair` structure representing a complete
//! HTTP request/response transaction.

use super::aggregator::ConnectionId;
use super::response::AggregatedResponse;
use crate::chrome_trace::{ChromeTraceEvent, ToChromeTraceEvent, next_flow_id};
use crate::parser::http::{ParsedRequest, ParsedResponse};
use crate::parser::sse::ParsedSseEvent;

/// Completed HTTP request/response pair
#[derive(Debug, Clone)]
pub struct HttpPair {
    /// Connection identifier
    pub connection_id: ConnectionId,
    /// Parsed request
    pub request: ParsedRequest,
    /// Aggregated response
    pub response: AggregatedResponse,
}

impl HttpPair {
    /// Create HttpPair from parsed request and response
    /// Timestamps are derived from source_event.timestamp_ns
    pub fn from_parsed(
        connection_id: ConnectionId,
        request: ParsedRequest,
        response: ParsedResponse,
    ) -> Self {
        let aggregated_response = AggregatedResponse::from_parsed(response);
        
        HttpPair {
            connection_id,
            request,
            response: aggregated_response,
        }
    }
    
    /// Add SSE event to the response
    pub fn add_sse_event(&mut self, event: ParsedSseEvent) {
        self.response.add_sse_event(event);
    }
}

impl ToChromeTraceEvent for HttpPair {
    /// Convert HttpPair to Chrome Trace Events
    /// 
    /// Returns request, response events and flow events linking them
    fn to_chrome_trace_events(&self) -> Vec<ChromeTraceEvent> {
        let mut events = Vec::new();
        
        // Add request events
        let req_events = self.request.to_chrome_trace_events();
        events.extend(req_events);
        
        // Add response events
        let resp_events = self.response.to_chrome_trace_events();
        events.extend(resp_events);
        
        // Create flow events linking request to response
        // Flow ID is generated on-demand for trace generation
        if let (Some(req_event), Some(resp_event)) = (events.first(), events.last()) {
            let flow_id = next_flow_id();
            let (flow_start, flow_end) = ChromeTraceEvent::flow_from_events_with_id(
                req_event, 
                resp_event, 
                flow_id
            );
            events.push(flow_start);
            events.push(flow_end);
        }
        
        events
    }
}
