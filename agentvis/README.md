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
CLI path through `agentsight vis`.

The AgentSight web UI also has an **Agent Nebula** Node view. Open a live Node
and select **Agent Nebula** beside the machine overview. It reads file audits
from the Node materialized view (`audit_events` with `audit_type=file`), runs the prepared layout in the collector
(`agentvis::build_nebula_document` via `GET /api/v1/nebula`), and only renders
in the browser. Use `agentsight vis` for offline GIF/HTML from native session
logs; use the web Nebula view when inspecting a capture already in AgentSight.

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

## Example

The committed ACTplane example uses the default 30-second action-uniform
compaction: [PNG](https://github.com/eunomia-bpf/agentsight/raw/master/agentvis/examples/actplane-agent-nebula.png),
[GIF](https://github.com/eunomia-bpf/agentsight/raw/master/agentvis/examples/actplane-agent-nebula.gif), and
[MP4](https://github.com/eunomia-bpf/agentsight/raw/master/agentvis/examples/actplane-agent-nebula.mp4).

![Agent Nebula visualizing ACTplane](https://github.com/eunomia-bpf/agentsight/raw/master/agentvis/examples/actplane-agent-nebula.png)
