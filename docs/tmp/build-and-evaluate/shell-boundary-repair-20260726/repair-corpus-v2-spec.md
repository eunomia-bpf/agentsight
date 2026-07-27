# RQ7 repair-corpus-v2 source-direct supplement

Specification ID: `native-root-conformance-v5-repair-20260726`.

This supplement replaces the shell-boundary rules of the parent
`native-root-conformance-v4` question specification for the inspected
116-question corpus. All other native-root identity, ordering, status,
lifecycle, answer, and workspace rules remain unchanged.

This is a repair corpus, not held-out evidence. The 116 parent question IDs,
their family allocation (29 each for A, B, C, and D), and their frozen P0--P4
paths remain fixed. Paths are remapped to the repaired artifact identities;
anchors are not reranked. This fixed-question design measures closure of the
known defects and cannot support a new generality claim.

Shell actions use source-direct semantics:

- a multi-source `cp S1 ... Sn DIR`, including a trailing fd redirection such
  as `2>&1`, reads every source and creates `DIR/basename(Si)`;
- redirection targets are not repository artifacts;
- non-recursive `git rm` contributes its exact operands, while recursive
  deletes are directory scope and are excluded from the exact-artifact ledger;
- balanced process-substitution bodies contribute their direct file actions
  under a single literal leading `cd`;
- a shell command is parsed across physical newlines, including quoted
  multiline arguments;
- the native Claude `Bash` command beginning with a bare backslash-newline that
  was rejected before launch contributes no attempted action; in generic shell
  transports, backslash-newline remains a normal POSIX line continuation; and
- every supported JSON-like static `tools.exec_command({...})` object
  contributes its actions under its own workdir.

Only exact non-scope actions enter the attempted and confirmed-effect artifact
ledgers. Production directory-scope annotations remain available to other
consumers.
