//! Token breakdown computation
//!
//! Counts tokens for each classified segment and builds the hierarchical
//! JSON output structure using the events list architecture.
//!
//! Events:
//! - "request": system_prompt + individual messages in order (user_message, assistant_response, etc.)
//! - "response": content + reasoning_content + tool_calls (3 sub-categories)

use anyhow::Result;

use crate::tokenizer::core::Tokenizer;

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
    tokenizer: &dyn Tokenizer,
    file_path: &str,
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
        file_path: file_path.to_string(),
        model_name: tokenizer.model_name().to_string(),
        total_tokens,
        summary: Some(top_summary),
        events,
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::token_breakdown::types::*;
    use crate::tokenizer::providers::ByteCountTokenizer;

    fn make_test_doc() -> ClassifiedDocument {
        ClassifiedDocument {
            system_content: "You are a helpful assistant.\nFollow the rules.".to_string(),
            messages: vec![
                ConversationTurn {
                    turn_type: ConversationTurnType::UserMessage,
                    content: "Hello, what is the weather?".to_string(),
                    is_history: true,
                },
                ConversationTurn {
                    turn_type: ConversationTurnType::AssistantText,
                    content: "The weather is sunny.".to_string(),
                    is_history: true,
                },
                ConversationTurn {
                    turn_type: ConversationTurnType::UserMessage,
                    content: "Thanks!".to_string(),
                    is_history: false,
                },
            ],
            response: None,
        }
    }

    fn make_test_doc_with_response() -> ClassifiedDocument {
        let mut doc = make_test_doc();
        doc.response = Some(ResponseData {
            content: vec!["The weather in Shenzhen is sunny.".to_string()],
            reasoning_content: Some("User asked about weather, I need to check.".to_string()),
            tool_calls: vec!["weather: {\"city\":\"Shenzhen\"}".to_string()],
        });
        doc
    }

    #[test]
    fn test_request_only_structure() {
        let doc = make_test_doc();
        let tokenizer = ByteCountTokenizer::new();
        let result = compute_breakdown(&doc, &tokenizer, "test.txt").unwrap();

        assert_eq!(result.file_path, "test.txt");
        assert_eq!(result.events.len(), 1); // only request
        assert_eq!(result.events[0].event_type, "request");
        // system_prompt + individual messages in order
        assert_eq!(result.events[0].children.len(), 4);
        assert_eq!(result.events[0].children[0].name, "system_prompt");
        assert_eq!(result.events[0].children[1].name, "user_message");
        assert_eq!(result.events[0].children[2].name, "assistant_response");
        assert_eq!(result.events[0].children[3].name, "user_message");
        assert!(result.total_tokens > 0);
    }

    #[test]
    fn test_system_prompt_no_children() {
        let doc = make_test_doc();
        let tokenizer = ByteCountTokenizer::new();
        let result = compute_breakdown(&doc, &tokenizer, "test.txt").unwrap();

        let sys = &result.events[0].children[0];
        assert!(sys.children.is_none()); // no sub-segmentation
        assert!(sys.tokens > 0);
    }

    #[test]
    fn test_request_response_structure() {
        let doc = make_test_doc_with_response();
        let tokenizer = ByteCountTokenizer::new();
        let result = compute_breakdown(&doc, &tokenizer, "test.txt").unwrap();

        assert_eq!(result.events.len(), 2); // request + response
        assert_eq!(result.events[0].event_type, "request");
        assert_eq!(result.events[1].event_type, "response");

        // response has 3 children
        let resp = &result.events[1];
        assert_eq!(resp.children.len(), 3);
        assert_eq!(resp.children[0].name, "content");
        assert_eq!(resp.children[1].name, "reasoning_content");
        assert_eq!(resp.children[2].name, "tool_calls");
    }

    #[test]
    fn test_token_sum_consistency() {
        let doc = make_test_doc_with_response();
        let tokenizer = ByteCountTokenizer::new();
        let result = compute_breakdown(&doc, &tokenizer, "test.txt").unwrap();

        // request children sum == request total (flattened structure)
        let req = &result.events[0];
        let req_children_sum: usize = req.children.iter().map(|c| c.tokens).sum();
        assert_eq!(req_children_sum, req.tokens);

        // response children sum == response total
        let resp = &result.events[1];
        let resp_children_sum: usize = resp.children.iter().map(|c| c.tokens).sum();
        assert_eq!(resp_children_sum, resp.tokens);

        // all events sum == total
        let events_sum: usize = result.events.iter().map(|e| e.tokens).sum();
        assert_eq!(events_sum, result.total_tokens);
    }

    #[test]
    fn test_is_history_propagated() {
        let doc = make_test_doc();
        let tokenizer = ByteCountTokenizer::new();
        let result = compute_breakdown(&doc, &tokenizer, "test.txt").unwrap();

        // First user message is history
        let user_msg_0 = &result.events[0].children[1];
        assert_eq!(user_msg_0.name, "user_message");
        assert!(user_msg_0.is_history.unwrap());
        assert!(user_msg_0.content.is_some());

        // Second user message is not history
        let user_msg_2 = &result.events[0].children[3];
        assert_eq!(user_msg_2.name, "user_message");
        assert!(!user_msg_2.is_history.unwrap());
        assert!(user_msg_2.content.is_some());
    }

    #[test]
    fn test_percentage_range() {
        let doc = make_test_doc_with_response();
        let tokenizer = ByteCountTokenizer::new();
        let result = compute_breakdown(&doc, &tokenizer, "test.txt").unwrap();

        for event in &result.events {
            assert!(
                event.percentage >= 0.0 && event.percentage <= 100.0,
                "event {} percentage out of range: {}",
                event.event_type,
                event.percentage
            );
        }
    }

    #[test]
    fn test_empty_response_fields() {
        let mut doc = make_test_doc();
        doc.response = Some(ResponseData {
            content: vec!["some text".to_string()],
            reasoning_content: None,
            tool_calls: vec![],
        });

        let tokenizer = ByteCountTokenizer::new();
        let result = compute_breakdown(&doc, &tokenizer, "test.txt").unwrap();

        let resp = &result.events[1];
        // reasoning_content should have 0 tokens
        assert_eq!(resp.children[1].tokens, 0);
        assert!(resp.children[1].content.is_none());
        // tool_calls should have 0 tokens
        assert_eq!(resp.children[2].tokens, 0);
        assert!(resp.children[2].response_items.is_none());
    }

    #[test]
    fn test_empty_system_prompt() {
        let doc = ClassifiedDocument {
            system_content: String::new(),
            messages: vec![ConversationTurn {
                turn_type: ConversationTurnType::UserMessage,
                content: "Hello".to_string(),
                is_history: false,
            }],
            response: None,
        };

        let tokenizer = ByteCountTokenizer::new();
        let result = compute_breakdown(&doc, &tokenizer, "test.txt").unwrap();

        let sys = &result.events[0].children[0];
        assert_eq!(sys.tokens, 0);
    }

    #[test]
    fn test_summary_statistics() {
        let doc = make_test_doc();
        let tokenizer = ByteCountTokenizer::new();
        let result = compute_breakdown(&doc, &tokenizer, "test.txt").unwrap();

        let req = &result.events[0];
        let summary = req.summary.as_ref().expect("summary should be present");

        // Check that we have the expected labels in summary
        assert!(summary.contains_key("系统提示词"));
        assert!(summary.contains_key("用户消息"));
        assert!(summary.contains_key("助手回复"));

        // Check user_message count (2 messages)
        let user_summary = summary.get("用户消息").unwrap();
        assert_eq!(user_summary.count, 2);

        // Check assistant_response count (1 message)
        let assistant_summary = summary.get("助手回复").unwrap();
        assert_eq!(assistant_summary.count, 1);

        // Summary tokens should equal children tokens sum
        let summary_total: usize = summary.values().map(|s| s.tokens).sum();
        assert_eq!(summary_total, req.tokens);
    }

}
