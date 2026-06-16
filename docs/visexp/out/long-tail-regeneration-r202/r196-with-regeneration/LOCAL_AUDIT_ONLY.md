# Local Audit Artifact

This directory is produced by the R202 regeneration smoke as the detailed
R196 governance run with regeneration enabled.

It is not public-safe by default. The CSV/JSON/MD files may contain
profile buckets such as local path components, tool names, process names,
or other machine-specific fingerprints. They do not need raw prompt text
to be useful for local audit, but they must be sanitized or excluded before
a public artifact release.

The public-oriented R202 files are the top-level summary JSON, summary
Markdown, and bounded attempts CSV in the parent directory.
