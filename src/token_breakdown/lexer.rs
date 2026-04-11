//! ChatML lexer - splits raw text into blocks by <|im_start|> / <|im_end|> markers
//!
//! Handles the ChatML format used by Qwen and similar models:
//! ```text
//! <|im_start|>system
//! ... content ...
//! <|im_end|>
//! <|im_start|>user
//! ... content ...
//! <|im_end|>
//! ```

use anyhow::{anyhow, Result};

use super::types::{ChatMLBlock, ChatMLDocument};

const IM_START: &str = "<|im_start|>";
const IM_END: &str = "<|im_end|>";

/// Parse a ChatML formatted text into a document of blocks.
///
/// Each block is delimited by `<|im_start|>role\n` and `<|im_end|>`.
/// The role is extracted from the first line after `<|im_start|>`.
/// The content is everything between the role line and `<|im_end|>`.
pub fn parse_chatml(input: &str) -> Result<ChatMLDocument> {
    let mut blocks = Vec::new();
    let mut pos = 0;

    while let Some(start_offset) = input[pos..].find(IM_START) {
        let block_start = pos + start_offset;
        let after_marker = block_start + IM_START.len();

        // Find the role: text from after <|im_start|> to the first newline
        let role_end = input[after_marker..]
            .find('\n')
            .ok_or_else(|| anyhow!("No newline after <|im_start|> at byte offset {}", block_start))?;
        let role = input[after_marker..after_marker + role_end].trim().to_string();

        // Content starts after the role line's newline
        let content_start = after_marker + role_end + 1;

        // Find the matching <|im_end|>
        let end_offset = input[content_start..]
            .find(IM_END)
            .ok_or_else(|| anyhow!("No matching <|im_end|> for <|im_start|>{} at byte offset {}", role, block_start))?;
        let content_end = content_start + end_offset;

        let raw_content = input[content_start..content_end].to_string();

        blocks.push(ChatMLBlock {
            role,
            raw_content,
        });

        // Move past <|im_end|>
        pos = content_end + IM_END.len();
    }

    if blocks.is_empty() {
        return Err(anyhow!("No ChatML blocks found in input"));
    }

    Ok(ChatMLDocument {
        blocks,
        raw_text: input.to_string(),
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_simple_chatml() {
        let input = "\
<|im_start|>system
You are a helpful assistant.
<|im_end|>
<|im_start|>user
Hello!
<|im_end|>
<|im_start|>assistant
Hi there!
<|im_end|>
";
        let doc = parse_chatml(input).unwrap();
        assert_eq!(doc.blocks.len(), 3);

        assert_eq!(doc.blocks[0].role, "system");
        assert_eq!(doc.blocks[0].raw_content, "You are a helpful assistant.\n");

        assert_eq!(doc.blocks[1].role, "user");
        assert_eq!(doc.blocks[1].raw_content, "Hello!\n");

        assert_eq!(doc.blocks[2].role, "assistant");
        assert_eq!(doc.blocks[2].raw_content, "Hi there!\n");
    }

    #[test]
    fn test_nested_xml_tags() {
        let input = "\
<|im_start|>system
<tools>
{\"function\":{\"name\":\"read\"}}
</tools>
<|im_end|>
";
        let doc = parse_chatml(input).unwrap();
        assert_eq!(doc.blocks.len(), 1);
        assert_eq!(doc.blocks[0].role, "system");
        assert!(doc.blocks[0].raw_content.contains("<tools>"));
        assert!(doc.blocks[0].raw_content.contains("</tools>"));
    }

    #[test]
    fn test_tool_call_content() {
        let input = "\
<|im_start|>assistant
<tool_call>
<function=read>
<parameter=path>/some/file</parameter>
</function>
</tool_call>
<|im_end|>
";
        let doc = parse_chatml(input).unwrap();
        assert_eq!(doc.blocks.len(), 1);
        assert_eq!(doc.blocks[0].role, "assistant");
        assert!(doc.blocks[0].raw_content.contains("<tool_call>"));
    }

    #[test]
    fn test_tool_response_content() {
        let input = "\
<|im_start|>user
<tool_response>
File contents here
</tool_response>
<|im_end|>
";
        let doc = parse_chatml(input).unwrap();
        assert_eq!(doc.blocks.len(), 1);
        assert_eq!(doc.blocks[0].role, "user");
        assert!(doc.blocks[0].raw_content.contains("<tool_response>"));
    }

    #[test]
    fn test_empty_input() {
        let result = parse_chatml("no chatml markers here");
        assert!(result.is_err());
    }

    #[test]
    fn test_multiple_user_assistant_turns() {
        let input = "\
<|im_start|>system
sys
<|im_end|>
<|im_start|>user
msg1
<|im_end|>
<|im_start|>assistant
resp1
<|im_end|>
<|im_start|>user
msg2
<|im_end|>
";
        let doc = parse_chatml(input).unwrap();
        assert_eq!(doc.blocks.len(), 4);
        assert_eq!(doc.blocks[0].role, "system");
        assert_eq!(doc.blocks[1].role, "user");
        assert_eq!(doc.blocks[2].role, "assistant");
        assert_eq!(doc.blocks[3].role, "user");
    }
}
