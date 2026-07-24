# agentvis

`agentvis` turns local Claude, Codex, and Gemini Tool actions into standalone
repository-evolution artifacts. It consumes the neutral session model from
`agent-session`; repository scoping, Git milestones, layout, and media export
stay in this crate.

The generated visualization is branded **Agent Nebula**: files are stars,
repository path areas are stable colors, and Agent actions drive the timeline.

```bash
cd your-repository
agentvis
```

The default artifact is `output/agent-nebula.gif`. Use `-o` to choose another
path or to request additional formats:

```bash
agentvis . --global \
  --compact-rate 30s \
  -o output/agent-nebula.html \
  -o output/agent-nebula.png \
  -o output/agent-nebula.gif \
  -o output/agent-nebula.mp4
```

HTML output is a self-contained interactive file. SVG and PNG are still
artifacts; GIF and MP4 replay the same layout frames. AgentSight exposes the
same implementation through `agentsight vis`.

GIF/MP4 default to `--compact-rate 30s`: media frames are selected at uniform
action intervals and encoded at 30 fps. Use `--compact-rate full` to encode
every action frame. HTML always retains every action and ignores media
compaction.

By default, discovery includes every Claude, Codex, and Gemini session whose
cwd, project identity, or Git remote belongs to the worktree. `--global` also
searches sessions rooted elsewhere and retains their absolute-path operations
inside this repository. Each retained Tool action stays on the timeline; an
action with no proven repository file effect produces an unchanged layout
frame instead of disappearing.

## Agent-readable process brief

`diagnose` uses the same native-session discovery and repository projection,
but produces a compact evidence-linked report for another Agent to read:

```bash
agentvis diagnose . -o output/trajectory-brief.md
```

The brief computes inspect–mutate–validate action sequences, pre-mutation
inspection, module migration, artifact revival, repeated changes, validation
lag and carryover, one-touch artifacts, documentation reuse, open and
mutation-closed exploration spans, and explicit Skill-associated session
footprints. These are candidate process signals, not automatic claims
of failure or waste. Every signal includes its interpretation boundary and
native transcript/Tool-call references plus the associated user-prompt
preview when the native record exposes one.

Physical transcript files are not assumed to be independent sessions. Continued
or archived copies of one native root are deduplicated by source-native Tool
call/event identity before any pattern is counted; the Coverage section shows
both the raw parsed-record count and the retained unique Tool-call count.

With `--global`, sessions rooted outside the repository are admitted only when
a native Tool call contains an exact repository path. Their read and mutation
effects are reported as root-external exact-path access. Read-only external
roots stay out of mutation-driven module transitions and pre-mutation inspection;
external roots that mutate the repository remain evolution evidence. Such a
session can be a delegated subagent intentionally working on the repository,
so the report does not call it an independent consumer. A later successful
worktree check is reported as a temporal association, never as proof that it
exercised every pending file. Each report also carries a source-snapshot
fingerprint so live histories from different runs are not silently compared.

Use a `.json` output path when an Agent needs every session and transition row
instead of the compact Markdown tables:

```bash
agentvis diagnose . --global -o output/trajectory-brief.json
```

## Example

The committed ACTplane example uses the default 30-second action-uniform
compaction: [PNG](https://github.com/eunomia-bpf/agentsight/raw/master/agentvis/examples/actplane-agent-nebula.png),
[GIF](https://github.com/eunomia-bpf/agentsight/raw/master/agentvis/examples/actplane-agent-nebula.gif), and
[MP4](https://github.com/eunomia-bpf/agentsight/raw/master/agentvis/examples/actplane-agent-nebula.mp4).

![Agent Nebula visualizing ACTplane](https://github.com/eunomia-bpf/agentsight/raw/master/agentvis/examples/actplane-agent-nebula.png)
