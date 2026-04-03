//! Token breakdown computation
//!
//! Counts tokens for each classified segment and builds the hierarchical
//! JSON output structure using the events list architecture.
//!
//! Events:
//! - "request": system_prompt + individual messages in order (user_message, assistant_response, etc.)
//! - "response": content + reasoning_content + tool_calls (3 sub-categories)

use anyhow::Result;

use crate::tokenizer::LlmTokenizer;

use super::types::{
    ChatMLTokenBreakdown, ClassifiedDocument, ConversationTurnType, EventNode, ResponseItem,
    SummaryItem, TokenBreakdownNode,
};

use std::collections::BTreeMap;

/// Compute percentage with one decimal place precision.
fn pct(tokens: usize, total: f64) -> f64 {
    if total > 0.0 {
        (tokens as f64 / total * 1000.0).round() / 10.0
    } else {
        0.0
    }
}

/// Compute summary statistics from children nodes.
fn compute_summary(children: &[TokenBreakdownNode], event_total: usize) -> BTreeMap<String, SummaryItem> {
    let mut summary: BTreeMap<String, SummaryItem> = BTreeMap::new();
    let event_total_f64 = event_total as f64;

    for child in children {
        let entry = summary.entry(child.label.clone()).or_insert(SummaryItem {
            count: 0,
            tokens: 0,
            percentage: 0.0,
        });
        entry.count += 1;
        entry.tokens += child.tokens;
    }

    // Set percentages
    for item in summary.values_mut() {
        item.percentage = pct(item.tokens, event_total_f64);
    }

    summary
}

/// Compute the token breakdown for a classified document.
///
/// Builds an events array with:
/// - "request" event: system_prompt + individual messages in original order
/// - "response" event (if response data present): content + reasoning_content + tool_calls
pub fn compute_breakdown(
    doc: &ClassifiedDocument,
    tokenizer: &LlmTokenizer,
) -> Result<ChatMLTokenBreakdown> {
    // === Build request event ===

    // System prompt: overall token count, no children
    let system_tokens = if doc.system_content.is_empty() {
        0
    } else {
        tokenizer.count_with_special_tokens(&doc.system_content)?
    };
    let system_chars = doc.system_content.chars().count();

    // Build individual message nodes in original order (no aggregation by type)
    let mut message_nodes = Vec::new();
    let mut messages_total_tokens = 0usize;
    let mut messages_total_chars = 0usize;

    for turn in doc.messages.iter() {
        let tokens = tokenizer.count_with_special_tokens(&turn.content)?;
        let chars = turn.content.chars().count();
        messages_total_tokens += tokens;
        messages_total_chars += chars;

        let (name, label) = match turn.turn_type {
            ConversationTurnType::UserMessage => ("user_message", "用户消息"),
            ConversationTurnType::AssistantText => ("assistant_response", "助手回复"),
            ConversationTurnType::ToolCall => ("tool_call", "工具调用"),
            ConversationTurnType::ToolResponse => ("tool_response", "工具响应"),
        };

        message_nodes.push(TokenBreakdownNode {
            name: name.to_string(),
            label: label.to_string(),
            tokens,
            percentage: 0.0, // set after total is known
            char_count: chars,
            is_history: Some(turn.is_history),
            content: Some(turn.content.clone()),
            children: None,
            response_items: None,
        });
    }

    let request_tokens = system_tokens + messages_total_tokens;
    let request_chars = system_chars + messages_total_chars;

    // === Build response event (if present) ===
    let mut response_event: Option<EventNode> = None;
    let mut response_total_tokens = 0usize;

    if let Some(ref resp) = doc.response {
        let mut resp_children = Vec::new();

        // content
        let mut content_tokens = 0usize;
        let mut content_chars = 0usize;
        let mut content_items = Vec::new();
        for (idx, text) in resp.content.iter().enumerate() {
            let t = tokenizer.count_with_special_tokens(text)?;
            let c = text.chars().count();
            content_tokens += t;
            content_chars += c;
            content_items.push(ResponseItem {
                index: idx,
                tokens: t,
                char_count: c,
                content: text.clone(),
            });
        }
        resp_children.push(TokenBreakdownNode {
            name: "content".to_string(),
            label: "文本内容".to_string(),
            tokens: content_tokens,
            percentage: 0.0,
            char_count: content_chars,
            is_history: None,
            content: None,
            children: None,
            response_items: if content_items.is_empty() {
                None
            } else {
                Some(content_items)
            },
        });

        // reasoning_content
        let (reasoning_tokens, reasoning_chars) =
            if let Some(ref text) = resp.reasoning_content {
                if text.is_empty() {
                    (0, 0)
                } else {
                    let t = tokenizer.count_with_special_tokens(text)?;
                    let c = text.chars().count();
                    (t, c)
                }
            } else {
                (0, 0)
            };
        resp_children.push(TokenBreakdownNode {
            name: "reasoning_content".to_string(),
            label: "推理内容".to_string(),
            tokens: reasoning_tokens,
            percentage: 0.0,
            char_count: reasoning_chars,
            is_history: None,
            content: if reasoning_tokens > 0 {
                resp.reasoning_content.clone()
            } else {
                None
            },
            children: None,
            response_items: None,
        });

        // tool_calls
        let mut tc_tokens = 0usize;
        let mut tc_chars = 0usize;
        let mut tc_items = Vec::new();
        for (idx, text) in resp.tool_calls.iter().enumerate() {
            let t = tokenizer.count_with_special_tokens(text)?;
            let c = text.chars().count();
            tc_tokens += t;
            tc_chars += c;
            tc_items.push(ResponseItem {
                index: idx,
                tokens: t,
                char_count: c,
                content: text.clone(),
            });
        }
        resp_children.push(TokenBreakdownNode {
            name: "tool_calls".to_string(),
            label: "工具调用".to_string(),
            tokens: tc_tokens,
            percentage: 0.0,
            char_count: tc_chars,
            is_history: None,
            content: None,
            children: None,
            response_items: if tc_items.is_empty() {
                None
            } else {
                Some(tc_items)
            },
        });

        response_total_tokens = content_tokens + reasoning_tokens + tc_tokens;
        let response_chars = content_chars + reasoning_chars + tc_chars;

        let resp_summary = compute_summary(&resp_children, response_total_tokens);
        response_event = Some(EventNode {
            event_type: "response".to_string(),
            label: "响应".to_string(),
            tokens: response_total_tokens,
            percentage: 0.0, // set after total is known
            char_count: response_chars,
            summary: Some(resp_summary),
            children: resp_children,
        });
    }

    // === Compute total and set percentages ===
    let total_tokens = request_tokens + response_total_tokens;
    let total_f64 = total_tokens as f64;

    // Build request children: system_prompt + individual messages in order
    let mut request_children = vec![TokenBreakdownNode {
        name: "system_prompt".to_string(),
        label: "系统提示词".to_string(),
        tokens: system_tokens,
        percentage: pct(system_tokens, total_f64),
        char_count: system_chars,
        is_history: None,
        content: if doc.system_content.is_empty() {
            None
        } else {
            Some(doc.system_content.clone())
        },
        children: None,
        response_items: None,
    }];

    // Set percentages for individual messages and add them to request_children
    for node in &mut message_nodes {
        node.percentage = pct(node.tokens, total_f64);
    }
    request_children.append(&mut message_nodes);

    let request_event = EventNode {
        event_type: "request".to_string(),
        label: "请求".to_string(),
        tokens: request_tokens,
        percentage: pct(request_tokens, total_f64),
        char_count: request_chars,
        summary: Some(compute_summary(&request_children, request_tokens)),
        children: request_children,
    };

    // Build events array
    let mut events = vec![request_event];

    if let Some(mut resp_evt) = response_event {
        resp_evt.percentage = pct(resp_evt.tokens, total_f64);
        for child in &mut resp_evt.children {
            child.percentage = pct(child.tokens, total_f64);
        }
        events.push(resp_evt);
    }

    // Build top-level summary: by_role and by_history
    let mut top_summary: BTreeMap<String, BTreeMap<String, SummaryItem>> = BTreeMap::new();
    
    // === by_role: original structure (input/output by label) ===
    let mut by_role: BTreeMap<String, SummaryItem> = BTreeMap::new();
    for event in &events {
        let category = if event.event_type == "request" {
            "input"
        } else {
            "output"
        };
        if let Some(ref event_summary) = event.summary {
            for (label, item) in event_summary {
                let entry = by_role.entry(label.clone()).or_insert(SummaryItem {
                    count: 0,
                    tokens: 0,
                    percentage: 0.0,
                });
                entry.count += item.count;
                entry.tokens += item.tokens;
            }
        }
    }
    // Set percentages for by_role
    for item in by_role.values_mut() {
        item.percentage = pct(item.tokens, total_f64);
    }
    top_summary.insert("by_role".to_string(), by_role);
    
    // === by_history: 系统提示词、历史消息、实时消息 ===
    let mut by_history: BTreeMap<String, SummaryItem> = BTreeMap::new();
    
    // 系统提示词
    let sys_tokens = system_tokens;
    if sys_tokens > 0 {
        by_history.insert("系统提示词".to_string(), SummaryItem {
            count: 1,
            tokens: sys_tokens,
            percentage: pct(sys_tokens, total_f64),
        });
    }
    
    // 历史消息和实时消息
    let mut history_tokens = 0usize;
    let mut history_count = 0usize;
    let mut realtime_tokens = 0usize;
    let mut realtime_count = 0usize;
    
    for turn in doc.messages.iter() {
        let tokens = tokenizer.count_with_special_tokens(&turn.content)?;
        if turn.is_history {
            history_tokens += tokens;
            history_count += 1;
        } else {
            realtime_tokens += tokens;
            realtime_count += 1;
        }
    }
    
    if history_tokens > 0 {
        by_history.insert("历史消息".to_string(), SummaryItem {
            count: history_count,
            tokens: history_tokens,
            percentage: pct(history_tokens, total_f64),
        });
    }
    if realtime_tokens > 0 {
        by_history.insert("实时消息".to_string(), SummaryItem {
            count: realtime_count,
            tokens: realtime_tokens,
            percentage: pct(realtime_tokens, total_f64),
        });
    }
    
    top_summary.insert("by_history".to_string(), by_history);

    Ok(ChatMLTokenBreakdown {
        model_name: tokenizer.model_name().to_string(),
        total_tokens,
        summary: Some(top_summary),
        events,
    })
}

