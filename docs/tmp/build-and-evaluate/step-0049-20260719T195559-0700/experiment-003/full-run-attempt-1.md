# Full Run Attempt 1 — V2 Unbounded-Whitespace Grammar

**Stopped:** 2026-07-19T22:11:12-07:00  
**State:** Invalid/incomplete; not scored  
**Semantic algorithm:** unchanged V2 single-frame stack

## Executed Scope

The first V2 full attempt retained 19,748 valid source-only transitions across
all 405 session caches. At shutdown, 378 trajectories were complete and 27
were partial. The official stage manifest and all target scores remained
unopened. No partial-population metric is permitted.

The failed inference outputs remain evidence under
.agentsight/experiments/rq3-qwen3b-semantic-task-stack-v2/full-invalid-unbounded-whitespace-v2/
and will not be reused in the corrected run.

## Failure

The single-frame grammar bounded new_frame to either null or one label of at
most 48 characters, so Experiment 002's arbitrary-list failure could not
recur. It nevertheless left JSON whitespace as:

    ws ::= [ \t\n]*

On one operation, Qwen emitted a valid short frame prefix followed by tabs
inside a legal whitespace position. Because the grammar admitted an unbounded
number of tabs, generation reached the fixed 96-token response budget before
the closing JSON delimiters. The independent parser rejected the truncated
response. There was no retry, completion, clamp, fallback, or score.

This is an output-language enforcement bug. It does not change keep_depth, the
zero-or-one-frame transition, label semantics, model, prompt, visible evidence,
seed, temperature, RQ, baseline, metric, or interpretation.

## First Repair And Review Block

The first proposed enforcement repair bounded each whitespace position:

    ws ::= [ \t\n]{0,8}

The independent repair reviewer correctly blocked this version. Although the
language became finite, eight legal whitespace positions could still contribute
up to 64 tab tokens. Retained compact responses with hex-heavy labels already
used 49–52 tokens, so a legal v2.1 response could still exceed the 96-token
budget. No v2.1 preflight or full run was started.

## Final Compact-JSON Repair

The grammar now admits only canonical compact JSON with no optional whitespace:

    {"keep_depth":20866,"new_frame":"aaaaaaaa..."}

Legal depth is enumerated from the current stack, new_frame is null or one
48-character label, and all punctuation and keys are fixed. A CodeTrace
trajectory has at most 20,866 operations, so keep_depth uses at most five ASCII
digits. The longest admitted response has fewer than 83 ASCII bytes. The Qwen
byte-level tokenizer can encode each ASCII byte with at most one fallback token,
so every admitted response requires fewer than 83 tokens and is strictly below
the fixed 96-token budget. The constraint version is now
direct-gbnf-single-frame-compact-json-v2.2.

Because this changes the decoding constraint after an invalid run, both
preflight and full inference will restart from empty caches. The repair may not
change the system prompt or use stage labels or scores.
