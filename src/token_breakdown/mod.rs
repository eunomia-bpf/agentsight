//! ChatML token consumption breakdown module
//!
//! Provides offline analysis of ChatML format dialogue files,
//! breaking down token consumption into a hierarchical event-based structure.
//!
//! # Architecture
//!
//! ```text
//! raw text → lexer → classifier → breakdown → JSON output
//! ```
//!
//! - **lexer**: Splits ChatML text into blocks by `<|im_start|>` / `<|im_end|>` markers
//! - **classifier**: Categorizes conversation messages (4 sub-types)
//! - **breakdown**: Counts tokens per segment and builds hierarchical events output
//!
//! # Events
//!
//! Output uses an events list architecture:
//! - `request`: system_prompt + individual messages in order (user_message, assistant_response, etc.)
//! - `response`: content + reasoning_content + tool_calls (3 sub-categories)

pub mod types;
pub mod lexer;
pub mod classifier;
pub mod breakdown;
pub mod cli;

pub use types::*;
pub use lexer::parse_chatml;
pub use classifier::classify_conversation;
pub use breakdown::compute_breakdown;
pub use cli::AnalyzeChatmlCommand;
