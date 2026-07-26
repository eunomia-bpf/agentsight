# Render Report — step-0086 self-profile flame graphs

This run rendered two paper-style flame graphs from the step-0086 self-profile
pprof artifacts into `docs/visexp/out/r221-pprof-renderer-v1/`, reproducing the
visual style of the existing figures in that directory.

## Source profiles

Both inputs live in this directory (`docs/tmp/build-and-evaluate/step-0086-20260725T213500-0700/experiment-001/`):

- `token-width.pb.gz` — pprof sample type `tokens`
- `operation-count.pb.gz` — pprof sample type `operations`

## Renderer

The paper renderer is `docs/visexp/r221_visual_gallery.py` in `--profile` mode.
It extracts folded stacks through `go tool pprof` and renders an SVG flame graph,
matching the R221 pprof-renderer-v1 figures. The `go tool pprof` invocation it
performs internally (for trace extraction) is:

```
go tool pprof -traces -unit=minimum -sample_index=<idx> <profile.pb.gz>
```

The SVG is then rasterized to PNG with ImageMagick `convert` at the density that
yields the directory's canonical 1980-px-wide, 16-bit sRGB style (verified
pixel-identical, AE=0, against the existing `git-multibranch.tokens.png`).

## Commands used

```bash
# 1. Tokens flame graph (SVG intermediate, then PNG)
python3 docs/visexp/r221_visual_gallery.py \
  --profile docs/tmp/build-and-evaluate/step-0086-20260725T213500-0700/experiment-001/token-width.pb.gz \
  --out /tmp/opencode/selfprof/selfprofile.tokens.svg \
  --sample-index tokens

# internal go tool pprof call:
#   go tool pprof -traces -unit=minimum -sample_index=tokens \
#     docs/tmp/build-and-evaluate/step-0086-20260725T213500-0700/experiment-001/token-width.pb.gz

convert -density 144 -background none \
  /tmp/opencode/selfprof/selfprofile.tokens.svg \
  docs/visexp/out/r221-pprof-renderer-v1/selfprofile.tokens.png

# 2. Operations flame graph (SVG intermediate, then PNG)
python3 docs/visexp/r221_visual_gallery.py \
  --profile docs/tmp/build-and-evaluate/step-0086-20260725T213500-0700/experiment-001/operation-count.pb.gz \
  --out /tmp/opencode/selfprof/selfprofile.operations.svg \
  --sample-index operations

# internal go tool pprof call:
#   go tool pprof -traces -unit=minimum -sample_index=operations \
#     docs/tmp/build-and-evaluate/step-0086-20260725T213500-0700/experiment-001/operation-count.pb.gz

convert -density 144 -background none \
  /tmp/opencode/selfprof/selfprofile.operations.svg \
  docs/visexp/out/r221-pprof-renderer-v1/selfprofile.operations.png
```

## Renderer-reported stats

| profile | sample index | pprof samples | rendered weight | stack depth | frames |
| --- | --- | --- | --- | --- | --- |
| `token-width.pb.gz` | tokens | 5,620 | 1,380,863,014 | 6 | 6,730 |
| `operation-count.pb.gz` | operations | 3,509 | 3,509 | 7 | 7,411 |

## Output sizes

Outputs are in `docs/visexp/out/r221-pprof-renderer-v1/`.

| file | dimensions | depth/color | bytes |
| --- | --- | --- | --- |
| `selfprofile.tokens.png` | 1980 x 492 | 16-bit sRGB | 179,544 |
| `selfprofile.operations.png` | 1980 x 532 | 16-bit sRGB | 205,149 |

Both outputs are 1980 px wide, 16-bit sRGB RGBA PNGs, matching the format of the
existing `r221-pprof-renderer-v1` figures (height varies with stack depth, as in
the existing figures whose heights range 532–573 px). The SVG intermediates were
kept under `/tmp/opencode/selfprof/`; no other files in the target directory were
modified.
