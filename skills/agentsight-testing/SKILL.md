---
name: agentsight-testing
description: Validate AgentSight changes before PR completion. Use when Codex changes AgentSight capture, parsing, top/TUI, web UI, reporting, agent-native session handling, CI scripts, or release-sensitive behavior and must run automated tests plus real CLI/TUI/UI/agent smoke checks.
---

# AgentSight Testing

## Goal

Prove that an AgentSight change works at the product boundary, not only at the
unit-test boundary. Prefer real binaries, real commands, and saved evidence.
Mocks are allowed only for narrow regression tests; they do not replace real
agent validation when the relevant CLI is installed and authenticated.

CI can supplement this proof, but it does not replace direct observation. The
agent doing the change must inspect the TUI/UI/CLI output or saved artifacts
itself and report what was observed. Do not defer missing observation to "the
next PR" or say CI should cover it unless the user explicitly narrows the task
to CI work.

## Validation Ladder

Run the narrowest relevant check first, then widen until the changed behavior
has been exercised end to end.

1. Unit/regression tests:
   - `cargo test --manifest-path collector/Cargo.toml <test_name> -- --nocapture`
   - `cargo test --manifest-path ext/session/Cargo.toml <test_name> -- --nocapture`
2. Component suites:
   - `cargo test --manifest-path collector/Cargo.toml`
   - `cargo test --manifest-path ext/session/Cargo.toml`
   - `cd frontend && npm run lint && npm run build`
3. CLI command smoke:
   - `collector/target/debug/agentsight top --plain --once`
   - `collector/target/debug/agentsight report list`
   - `collector/target/debug/agentsight report summary`
   - `collector/target/debug/agentsight report token`
   - `collector/target/debug/agentsight stat -- <short command>` when the change affects stat/record paths
4. TUI smoke:
   - Run `agentsight top` in a real terminal or PTY.
   - Capture the screen text or screenshot artifact. Prefer terminal buffer
     capture such as `tmux capture-pane`, `script` output that includes the
     rendered screen, or a real screenshot; raw alt-screen escape logs without
     readable fields are not sufficient.
   - Verify key fields by screen buffer/text, not OCR: session id, agent, state, tokens, last message, model, evidence.
5. Web UI smoke:
   - Start a command that serves the web UI (`record`, `stat`, or the relevant server mode).
   - Open the URL in a browser or Playwright.
   - Verify the page loads real session/event data and save a screenshot artifact.
   - The screenshot/artifact must show the relevant feature state, not only that
     a page rendered or that some JSON endpoint returned data.
6. Real supported-agent smoke:
   - Check installed/authenticated CLIs with `command -v`.
   - Native session agents: `claude`, `codex`, `gemini`.
   - Live/record targets from README support: Claude Code, Codex, Gemini CLI, OpenCode, OpenClaw/Node/OpenAI-compatible clients, and any command path touched by the change.
   - For each available CLI, run a short non-destructive prompt under AgentSight and verify the expected rows/events. Do not count a mock agent as satisfying this step.
   - Seeing generic captured data is not enough. Verify the product-level fields
     affected by the change, such as prompt text, response/last message, token
     counts, model, session binding, tool calls, evidence, and report/top rows.

## Real Agent Rules

- Use short prompts that do not modify the repository unless the test is
  specifically about file effects. Prefer "print a short JSON object" or
  "answer with one word" prompts.
- Record the exact command, agent version when available, exit status, DB path
  or output artifact, and the AgentSight command used to inspect it.
- If a CLI is not installed, not authenticated, rate-limited, or requires
  unavailable credentials, report it as a blocker or explicit unverified gap.
  Do not silently skip it.
- If one supported agent fails and the failure is in AgentSight, fix it before
  completing the PR. If the failure is external, capture enough evidence to
  distinguish external failure from AgentSight failure.

## Evidence Contract

Before saying a PR is done, provide:

- Commands run and pass/fail status.
- TUI screen text or screenshot path, plus the specific fields observed.
- Web UI screenshot path or Playwright artifact path, plus the specific UI state observed.
- Real agent matrix: agent, installed/authenticated status, AgentSight command,
  observed output, DB/artifact path when available, inspection command, fields
  verified, and result.
- CI links after push.
- Copilot review/comment/thread status for the final pushed head.

## Guardrails

- Do not relax CI to make validation pass.
- Do not replace a required real-agent test with a fixture unless the real CLI
  is unavailable and that gap is reported.
- Keep generated DBs, screenshots, logs, and temporary homes out of commits
  unless they are intentional fixtures.
- Avoid exposing prompts, auth headers, private paths, or response bodies in PR
  comments; summarize sensitive evidence.
