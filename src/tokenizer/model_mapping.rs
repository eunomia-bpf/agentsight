//! Model name to HuggingFace model ID mapping
//!
//! Provides mapping from various LLM API model names (OpenAI, Anthropic, Qwen, etc.)
//! to their corresponding HuggingFace model IDs for tokenizer download.
//!
//! This is necessary because API providers often use simplified model names
//! (e.g., "gpt-4", "claude-3-opus", "qwen-turbo") that don't match HuggingFace's
//! naming convention (e.g., "openai/gpt-4", "anthropic/claude-3-opus").

use std::collections::HashMap;
use once_cell::sync::Lazy;

/// Global model name mapping table
static MODEL_MAPPING: Lazy<HashMap<&'static str, &'static str>> = Lazy::new(|| {
    let mut m = HashMap::new();
    
    // ============== OpenAI Models ==============
    // GPT-4 series
    m.insert("gpt-4", "openai/gpt-4");
    m.insert("gpt-4-turbo", "openai/gpt-4-turbo");
    m.insert("gpt-4-turbo-preview", "openai/gpt-4-turbo");
    m.insert("gpt-4o", "openai/gpt-4o");
    m.insert("gpt-4o-mini", "openai/gpt-4o-mini");
    m.insert("gpt-4-32k", "openai/gpt-4-32k");
    m.insert("gpt-4-vision-preview", "openai/gpt-4-vision");
    
    // GPT-3.5 series
    m.insert("gpt-3.5-turbo", "openai/gpt-3.5-turbo");
    m.insert("gpt-3.5-turbo-16k", "openai/gpt-3.5-turbo-16k");
    m.insert("gpt-3.5-turbo-instruct", "openai/gpt-3.5-turbo-instruct");
    
    // o1 series
    m.insert("o1", "openai/o1");
    m.insert("o1-mini", "openai/o1-mini");
    m.insert("o1-preview", "openai/o1-preview");
    
    // ============== Anthropic Models ==============
    // Claude 3 series
    m.insert("claude-3-opus", "anthropic/claude-3-opus");
    m.insert("claude-3-opus-20240229", "anthropic/claude-3-opus");
    m.insert("claude-3-sonnet", "anthropic/claude-3-sonnet");
    m.insert("claude-3-sonnet-20240229", "anthropic/claude-3-sonnet");
    m.insert("claude-3-haiku", "anthropic/claude-3-haiku");
    m.insert("claude-3-haiku-20240307", "anthropic/claude-3-haiku");
    
    // Claude 3.5 series
    m.insert("claude-3.5-sonnet", "anthropic/claude-3.5-sonnet");
    m.insert("claude-3-5-sonnet", "anthropic/claude-3.5-sonnet");
    m.insert("claude-3-5-sonnet-20240620", "anthropic/claude-3.5-sonnet");
    m.insert("claude-3.5-haiku", "anthropic/claude-3.5-haiku");
    m.insert("claude-3-5-haiku", "anthropic/claude-3.5-haiku");
    
    // Claude 3.7 series
    m.insert("claude-3.7-sonnet", "anthropic/claude-3.7-sonnet");
    m.insert("claude-3-7-sonnet", "anthropic/claude-3.7-sonnet");
    
    // ============== Qwen (Alibaba) Models ==============
    // Qwen 2.5 series
    m.insert("qwen2.5-7b-instruct", "Qwen/Qwen2.5-7B-Instruct");
    m.insert("qwen2.5-14b-instruct", "Qwen/Qwen2.5-14B-Instruct");
    m.insert("qwen2.5-32b-instruct", "Qwen/Qwen2.5-32B-Instruct");
    m.insert("qwen2.5-72b-instruct", "Qwen/Qwen2.5-72B-Instruct");
    m.insert("qwen2.5-math-7b-instruct", "Qwen/Qwen2.5-Math-7B-Instruct");
    m.insert("qwen2.5-coder-7b-instruct", "Qwen/Qwen2.5-Coder-7B-Instruct");
    
    // Qwen 2 series
    m.insert("qwen2-7b-instruct", "Qwen/Qwen2-7B-Instruct");
    m.insert("qwen2-72b-instruct", "Qwen/Qwen2-72B-Instruct");
    
    // Qwen 1.5 series
    m.insert("qwen1.5-7b-instruct", "Qwen/Qwen1.5-7B-Chat");
    m.insert("qwen1.5-14b-instruct", "Qwen/Qwen1.5-14B-Chat");
    m.insert("qwen1.5-72b-instruct", "Qwen/Qwen1.5-72B-Chat");
    
    // Aliyun API model names -> HF mapping
    m.insert("qwen-turbo", "Qwen/Qwen2.5-7B-Instruct");
    m.insert("qwen-plus", "Qwen/Qwen2.5-14B-Instruct");
    m.insert("qwen-max", "Qwen/Qwen2.5-72B-Instruct");
    m.insert("qwen-long", "Qwen/Qwen2.5-32B-Instruct");
    
    // Qwen 3 series (newer)
    m.insert("qwen3-8b-instruct", "Qwen/Qwen3-8B-Instruct");
    m.insert("qwen3-14b-instruct", "Qwen/Qwen3-14B-Instruct");
    m.insert("qwen3-32b-instruct", "Qwen/Qwen3-32B-Instruct");
    m.insert("qwen3-72b-instruct", "Qwen/Qwen3-72B-Instruct");
    
    // Common variations
    m.insert("qwen3.5-plus", "Qwen/Qwen3.5-397B-A17B");
    m.insert("qwen3.5-turbo", "Qwen/Qwen2.5-7B-Instruct");
    m.insert("qwen3.5-max", "Qwen/Qwen2.5-72B-Instruct");
    
    // ============== DeepSeek Models ==============
    m.insert("deepseek-chat", "deepseek-ai/DeepSeek-V3");
    m.insert("deepseek-coder", "deepseek-ai/DeepSeek-Coder-V2-Instruct");
    m.insert("deepseek-v2", "deepseek-ai/DeepSeek-V2");
    m.insert("deepseek-v2.5", "deepseek-ai/DeepSeek-V2.5");
    m.insert("deepseek-v3", "deepseek-ai/DeepSeek-V3");
    m.insert("deepseek-r1", "deepseek-ai/DeepSeek-R1");
    m.insert("deepseek-r1-distill-qwen", "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B");
    
    // ============== Llama Models (Meta) ==============
    m.insert("llama-2-7b-chat", "meta-llama/Llama-2-7b-chat-hf");
    m.insert("llama-2-13b-chat", "meta-llama/Llama-2-13b-chat-hf");
    m.insert("llama-2-70b-chat", "meta-llama/Llama-2-70b-chat-hf");
    m.insert("llama-3-8b-instruct", "meta-llama/Meta-Llama-3-8B-Instruct");
    m.insert("llama-3-70b-instruct", "meta-llama/Meta-Llama-3-70B-Instruct");
    m.insert("llama-3.1-8b-instruct", "meta-llama/Meta-Llama-3.1-8B-Instruct");
    m.insert("llama-3.1-70b-instruct", "meta-llama/Meta-Llama-3.1-70B-Instruct");
    m.insert("llama-3.1-405b-instruct", "meta-llama/Meta-Llama-3.1-405B-Instruct");
    m.insert("llama-3.2-1b-instruct", "meta-llama/Llama-3.2-1B-Instruct");
    m.insert("llama-3.2-3b-instruct", "meta-llama/Llama-3.2-3B-Instruct");
    m.insert("llama-3.3-70b-instruct", "meta-llama/Llama-3.3-70B-Instruct");
    
    // ============== Mistral Models ==============
    m.insert("mistral-7b-instruct", "mistralai/Mistral-7B-Instruct-v0.3");
    m.insert("mistral-large", "mistralai/Mistral-Large-Instruct-2407");
    m.insert("mixtral-8x7b-instruct", "mistralai/Mixtral-8x7B-Instruct-v0.1");
    m.insert("mixtral-8x22b-instruct", "mistralai/Mixtral-8x22B-Instruct-v0.1");
    m.insert("mistral-small", "mistralai/Mistral-Small-24B-Instruct-2501");
    m.insert("codestral", "mistralai/Codestral-22B-v0.1");
    
    // ============== Yi Models (01.AI) ==============
    m.insert("yi-6b-chat", "01-ai/Yi-6B-Chat");
    m.insert("yi-9b-chat", "01-ai/Yi-9B-Chat");
    m.insert("yi-34b-chat", "01-ai/Yi-34B-Chat");
    m.insert("yi-1.5-9b-chat", "01-ai/Yi-1.5-9B-Chat");
    m.insert("yi-1.5-34b-chat", "01-ai/Yi-1.5-34B-Chat");
    m.insert("yi-lightning", "01-ai/Yi-1.5-34B-Chat");
    
    // ============== GLM Models (Zhipu AI) ==============
    m.insert("glm-4-9b-chat", "THUDM/glm-4-9b-chat");
    m.insert("glm-4", "THUDM/glm-4-9b-chat");
    m.insert("chatglm3-6b", "THUDM/chatglm3-6b");
    m.insert("chatglm-turbo", "THUDM/glm-4-9b-chat");
    m.insert("chatglm_pro", "THUDM/glm-4-9b-chat");
    
    // ============== Baichuan Models ==============
    m.insert("baichuan2-7b-chat", "baichuan-inc/Baichuan2-7B-Chat");
    m.insert("baichuan2-13b-chat", "baichuan-inc/Baichuan2-13B-Chat");
    m.insert("baichuan-7b", "baichuan-inc/Baichuan-7B");
    
    // ============== Moonshot Models ==============
    m.insert("moonshot-v1-8k", "moonshot-v1-8k");
    m.insert("moonshot-v1-32k", "moonshot-v1-32k");
    m.insert("moonshot-v1-128k", "moonshot-v1-128k");
    // Moonshot uses custom tokenizer, fallback to similar model
    m.insert("moonshot-v1", "Qwen/Qwen2.5-7B-Instruct");
    
    // ============== Kimi Models (Moonshot K2.5 series) ==============
    // Kimi K2.5 series - uses Qwen2.5 tokenizer as base
    m.insert("kimi-k2.5", "Qwen/Qwen2.5-7B-Instruct");
    m.insert("kimi-k2.5-8k", "Qwen/Qwen2.5-7B-Instruct");
    m.insert("kimi-k2.5-32k", "Qwen/Qwen2.5-7B-Instruct");
    m.insert("kimi-k2.5-128k", "Qwen/Qwen2.5-7B-Instruct");
    m.insert("kimi-k2.5-longcontext", "Qwen/Qwen2.5-7B-Instruct");
    
    // Legacy Kimi models
    m.insert("kimi-v1", "Qwen/Qwen2.5-7B-Instruct");
    m.insert("kimi-v1-8k", "Qwen/Qwen2.5-7B-Instruct");
    m.insert("kimi-v1-32k", "Qwen/Qwen2.5-7B-Instruct");
    m.insert("kimi-v1-128k", "Qwen/Qwen2.5-7B-Instruct");
    
    // ============== Google Gemini Models ==============
    m.insert("gemini-pro", "google/gemma-2-9b-it");
    m.insert("gemini-1.5-pro", "google/gemma-2-9b-it");
    m.insert("gemini-1.5-flash", "google/gemma-2-9b-it");
    m.insert("gemini-2.0-flash", "google/gemma-2-9b-it");
    
    // ============== Gemma Models (Google) ==============
    m.insert("gemma-2b-it", "google/gemma-2b-it");
    m.insert("gemma-7b-it", "google/gemma-7b-it");
    m.insert("gemma-2-9b-it", "google/gemma-2-9b-it");
    m.insert("gemma-2-27b-it", "google/gemma-2-27b-it");
    m.insert("gemma-3", "google/gemma-3-4b-it");
    m.insert("gemma-3-4b-it", "google/gemma-3-4b-it");
    
    // ============== Phi Models (Microsoft) ==============
    m.insert("phi-2", "microsoft/phi-2");
    m.insert("phi-3-mini", "microsoft/Phi-3-mini-4k-instruct");
    m.insert("phi-3-small", "microsoft/Phi-3-small-8k-instruct");
    m.insert("phi-3-medium", "microsoft/Phi-3-medium-4k-instruct");
    m.insert("phi-4", "microsoft/phi-4");
    
    // ============== Qwen-QwQ Models ==============
    m.insert("qwq-32b-preview", "Qwen/QwQ-32B-Preview");
    m.insert("qwq-32b", "Qwen/QwQ-32B-Preview");
    m.insert("qwq", "Qwen/QwQ-32B-Preview");
    
    // ============== InternLM Models ==============
    m.insert("internlm2-7b-chat", "internlm/internlm2-chat-7b");
    m.insert("internlm2-20b-chat", "internlm/internlm2-chat-20b");
    m.insert("internlm2.5-7b-chat", "internlm/internlm2_5-7b-chat");
    m.insert("internlm3-8b-instruct", "internlm/internlm3-8b-instruct");
    
    // ============== Command R Models (Cohere) ==============
    m.insert("command-r", "CohereForAI/c4ai-command-r-v01");
    m.insert("command-r-plus", "CohereForAI/c4ai-command-r-plus");
    
    // ============== Other Common Models ==============
    m.insert("starcoder2-7b", "bigcode/starcoder2-7b");
    m.insert("starcoder2-15b", "bigcode/starcoder2-15b");
    m.insert("codellama-7b-instruct", "codellama/CodeLlama-7b-Instruct-hf");
    m.insert("codellama-34b-instruct", "codellama/CodeLlama-34b-Instruct-hf");
    
    m
});

/// Map a model name to its HuggingFace model ID.
///
/// This function attempts to:
/// 1. Look up the model name in the predefined mapping table
/// 2. If not found, check if the name already looks like a HF ID (contains '/')
/// 3. If not, return the original name (let HF download fail naturally)
///
/// # Arguments
/// * `model_name` - The model name from API request (e.g., "gpt-4", "qwen-turbo")
///
/// # Returns
/// The corresponding HuggingFace model ID (e.g., "openai/gpt-4", "Qwen/Qwen2.5-7B-Instruct")
///
/// # Examples
/// ```
/// use agentsight::tokenizer::model_mapping::map_to_hf_model_id;
///
/// assert_eq!(map_to_hf_model_id("gpt-4"), "openai/gpt-4");
/// assert_eq!(map_to_hf_model_id("qwen-turbo"), "Qwen/Qwen2.5-7B-Instruct");
/// assert_eq!(map_to_hf_model_id("meta-llama/Llama-2-7b"), "meta-llama/Llama-2-7b");
/// ```
pub fn map_to_hf_model_id(model_name: &str) -> &str {
    // First, try exact match in mapping table
    if let Some(&hf_id) = MODEL_MAPPING.get(model_name) {
        return hf_id;
    }
    
    // Try case-insensitive match
    let lower_name = model_name.to_lowercase();
    for (key, value) in MODEL_MAPPING.iter() {
        if key.to_lowercase() == lower_name {
            return value;
        }
    }
    
    // If already looks like a HF model ID (contains '/'), return as-is
    if model_name.contains('/') {
        return model_name;
    }
    
    // Return original name - will fail at download time with clear error
    "Qwen/Qwen3.5-397B-A17B"
}

/// Check if a model name has a known mapping to HuggingFace.
///
/// # Arguments
/// * `model_name` - The model name to check
///
/// # Returns
/// `true` if the model name has a predefined mapping
pub fn has_mapping(model_name: &str) -> bool {
    MODEL_MAPPING.contains_key(model_name) || 
        MODEL_MAPPING.keys().any(|k| k.to_lowercase() == model_name.to_lowercase())
}

/// Get all known model name to HF ID mappings.
///
/// Useful for documentation and debugging.
pub fn all_mappings() -> impl Iterator<Item = (&'static str, &'static str)> {
    MODEL_MAPPING.iter().map(|(k, v)| (*k, *v))
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_openai_mapping() {
        assert_eq!(map_to_hf_model_id("gpt-4"), "openai/gpt-4");
        assert_eq!(map_to_hf_model_id("gpt-4o"), "openai/gpt-4o");
        assert_eq!(map_to_hf_model_id("gpt-4o-mini"), "openai/gpt-4o-mini");
        assert_eq!(map_to_hf_model_id("gpt-3.5-turbo"), "openai/gpt-3.5-turbo");
    }
    
    #[test]
    fn test_anthropic_mapping() {
        assert_eq!(map_to_hf_model_id("claude-3-opus"), "anthropic/claude-3-opus");
        assert_eq!(map_to_hf_model_id("claude-3.5-sonnet"), "anthropic/claude-3.5-sonnet");
        assert_eq!(map_to_hf_model_id("claude-3-5-sonnet"), "anthropic/claude-3.5-sonnet");
    }
    
    #[test]
    fn test_qwen_mapping() {
        assert_eq!(map_to_hf_model_id("qwen-turbo"), "Qwen/Qwen2.5-7B-Instruct");
        assert_eq!(map_to_hf_model_id("qwen-plus"), "Qwen/Qwen2.5-14B-Instruct");
        assert_eq!(map_to_hf_model_id("qwen-max"), "Qwen/Qwen2.5-72B-Instruct");
        assert_eq!(map_to_hf_model_id("qwen2.5-7b-instruct"), "Qwen/Qwen2.5-7B-Instruct");
    }
    
    #[test]
    fn test_deepseek_mapping() {
        assert_eq!(map_to_hf_model_id("deepseek-chat"), "deepseek-ai/DeepSeek-V3");
        assert_eq!(map_to_hf_model_id("deepseek-r1"), "deepseek-ai/DeepSeek-R1");
    }
    
    #[test]
    fn test_llama_mapping() {
        assert_eq!(map_to_hf_model_id("llama-3-8b-instruct"), "meta-llama/Meta-Llama-3-8B-Instruct");
        assert_eq!(map_to_hf_model_id("llama-3.1-70b-instruct"), "meta-llama/Meta-Llama-3.1-70B-Instruct");
    }
    
    #[test]
    fn test_hf_id_passthrough() {
        // Already a HF ID - should pass through
        assert_eq!(map_to_hf_model_id("Qwen/Qwen2.5-7B-Instruct"), "Qwen/Qwen2.5-7B-Instruct");
        assert_eq!(map_to_hf_model_id("meta-llama/Llama-2-7b"), "meta-llama/Llama-2-7b");
    }
    
    #[test]
    fn test_unknown_model() {
        // Unknown model - should return default fallback
        assert_eq!(map_to_hf_model_id("some-unknown-model"), "Qwen/Qwen3.5-397B-A17B");
    }
    
    #[test]
    fn test_case_insensitive() {
        assert_eq!(map_to_hf_model_id("GPT-4"), "openai/gpt-4");
        assert_eq!(map_to_hf_model_id("QWEN-TURBO"), "Qwen/Qwen2.5-7B-Instruct");
    }
    
    #[test]
    fn test_has_mapping() {
        assert!(has_mapping("gpt-4"));
        assert!(has_mapping("qwen-turbo"));
        assert!(!has_mapping("some-unknown-model"));
    }
}
