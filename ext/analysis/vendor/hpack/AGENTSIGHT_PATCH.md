# Local hpack 0.3.0 patch

This is the MIT-licensed hpack 0.3.0 crate. AgentSight uses a local path copy
because its decoder panics on a truncated dynamic-table-size update such as
`[0x3f]`. The patch changes `update_max_dynamic_size` to propagate the
existing integer-decoding error through `decode_with_cb` and adds a regression
test. The AgentSight HTTP/2 parser resets its decoder after an error so partial
state from a malformed header block is not reused.

The crate root also allows four legacy compiler lints in this vendored copy
(`deprecated`, `unused_parens`, `dead_code`, and
`mismatched_lifetime_syntaxes`) so CI's `-D warnings` check can compile it
without changing unrelated upstream implementation.
