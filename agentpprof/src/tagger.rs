use anyhow::{Result, anyhow, bail};
use chrono::Utc;
use rayon::prelude::*;
use regex::Regex;
use serde::{Deserialize, Serialize};
use serde_json::{Value, json};
use std::collections::BTreeMap;
use std::fs;
use std::path::PathBuf;
use std::sync::atomic::{AtomicUsize, Ordering};
use std::time::Duration;

use crate::session::{SessionRecord, short_hash, truncate_clean};

const TAG_CACHE_VERSION: &str = "v3";
const TAG_GRAMMAR: &str =
    "root ::= [a-z] [a-z] [a-z] [a-z]? [a-z]? [a-z]? [a-z]? [a-z]? [a-z]? [a-z]? [a-z]? [a-z]?";

#[derive(Default, Serialize, Clone)]
pub struct TagStats {
    pub requests: usize,
    pub cache_hits: usize,
    pub llm_calls: usize,
    pub llm_successes: usize,
    pub failures: Vec<String>,
}

#[derive(Serialize, Deserialize, Clone)]
pub struct TagEntry {
    pub tag: String,
    pub kind: String,
    pub source_hash: String,
    pub created_at: String,
    pub llm: LlmInfo,
}

#[derive(Serialize, Deserialize, Clone)]
pub struct LlmInfo {
    pub provider: String,
    pub base_url: String,
    pub model: String,
}

#[derive(Deserialize)]
struct ExistingCache {
    tags: Option<BTreeMap<String, TagEntry>>,
}

pub struct LlamaTagger {
    cache_path: PathBuf,
    base_url: String,
    model: String,
    timeout: Duration,
    max_uncached: isize,
    stats: TagStats,
    cache: BTreeMap<String, TagEntry>,
    agent: ureq::Agent,
}

impl LlamaTagger {
    pub fn new(
        cache_path: PathBuf,
        base_url: String,
        model: String,
        timeout: Duration,
        max_uncached: isize,
    ) -> Self {
        let cache = fs::read_to_string(&cache_path)
            .ok()
            .and_then(|text| serde_json::from_str::<ExistingCache>(&text).ok())
            .and_then(|payload| payload.tags)
            .unwrap_or_default();
        let agent = ureq::AgentBuilder::new()
            .timeout_read(timeout)
            .timeout_write(timeout)
            .build();
        Self {
            cache_path,
            base_url: base_url.trim_end_matches('/').to_string(),
            model,
            timeout,
            max_uncached,
            stats: TagStats::default(),
            cache,
            agent,
        }
    }

    pub fn tag(&mut self, kind: &str, text: &str, hints: &[String]) -> Result<String> {
        self.stats.requests += 1;
        let source = truncate_clean(&format!("{} {}", hints.join(" "), text), 1800);
        let key = short_hash(
            &format!(
                "{}\nllama.cpp\n{}\n{}\n{}\n{}\n{}",
                TAG_CACHE_VERSION, self.base_url, self.model, kind, TAG_GRAMMAR, source
            ),
            32,
        );
        if let Some(entry) = self.cache.get(&key) {
            if valid_tag(&entry.tag) {
                self.stats.cache_hits += 1;
                return Ok(entry.tag.clone());
            }
        }
        if self.max_uncached >= 0 && self.stats.llm_calls as isize >= self.max_uncached {
            bail!(
                "LLM tag budget exhausted after {} uncached calls",
                self.stats.llm_calls
            );
        }
        let tag = self.tag_uncached(kind, &source)?;
        self.cache.insert(
            key,
            TagEntry {
                tag: tag.clone(),
                kind: kind.to_string(),
                source_hash: short_hash(&source, 24),
                created_at: now_iso(),
                llm: LlmInfo {
                    provider: "llama.cpp".to_string(),
                    base_url: self.base_url.clone(),
                    model: self.model.clone(),
                },
            },
        );
        Ok(tag)
    }

    fn tag_uncached(&mut self, kind: &str, source: &str) -> Result<String> {
        let mut previous = String::new();
        for attempt in 0..2 {
            let prompt = tag_prompt(kind, source, if attempt == 0 { "" } else { &previous });
            let raw = self.call_llm(&prompt)?;
            if let Some(tag) = sanitize_tag(&raw) {
                if valid_tag(&tag) {
                    self.stats.llm_successes += 1;
                    return Ok(tag);
                }
            }
            previous = raw;
        }
        let detail = truncate_clean(&previous, 200);
        self.stats
            .failures
            .push(format!("invalid_output kind={kind} output={detail}"));
        bail!("LLM returned invalid one-word tag for {kind}: {detail:?}");
    }

    fn call_llm(&mut self, prompt: &str) -> Result<String> {
        self.stats.llm_calls += 1;
        let url = format!("{}/v1/chat/completions", self.base_url);
        let body = json!({
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You output exactly one lowercase English word."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0,
            "max_tokens": 8,
            "grammar": TAG_GRAMMAR,
            "stream": false
        });
        let response = self
            .agent
            .post(&url)
            .timeout(self.timeout)
            .send_json(body)
            .map_err(|error| anyhow!("llama.cpp request failed at {url}: {error}"))?;
        let payload: Value = response
            .into_json()
            .map_err(|error| anyhow!("invalid llama.cpp JSON response: {error}"))?;
        extract_llm_text(&payload).ok_or_else(|| anyhow!("llama.cpp response had no text content"))
    }

    pub fn save(&self) -> Result<()> {
        if let Some(parent) = self.cache_path.parent() {
            fs::create_dir_all(parent)?;
        }
        let payload = json!({
            "schema_version": 2,
            "created_by": "agentpprof-rust",
            "updated_at": now_iso(),
            "llm": {
                "provider": "llama.cpp",
                "base_url": self.base_url,
                "model": self.model,
            },
            "stats": self.stats,
            "tags": self.cache,
        });
        fs::write(&self.cache_path, serde_json::to_vec_pretty(&payload)?)?;
        Ok(())
    }
}

fn tag_prompt(kind: &str, source: &str, invalid_previous: &str) -> String {
    let retry = if invalid_previous.is_empty() {
        String::new()
    } else {
        format!(
            "\nPrevious invalid answer: {invalid_previous:?}\nReturn only one valid word now.\n"
        )
    };
    format!(
        "You label local AI coding-agent session fragments.\n\
         Return exactly one lowercase English word, 3 to 12 letters.\n\
         No spaces, punctuation, quotes, markdown, or explanation.\n\
         Choose the most specific short action or topic word from the fragment itself.\n\
         Do not concatenate multiple words into one string. Do not output fragments like codingupdate, testdebug, or flamegraphfix.\n\
         Do not use generic words like task, work, misc, thing, stuff, or other.\n\
         {retry}\nFragment kind: {kind}\nFragment:\n{}\n\nTag:",
        truncate_clean(source, 1600)
    )
}

fn extract_llm_text(payload: &Value) -> Option<String> {
    payload
        .pointer("/choices/0/message/content")
        .and_then(Value::as_str)
        .or_else(|| payload.pointer("/choices/0/text").and_then(Value::as_str))
        .or_else(|| payload.get("content").and_then(Value::as_str))
        .map(str::to_string)
}

pub struct RegexTagger {
    rules: Vec<TagRule>,
    use_preset: bool,
}

struct TagRule {
    kind: String,
    tag: String,
    regex: Regex,
}

#[derive(Default, Debug, Clone)]
pub struct TagDiagnostics {
    pub total_sessions: usize,
    pub matched_sessions: usize,
    pub unmatched_sessions: usize,
    pub total_prompts: usize,
    pub matched_prompts: usize,
    pub unmatched_prompts: usize,
    pub total_llm_calls: usize,
    pub matched_llm_calls: usize,
    pub unmatched_llm_calls: usize,
    pub unmatched_samples: Vec<UnmatchedSample>,
    pub tag_counts: BTreeMap<String, usize>,
}

#[derive(Debug, Clone)]
pub struct UnmatchedSample {
    pub kind: String,
    pub preview: String,
    pub session_id: String,
}

impl RegexTagger {
    pub fn new(rule_specs: &[String], use_preset: bool) -> Result<Self> {
        let mut rules = Vec::new();
        for spec in rule_specs {
            rules.push(parse_tag_rule(spec)?);
        }
        Ok(Self { rules, use_preset })
    }

    pub fn tag(&self, kind: &str, text: &str, _hints: &[String]) -> Option<String> {
        self.tag_with_fallback(kind, text, None)
    }

    pub fn tag_with_fallback(
        &self,
        kind: &str,
        text: &str,
        _fallback: Option<&str>,
    ) -> Option<String> {
        if let Some(tag) = self.custom_tag(kind, text) {
            return Some(tag);
        }
        if self.use_preset {
            let haystack = text.to_ascii_lowercase();
            if let Some(tag) = keyword_tag(&haystack) {
                return Some(tag);
            }
        }
        None
    }

    fn custom_tag(&self, kind: &str, source: &str) -> Option<String> {
        self.rules
            .iter()
            .find(|rule| (rule.kind == kind || rule.kind == "all") && rule.regex.is_match(source))
            .map(|rule| rule.tag.clone())
    }
}

fn parse_tag_rule(spec: &str) -> Result<TagRule> {
    let (left, pattern) = spec
        .split_once('=')
        .ok_or_else(|| anyhow!("invalid --tag-rule {spec:?}; expected KIND:TAG=REGEX"))?;
    let (kind, tag) = left
        .split_once(':')
        .ok_or_else(|| anyhow!("invalid --tag-rule {spec:?}; expected KIND:TAG=REGEX"))?;
    if !matches!(kind, "session" | "prompt" | "llm" | "all") {
        bail!("invalid --tag-rule kind {kind:?}; expected session, prompt, llm, or all");
    }
    if let Err(reason) = validate_tag(tag) {
        bail!("invalid --tag-rule tag {tag:?}; {reason}");
    }
    if pattern.is_empty() {
        bail!("invalid --tag-rule {spec:?}; regex pattern cannot be empty");
    }
    // Warn about catch-all patterns that defeat semantic tagging
    if pattern == "." || pattern == ".*" || pattern == ".+" {
        eprintln!(
            "Warning: catch-all rule '{}:{}={}' will match everything. \
             This defeats semantic tagging. Use specific patterns instead.",
            kind, tag, pattern
        );
    }
    let regex = Regex::new(pattern)
        .map_err(|error| anyhow!("invalid --tag-rule regex {pattern:?}: {error}"))?;
    Ok(TagRule {
        kind: kind.to_string(),
        tag: tag.to_string(),
        regex,
    })
}

pub const UNMATCHED_TAG: &str = "unmatched";

pub fn annotate_sessions_regex(
    sessions: &mut [SessionRecord],
    tagger: &RegexTagger,
) -> TagDiagnostics {
    // Use parallel processing for tagging
    let total_sessions = AtomicUsize::new(0);
    let matched_sessions = AtomicUsize::new(0);
    let total_prompts = AtomicUsize::new(0);
    let matched_prompts = AtomicUsize::new(0);
    let total_llm_calls = AtomicUsize::new(0);
    let matched_llm_calls = AtomicUsize::new(0);

    // Process sessions in parallel
    sessions.par_iter_mut().for_each(|session| {
        total_sessions.fetch_add(1, Ordering::Relaxed);

        // Tag session
        let prompt_text = session
            .user_requests
            .iter()
            .take(8)
            .map(|req| req.preview.as_str())
            .collect::<Vec<_>>()
            .join(" ");
        let session_input = truncate_clean(
            &format!("{} {} {}", session.title, session.cwd, prompt_text),
            1500,
        );
        if let Some(tag) = tagger.tag(
            "session",
            &session_input,
            &[session.source.clone(), session.model.clone()],
        ) {
            session.session_tag = tag;
            matched_sessions.fetch_add(1, Ordering::Relaxed);
        } else {
            session.session_tag = UNMATCHED_TAG.to_string();
        }

        // Tag prompts
        for req in &mut session.user_requests {
            total_prompts.fetch_add(1, Ordering::Relaxed);
            if let Some(tag) = tagger.tag(
                "prompt",
                &req.preview,
                &[session.session_tag.clone(), session.source.clone()],
            ) {
                req.tag = tag;
                matched_prompts.fetch_add(1, Ordering::Relaxed);
            } else {
                req.tag = UNMATCHED_TAG.to_string();
            }
        }

        // Tag LLM calls
        for call in &mut session.llm_calls {
            total_llm_calls.fetch_add(1, Ordering::Relaxed);
            if let Some(tag) = tagger.tag("llm", &call.preview, &[]) {
                call.tag = tag;
                matched_llm_calls.fetch_add(1, Ordering::Relaxed);
            } else {
                call.tag = UNMATCHED_TAG.to_string();
            }
        }
    });

    // Collect diagnostics (sequential pass for samples and tag counts)
    let mut diagnostics = TagDiagnostics {
        total_sessions: total_sessions.load(Ordering::Relaxed),
        matched_sessions: matched_sessions.load(Ordering::Relaxed),
        unmatched_sessions: 0,
        total_prompts: total_prompts.load(Ordering::Relaxed),
        matched_prompts: matched_prompts.load(Ordering::Relaxed),
        unmatched_prompts: 0,
        total_llm_calls: total_llm_calls.load(Ordering::Relaxed),
        matched_llm_calls: matched_llm_calls.load(Ordering::Relaxed),
        unmatched_llm_calls: 0,
        unmatched_samples: Vec::new(),
        tag_counts: BTreeMap::new(),
    };

    diagnostics.unmatched_sessions = diagnostics.total_sessions - diagnostics.matched_sessions;
    diagnostics.unmatched_prompts = diagnostics.total_prompts - diagnostics.matched_prompts;
    diagnostics.unmatched_llm_calls = diagnostics.total_llm_calls - diagnostics.matched_llm_calls;

    // Collect samples and tag counts (sequential)
    for session in sessions.iter() {
        if session.session_tag == UNMATCHED_TAG && diagnostics.unmatched_samples.len() < 30 {
            let session_input = truncate_clean(
                &format!("{} {}", session.cwd, session.title),
                120,
            );
            diagnostics.unmatched_samples.push(UnmatchedSample {
                kind: "session".to_string(),
                preview: session_input,
                session_id: session.session_id.clone(),
            });
        }

        for req in &session.user_requests {
            if req.tag == UNMATCHED_TAG {
                *diagnostics
                    .tag_counts
                    .entry("prompt:unmatched".to_string())
                    .or_default() += 1;
                if diagnostics.unmatched_samples.len() < 30 {
                    diagnostics.unmatched_samples.push(UnmatchedSample {
                        kind: "prompt".to_string(),
                        preview: truncate_clean(&req.preview, 120),
                        session_id: session.session_id.clone(),
                    });
                }
            } else {
                *diagnostics
                    .tag_counts
                    .entry(format!("prompt:{}", req.tag))
                    .or_default() += 1;
            }
        }

        for call in &session.llm_calls {
            if call.tag == UNMATCHED_TAG {
                if diagnostics.unmatched_samples.len() < 30 {
                    diagnostics.unmatched_samples.push(UnmatchedSample {
                        kind: "llm".to_string(),
                        preview: truncate_clean(&call.preview, 120),
                        session_id: session.session_id.clone(),
                    });
                }
            } else {
                *diagnostics
                    .tag_counts
                    .entry(format!("llm:{}", call.tag))
                    .or_default() += 1;
            }
        }
    }

    // Print warnings for unmatched items (target: <5% unmatched)
    let prompt_pct = if diagnostics.total_prompts > 0 {
        diagnostics.unmatched_prompts as f64 / diagnostics.total_prompts as f64 * 100.0
    } else {
        0.0
    };
    let session_pct = if diagnostics.total_sessions > 0 {
        diagnostics.unmatched_sessions as f64 / diagnostics.total_sessions as f64 * 100.0
    } else {
        0.0
    };
    let llm_pct = if diagnostics.total_llm_calls > 0 {
        diagnostics.unmatched_llm_calls as f64 / diagnostics.total_llm_calls as f64 * 100.0
    } else {
        0.0
    };

    if diagnostics.unmatched_sessions > 0 {
        eprintln!(
            "Warning: {}/{} sessions unmatched ({:.1}%). Add session tag rules. Target: <5%.",
            diagnostics.unmatched_sessions, diagnostics.total_sessions, session_pct
        );
    }
    if diagnostics.unmatched_prompts > 0 {
        eprintln!(
            "Warning: {}/{} prompts unmatched ({:.1}%). Add prompt tag rules. Target: <5%.",
            diagnostics.unmatched_prompts, diagnostics.total_prompts, prompt_pct
        );
    }
    if diagnostics.unmatched_llm_calls > 0 {
        eprintln!(
            "Warning: {}/{} LLM calls unmatched ({:.1}%). Add llm tag rules. Target: <5%.",
            diagnostics.unmatched_llm_calls, diagnostics.total_llm_calls, llm_pct
        );
    }

    // Distribution analysis for each category
    print_distribution_analysis("prompt", &diagnostics.tag_counts);
    print_distribution_analysis("llm", &diagnostics.tag_counts);
    print_distribution_analysis("session", &diagnostics.tag_counts);

    diagnostics
}

fn print_distribution_analysis(kind: &str, tag_counts: &BTreeMap<String, usize>) {
    let prefix = format!("{}:", kind);
    let tags: Vec<_> = tag_counts
        .iter()
        .filter(|(k, _)| k.starts_with(&prefix) && !k.ends_with(":unmatched"))
        .collect();

    if tags.is_empty() {
        return;
    }

    let total: usize = tags.iter().map(|(_, v)| *v).sum();
    let num_tags = tags.len();

    // Sort by count descending
    let mut sorted: Vec<_> = tags.iter().map(|(k, v)| (k.as_str(), **v)).collect();
    sorted.sort_by_key(|item| std::cmp::Reverse(item.1));

    // Calculate distribution metrics
    let top1_pct = sorted.first().map(|(_, v)| *v as f64 / total as f64 * 100.0).unwrap_or(0.0);
    let top3_sum: usize = sorted.iter().take(3).map(|(_, v)| *v).sum();
    let top3_pct = top3_sum as f64 / total as f64 * 100.0;
    let top5_sum: usize = sorted.iter().take(5).map(|(_, v)| *v).sum();
    let top5_pct = top5_sum as f64 / total as f64 * 100.0;

    // Calculate entropy (higher = more evenly distributed)
    let entropy: f64 = tags
        .iter()
        .map(|(_, v)| {
            let p = **v as f64 / total as f64;
            if p > 0.0 { -p * p.ln() } else { 0.0 }
        })
        .sum();
    let max_entropy = (num_tags as f64).ln();
    let normalized_entropy = if max_entropy > 0.0 { entropy / max_entropy } else { 0.0 };

    // Print distribution summary
    eprintln!(
        "Distribution ({} tags, {} total): top1={:.1}%, top3={:.1}%, top5={:.1}%, entropy={:.2}",
        num_tags, total, top1_pct, top3_pct, top5_pct, normalized_entropy
    );

    // Print top 5 tags
    eprintln!("  Top tags:");
    for (i, (tag, count)) in sorted.iter().take(5).enumerate() {
        let pct = *count as f64 / total as f64 * 100.0;
        eprintln!("    {}. {} = {} ({:.1}%)", i + 1, tag, count, pct);
    }

    // Warnings based on quality criteria
    if top1_pct > 40.0 {
        eprintln!(
            "  Warning: {} dominates ({:.1}%). Target: top1 < 40%. Split into sub-categories.",
            sorted[0].0, top1_pct
        );
    }
    if top3_pct > 80.0 && num_tags > 3 {
        eprintln!(
            "  Warning: top 3 tags cover {:.1}%. Target: top3 < 70%. Add more specific rules.",
            top3_pct
        );
    }
    if num_tags < 5 {
        eprintln!(
            "  Warning: only {} tags. Target: 10-20 categories for meaningful aggregation.",
            num_tags
        );
    } else if num_tags > 25 {
        eprintln!(
            "  Warning: {} tags is too fragmented. Target: 10-20 categories. Merge similar tags.",
            num_tags
        );
    }
    if normalized_entropy < 0.5 && num_tags > 3 {
        eprintln!(
            "  Warning: low entropy ({:.2}). Distribution is uneven. Target: entropy > 0.7.",
            normalized_entropy
        );
    }
}

pub fn annotate_sessions(sessions: &mut [SessionRecord], tagger: &mut LlamaTagger) -> Result<()> {
    for session in sessions {
        let prompt_text = session
            .user_requests
            .iter()
            .take(8)
            .map(|req| req.preview.as_str())
            .collect::<Vec<_>>()
            .join(" ");
        session.session_tag = tagger.tag(
            "session",
            &truncate_clean(
                &format!("{} {} {}", session.title, session.cwd, prompt_text),
                1500,
            ),
            &[session.source.clone(), session.model.clone()],
        )?;
        for req in &mut session.user_requests {
            req.tag = tagger.tag(
                "prompt",
                &req.preview,
                &[session.session_tag.clone(), session.source.clone()],
            )?;
        }
        for idx in 0..session.llm_calls.len() {
            let call = &session.llm_calls[idx];
            session.llm_calls[idx].tag = tagger.tag(
                "llm",
                &call.preview,
                &[
                    session.session_tag.clone(),
                    session.source.clone(),
                    call.model.clone(),
                ],
            )?;
        }
    }
    Ok(())
}

fn keyword_tag(text: &str) -> Option<String> {
    let rules: &[(&str, &[&str])] = &[
        (
            "profile",
            &[
                "pprof",
                "flamegraph",
                "trace",
                "otel",
                "span",
                "observability",
                "火焰图",
            ],
        ),
        (
            "research",
            &[
                "paper",
                "osdi",
                "novelty",
                "evaluation",
                "literature",
                "论文",
                "调研",
            ],
        ),
        (
            "design",
            &[
                "design",
                "architecture",
                "visualization",
                "schema",
                "projection",
                "设计",
                "可视化",
            ],
        ),
        (
            "debug",
            &["debug", "failing", "failed", "error", "panic", "bug", "fix"],
        ),
        (
            "test",
            &["test", "cargo test", "pytest", "unit test", "coverage"],
        ),
        ("review", &["review", "audit", "pr", "diff", "regression"]),
        (
            "release",
            &["release", "publish", "crates.io", "version", "tag"],
        ),
        (
            "build",
            &["build", "compile", "cargo check", "npm run build"],
        ),
        (
            "docs",
            &["readme", "docs", "documentation", "latex", "markdown"],
        ),
        ("git", &["branch", "commit", "push", "rebase", "merge"]),
        (
            "network",
            &["network", "github.com", "curl", "wget", "fetch"],
        ),
        ("frontend", &["frontend", "react", "css", "html", "svg"]),
        ("parser", &["parse", "parser", "jsonl", "session"]),
        ("cli", &["cli", "argument", "option", "subcommand", "flag"]),
    ];
    rules
        .iter()
        .find(|(_, needles)| needles.iter().any(|needle| text.contains(needle)))
        .map(|(tag, _)| (*tag).to_string())
}

pub fn default_tag_cache_path() -> PathBuf {
    dirs::cache_dir()
        .or_else(|| dirs::home_dir().map(|home| home.join(".cache")))
        .unwrap_or_else(|| PathBuf::from("."))
        .join("agentpprof/tags.json")
}

pub fn sanitize_tag(text: &str) -> Option<String> {
    let trimmed = text
        .trim()
        .trim_matches(|c: char| {
            c.is_whitespace() || ['"', '\'', '`', '*', '_', '.', '>'].contains(&c)
        })
        .to_ascii_lowercase();
    let words = trimmed
        .split(|c: char| !c.is_ascii_alphanumeric())
        .filter(|part| !part.is_empty())
        .collect::<Vec<_>>();
    if words.len() == 1 {
        Some(words[0].to_string())
    } else {
        None
    }
}

/// Validate tag format. Returns Ok(()) if valid, Err with reason if invalid.
/// Warns (to stderr) for vague tags but still accepts them.
pub fn validate_tag(tag: &str) -> Result<(), String> {
    if tag.is_empty() {
        return Err("tag cannot be empty".to_string());
    }
    if tag.len() < 3 {
        return Err(format!("tag \"{}\" too short (minimum 3 letters)", tag));
    }
    if tag.len() > 12 {
        return Err(format!("tag \"{}\" too long (maximum 12 letters)", tag));
    }
    if !tag.chars().next().unwrap().is_ascii_lowercase() {
        return Err(format!("tag \"{}\" must start with lowercase letter", tag));
    }
    if !tag.chars().all(|c| c.is_ascii_lowercase()) {
        return Err(format!(
            "tag \"{}\" must contain only lowercase letters",
            tag
        ));
    }
    // Warn for vague tags that don't convey semantic meaning
    const VAGUE_TAGS: &[&str] = &[
        "task", "work", "misc", "thing", "stuff", "other", "item", "data",
    ];
    if VAGUE_TAGS.contains(&tag) {
        eprintln!(
            "Warning: tag \"{}\" is vague and unlikely to aggregate meaningfully. Consider a more specific semantic tag.",
            tag
        );
    }
    Ok(())
}

pub fn valid_tag(tag: &str) -> bool {
    validate_tag(tag).is_ok()
}

fn now_iso() -> String {
    Utc::now().to_rfc3339_opts(chrono::SecondsFormat::Secs, true)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn tag_validation_has_no_label_fallback() {
        assert!(valid_tag("debug"));
        assert!(!valid_tag("two words"));
        // Vague tags are now allowed (with warning) - no blocklist
        assert!(valid_tag("task"));
        assert!(valid_tag("misc"));
        assert_eq!(sanitize_tag("debug."), Some("debug".to_string()));
        assert_eq!(sanitize_tag("debug tests"), None);
        assert!(!valid_tag("codingupdateflamegraph"));
    }

    #[test]
    fn custom_tag_rules_match() {
        let tagger = RegexTagger::new(
            &[
                "prompt:verify=(?i)cargo test|pytest".to_string(),
                "prompt:review=(?i)review|diff|regression".to_string(),
            ],
            false,
        )
        .unwrap();
        assert_eq!(
            tagger.tag("prompt", "please review this diff", &[]),
            Some("review".to_string())
        );
        assert_eq!(
            tagger.tag("prompt", "run cargo test", &[]),
            Some("verify".to_string())
        );
    }

    #[test]
    fn no_rules_returns_none() {
        let tagger = RegexTagger::new(&[], false).unwrap();
        assert_eq!(tagger.tag("prompt", "random text", &[]), None);
        assert_eq!(tagger.tag("session", "random text", &[]), None);
    }

    #[test]
    fn preset_enables_builtin_rules() {
        let tagger = RegexTagger::new(&[], true).unwrap();
        assert_eq!(
            tagger.tag("prompt", "please debug this error", &[]),
            Some("debug".to_string())
        );
        assert_eq!(
            tagger.tag("prompt", "run cargo test", &[]),
            Some("test".to_string())
        );
    }

    #[test]
    fn custom_rules_are_scoped_by_kind() {
        let tagger = RegexTagger::new(&["prompt:review=x y".to_string()], false).unwrap();
        assert_eq!(tagger.tag("prompt", "x y", &[]), Some("review".to_string()));
        assert_eq!(tagger.tag("session", "x y", &[]), None);
    }

    #[test]
    fn custom_rules_do_not_match_hints() {
        let tagger = RegexTagger::new(&["prompt:review=(?i)review".to_string()], false).unwrap();
        assert_eq!(tagger.tag("prompt", "x y", &["review".to_string()]), None);
    }

    #[test]
    fn invalid_custom_tag_rules_are_rejected() {
        assert!(RegexTagger::new(&["prompt:two-words=review".to_string()], false).is_err());
        assert!(RegexTagger::new(&["tool:review=review".to_string()], false).is_err());
        assert!(RegexTagger::new(&["prompt:review=(".to_string()], false).is_err());
    }
}
