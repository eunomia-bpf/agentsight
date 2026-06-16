from __future__ import annotations

import re
from collections.abc import Iterable

from .util import one_word


class SimpleTagger:
    """Deterministic bootstrap tagger.

    This is intentionally boring. The research implementation can swap in a
    small LLM later, but pprof export should work without model setup.
    """

    def tag(self, kind: str, text: str, hints: Iterable[str] = ()) -> str:
        source = f"{' '.join(hints)} {text}".lower()
        pairs = [
            (r"pprof|profile|profiling|flamegraph|folded|trace", "profile"),
            (r"osdi|sosp|nsdi|eurosys|paper|论文|学术|review", "paper"),
            (r"visual|可视化|svg|html|render|dashboard|图", "visual"),
            (r"cluster|聚类|聚合|aggregate|collapse|long.tail", "cluster"),
            (r"semantic|tag|标签|one.word|一个词|单词", "tagging"),
            (r"llama|gguf|qwen|haiku|model|模型", "model"),
            (r"session|history|prompt|conversation|上下文", "session"),
            (r"subagent|multi.agent|spawn", "subagent"),
            (r"test|cargo test|pytest|验证|check", "test"),
            (r"debug|bug|failed|error|修复|fix", "debug"),
            (r"implement|实现|patch|edit|write|新增|修改", "implement"),
            (r"commit|push|git add|git commit", "git"),
            (r"cleanup|clean|delete|清理|archive", "cleanup"),
            (r"design|设计|doc|文档|readme", "design"),
            (r"network|github|crates|download|hf\.co|huggingface", "network"),
            (r"collector|ebpf|kernel|process|syscall|system effect", "collector"),
            (r"frontend|react|next|ui|css", "frontend"),
            (r"read|inspect|search|rg|sed|grep|查看|分析", "inspect"),
            (r"claim|mismatch|verdict|validation", "claim"),
            (r"token|cost|usage", "token"),
            (r"schema|jsonl|parse|parser|proto", "parse"),
            (r"compare|diff|baseline", "diff"),
        ]
        for pattern, tag in pairs:
            if re.search(pattern, source):
                return tag
        if kind == "llm":
            return "response"
        if kind == "tool":
            return one_word(source, "tool")
        return one_word(source, "work")
