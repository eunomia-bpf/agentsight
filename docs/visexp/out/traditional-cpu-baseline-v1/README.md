# Traditional CPU flame graph baseline (v1)

One conventional CPU profile, rendered by the same paper renderer as every
AgentPProf figure, so the paper can place a traditional program flame graph
beside a semantic operation flame graph without changing anything about how
the two are drawn.

This directory is a figure input. It is not an AgentPProf product output and
does not involve `agentpprof`, agent histories, or any model.

## What was profiled

`workload.go` is a small Go HTTP service: a `net/http` handler that reads a
request body, parses it into records, validates tags, hashes them, ranks them,
and renders a response. Eight client goroutines drive it for 12 seconds while
stock `runtime/pprof` records a CPU profile.

- Go 1.22.2, Linux 6.15.11, 24-core Intel Core Ultra 9 285K
- `go-http-cpu.pb.gz` — the captured profile, 26.86 s of CPU samples

## Reproduction

```bash
go build -o goprof workload.go
./goprof go-http-cpu.pb.gz

python3 docs/visexp/r221_visual_gallery.py \
  --profile go-http-cpu.pb.gz \
  --out go-http-cpu.svg \
  --focus 'handleIngest' \
  --max-depth 12 \
  --title "Traditional CPU profile: a Go HTTP service" \
  --subtitle "stock runtime/pprof; focus main.handleIngest; 26.9 s of CPU samples"
```

The renderer reads the profile through `go tool pprof -traces`, exactly as it
does for AgentPProf profiles. No renderer code path is specific to either kind
of profile.

## Two notes on the rendering

`--max-depth 12` is a display-only truncation added for this figure; the
profile itself is 30 frames deep, and the rendered subtitle states the
truncation. Omitting the flag reproduces the full-depth picture and leaves
every previously committed figure byte-identical.

`--focus handleIngest` selects the request-handling path. Without it the
profile also contains client-side and GC stacks, which are real but not what
the comparison is about.

## One workload detail

The renderer rejects frame names containing `;`, because folded stacks use `;`
as the frame separator. Go generic instantiations such as
`slices.SortFunc[go.shape.struct { encoding/json.v reflect.Value; ... }]`
contain one. The workload therefore encodes its response directly instead of
calling `encoding/json` on a map, which is what pulled in the generic sort.
