//! Classifier for conversation messages
//!
//! Conversation messages are classified by role and content markers into 4 types:
//! - UserMessage, AssistantText, ToolCall, ToolResponse
//!
//! System prompt is treated as a whole (no sub-segmentation in current phase).

use super::types::{
    ChatMLBlock, ClassifiedDocument, ConversationTurn, ConversationTurnType, ResponseData,
};

/// Classify conversation blocks into typed messages.
///
/// - Skips system blocks
/// - assistant with `<tool_call>` -> ToolCall
/// - assistant without `<tool_call>` -> AssistantText
/// - user with `<tool_response>` -> ToolResponse
/// - user without `<tool_response>` -> UserMessage
/// - The last UserMessage gets `is_history: false`, all others `is_history: true`
pub fn classify_conversation(blocks: &[ChatMLBlock]) -> Vec<ConversationTurn> {
    let mut turns: Vec<ConversationTurn> = Vec::new();

    for block in blocks {
        if block.role == "system" {
            continue;
        }

        let turn_type = if block.role == "assistant" {
            if block.raw_content.contains("<tool_call>") {
                ConversationTurnType::ToolCall
            } else {
                ConversationTurnType::AssistantText
            }
        } else {
            if block.raw_content.contains("<tool_response>") {
                ConversationTurnType::ToolResponse
            } else {
                ConversationTurnType::UserMessage
            }
        };

        turns.push(ConversationTurn {
            turn_type,
            content: block.raw_content.clone(),
            is_history: true,
        });
    }

    // Find the last UserMessage and mark it as current (is_history = false)
    if let Some(last_user_idx) = turns
        .iter()
        .rposition(|t| t.turn_type == ConversationTurnType::UserMessage)
    {
        turns[last_user_idx].is_history = false;
    }

    turns
}

/// Classify a complete ChatML document into system content and messages.
///
/// System prompt content is kept as-is (no sub-segmentation).
/// Response data is passed through if provided.
pub fn classify_document(
    blocks: &[ChatMLBlock],
    response: Option<ResponseData>,
) -> ClassifiedDocument {
    let system_content = blocks
        .iter()
        .find(|b| b.role == "system")
        .map(|b| b.raw_content.clone())
        .unwrap_or_default();

    let messages = classify_conversation(blocks);

    ClassifiedDocument {
        system_content,
        messages,
        response,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn make_block(role: &str, content: &str) -> ChatMLBlock {
        ChatMLBlock {
            role: role.to_string(),
            raw_content: content.to_string(),
        }
    }

    // === Conversation classification tests ===

    #[test]
    fn test_user_message_classification() {
        let blocks = vec![
            make_block("system", "system prompt"),
            make_block("user", "Hello"),
            make_block("assistant", "Hi there"),
        ];
        let turns = classify_conversation(&blocks);
        assert_eq!(turns.len(), 2);
        assert_eq!(turns[0].turn_type, ConversationTurnType::UserMessage);
        assert_eq!(turns[1].turn_type, ConversationTurnType::AssistantText);
    }

    #[test]
    fn test_tool_call_classification() {
        let blocks = vec![
            make_block("system", "sys"),
            make_block("user", "query"),
            make_block("assistant", "<tool_call>\n<function=read>\n</function>\n</tool_call>"),
        ];
        let turns = classify_conversation(&blocks);
        assert_eq!(turns[1].turn_type, ConversationTurnType::ToolCall);
    }

    #[test]
    fn test_tool_response_classification() {
        let blocks = vec![
            make_block("system", "sys"),
            make_block("user", "<tool_response>\nfile contents\n</tool_response>"),
        ];
        let turns = classify_conversation(&blocks);
        assert_eq!(turns[0].turn_type, ConversationTurnType::ToolResponse);
    }

    #[test]
    fn test_is_history_marking() {
        let blocks = vec![
            make_block("system", "sys"),
            make_block("user", "first question"),
            make_block("assistant", "first answer"),
            make_block("user", "<tool_response>\ndata\n</tool_response>"),
            make_block("user", "second question"),
        ];
        let turns = classify_conversation(&blocks);
        assert_eq!(turns.len(), 4);

        assert!(turns[0].is_history);
        assert!(turns[1].is_history);
        assert!(turns[2].is_history);
        assert!(!turns[3].is_history);
    }

    #[test]
    fn test_system_blocks_skipped() {
        let blocks = vec![make_block("system", "sys prompt")];
        let turns = classify_conversation(&blocks);
        assert!(turns.is_empty());
    }

    // === Full document classification ===

    #[test]
    fn test_classify_document() {
        let blocks = vec![
            make_block("system", "You are a helpful assistant."),
            make_block("user", "Hello"),
            make_block("assistant", "Hi"),
        ];
        let doc = classify_document(&blocks, None);
        assert_eq!(doc.system_content, "You are a helpful assistant.");
        assert_eq!(doc.messages.len(), 2);
        assert!(doc.response.is_none());
    }

    #[test]
    fn test_classify_document_with_response() {
        let blocks = vec![
            make_block("system", "sys"),
            make_block("user", "Hello"),
        ];
        let response = ResponseData {
            content: vec!["Hello!".to_string()],
            reasoning_content: Some("thinking...".to_string()),
            tool_calls: vec![],
        };
        let doc = classify_document(&blocks, Some(response));
        assert!(doc.response.is_some());
        let resp = doc.response.unwrap();
        assert_eq!(resp.content.len(), 1);
        assert!(resp.reasoning_content.is_some());
    }

    #[test]
    fn test_classify_document_no_system() {
        let blocks = vec![make_block("user", "Hello")];
        let doc = classify_document(&blocks, None);
        assert_eq!(doc.system_content, "");
        assert_eq!(doc.messages.len(), 1);
    }
}
