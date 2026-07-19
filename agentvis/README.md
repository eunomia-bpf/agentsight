# agentvis

`agentvis` turns local Claude, Codex, and Gemini Tool actions into standalone
repository-evolution artifacts. It consumes the neutral session model from
`agent-session`; repository scoping, Git milestones, layout, and media export
stay in this crate.

```bash
agentvis . --global \
  --compact-rate 30s \
  -o output/repository-nebula.html \
  -o output/repository-nebula.png \
  -o output/repository-nebula.gif \
  -o output/repository-nebula.mp4
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
