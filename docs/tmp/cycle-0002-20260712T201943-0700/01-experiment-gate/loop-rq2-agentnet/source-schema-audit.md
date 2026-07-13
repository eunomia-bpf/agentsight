# AgentNet official source-schema audit

**Observed:** 2026-07-13T03:36:00-07:00  
**Stage:** source preparation before REAL PREFLIGHT  
**Execution status:** `SCHEMA_REPAIR_REQUIRED`  
**Scientific status:** `NOT_EVALUATED`

## Trigger

The first real `prepare` invocation stopped at raw row 13,864 because the
implementation expected one raw JSONL row per task ID. The downloaded file
passed its approved size and SHA-256 checks, so the stop was treated as a
source-schema finding rather than corruption, a negative scientific result, or
permission to discard data.

## Official inputs

- Dataset: `xlangai/AgentNet`
- Revision: `d76ee50a63fad81cfdbe576416757d7c2091ed50`
- `agentnet_win_mac_18k.jsonl`: 1,400,605,632 bytes; SHA-256
  `5c0d782cbf55af02835c3d6d9120072b87c06d24c5a8354c2544bd8d3568e72c`
- `meta_data_merged.jsonl`: 18,840,344 bytes; SHA-256
  `9bb101e8373cd8cd1316f29d53c938b378f96aae1f09776a32bcc27454a0184d`

The official file page independently reports the same trajectory-file size and
SHA-256. The official OpenCUA viewer documentation defines each JSONL line as
one trajectory object. Its loader appends every line to the trajectory table
and performs a direct left merge to metadata on `task_id`; it contains no
deduplication or longest-row selection.

Official references:

- <https://huggingface.co/datasets/xlangai/AgentNet/blob/d76ee50a63fad81cfdbe576416757d7c2091ed50/agentnet_win_mac_18k.jsonl>
- <https://github.com/xlang-ai/OpenCUA/blob/dfc91ba89f700d10f26ec50362d308571482ab8b/data/vis/README.md#data-format>
- <https://github.com/xlang-ai/OpenCUA/blob/dfc91ba89f700d10f26ec50362d308571482ab8b/data/vis/app.py#L61-L96>

## Complete scan

| Property | Observed |
|---|---:|
| Raw JSONL trajectory rows | 17,625 |
| Unique raw task IDs | 17,532 |
| Extra rows from repeated IDs | 93 |
| Task IDs occurring twice | 93 |
| Task IDs occurring more than twice | 0 |
| Byte-identical duplicate rows | 0 |
| Raw rows missing metadata | 0 |
| Unique Windows task IDs | 12,364 |
| Unique Darwin task IDs | 5,168 |
| Repeated Windows task IDs | 63 |
| Repeated Darwin task IDs | 30 |

For all 93 repeated IDs, the later row has more trajectory steps than the
earlier row, but it is not an exact trajectory, action-code, or label prefix.
Ninety-one pairs retain the same `instruction`; two do not. These facts rule
out treating the rows as byte duplication and provide no official basis for
selecting one version.

The metadata scan remains exactly 22,532 unique tasks: 12,364 Windows, 5,168
Darwin, and 5,000 Ubuntu. Every one of the 17,532 Win/Mac raw IDs joins one
metadata row.

## Resolution chosen before scoring

Primary population semantics follow the released trajectory file and official
viewer behavior:

1. Keep all 17,625 released raw trajectory rows.
2. Assign each row a deterministic `trajectory_id` from its zero-based source
   row position and original task ID.
3. Use `trajectory_id` for operation IDs and session groups so two released
   records never collide.
4. Keep the original `task_id` as the dependence unit. Bootstrap resampling
   selects task IDs, so both records of any repeated task are included or
   excluded together.
5. Report trajectory-row, unique-task, duplicate-task, platform, operation,
   and label coverage before REAL PREFLIGHT.

This preserves the full public population without a label-dependent or
length-dependent choice. It adds no model feature, changes no baseline or
metric, and cannot alter the paper thesis, RQs, hypothesis, or story.

## Next action

Revision 4 of the experiment plan records this source semantics. An independent
`research-experiment-design` review must approve the amendment before the
converter is changed and `prepare` is rerun. The current partial projection and
label files are invalid and cannot enter preflight.
