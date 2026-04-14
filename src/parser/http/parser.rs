//! HTTP Parser - 无状态 HTTP 解析器

use super::request::ParsedRequest;
use super::response::ParsedResponse;
use crate::probes::sslsniff::SslEvent;
use anyhow::{Context, Result};
use std::collections::HashMap;
use std::rc::Rc;

/// 最大 headers 数量
const MAX_HEADERS: usize = 64;

/// 解析后的 HTTP 消息
#[derive(Debug, Clone)]
pub enum ParsedHttpMessage {
    Request(ParsedRequest),
    Response(ParsedResponse),
}

/// HTTP 解析器（无状态）
#[derive(Debug, Default)]
pub struct HttpParser;

impl HttpParser {
    /// 创建新的解析器实例
    pub fn new() -> Self {
        Self
    }

    /// 解析 SslEvent，返回 Request 或 Response
    pub fn parse(&self, event: Rc<SslEvent>) -> Result<ParsedHttpMessage> {
        // 只使用实际数据长度，而非整个 buf 数组
        let data_len = event.buf_size() as usize;
        let data = &event.buf[..data_len];

        // 尝试解析为 Request
        match Self::parse_request(data, &event) {
            Ok(req) => return Ok(ParsedHttpMessage::Request(req)),
            Err(e) => log::trace!("Failed to parse as HTTP request: {}", e),
        }

        // 尝试解析为 Response
        match Self::parse_response(data, &event) {
            Ok(resp) => return Ok(ParsedHttpMessage::Response(resp)),
            Err(e) => log::trace!("Failed to parse as HTTP response: {}", e),
        }

        Err(anyhow::anyhow!(
            "Failed to parse HTTP message (len={}), not a valid HTTP request or response, raw data: {:?}",
            data_len,
            event
        ))
    }

    /// 解析 HTTP Request
    fn parse_request(data: &[u8], event: &Rc<SslEvent>) -> Result<ParsedRequest> {
        let mut headers = [httparse::EMPTY_HEADER; MAX_HEADERS];
        let mut req = httparse::Request::new(&mut headers);

        let header_end = match req.parse(data)? {
            httparse::Status::Complete(n) => n,
            httparse::Status::Partial => {
                return Err(anyhow::anyhow!(
                    "HTTP request parsing incomplete (partial data)"
                ));
            }
        };

        let method = req.method.context("Missing HTTP method")?.to_string();
        let path = req.path.context("Missing HTTP path")?.to_string();
        let version = req.version.context("Missing HTTP version")?;

        let parsed_headers: HashMap<String, String> = req
            .headers
            .iter()
            .map(|h| {
                let key = h.name.to_lowercase();
                let value = String::from_utf8_lossy(h.value).to_string();
                (key, value)
            })
            .collect();

        let body_len = data.len().saturating_sub(header_end);

        Ok(ParsedRequest {
            method,
            path,
            version,
            headers: parsed_headers,
            body_offset: header_end,
            body_len,
            source_event: Rc::clone(event),
        })
    }

    /// 解析 HTTP Response
    fn parse_response(data: &[u8], event: &Rc<SslEvent>) -> Result<ParsedResponse> {
        let mut headers = [httparse::EMPTY_HEADER; MAX_HEADERS];
        let mut resp = httparse::Response::new(&mut headers);

        let header_end = match resp.parse(data)? {
            httparse::Status::Complete(n) => n,
            httparse::Status::Partial => {
                return Err(anyhow::anyhow!(
                    "HTTP response parsing incomplete (partial data)"
                ));
            }
        };

        let version = resp.version.context("Missing HTTP version")?;
        let status_code = resp.code.context("Missing HTTP status code")?;
        let reason = resp.reason.context("Missing HTTP reason")?.to_string();

        let parsed_headers: HashMap<String, String> = resp
            .headers
            .iter()
            .map(|h| {
                let key = h.name.to_lowercase();
                let value = String::from_utf8_lossy(h.value).to_string();
                (key, value)
            })
            .collect();

        let body_len = data.len().saturating_sub(header_end);

        Ok(ParsedResponse {
            version,
            status_code,
            reason,
            headers: parsed_headers,
            body_offset: header_end,
            body_len,
            source_event: Rc::clone(event),
        })
    }
}
