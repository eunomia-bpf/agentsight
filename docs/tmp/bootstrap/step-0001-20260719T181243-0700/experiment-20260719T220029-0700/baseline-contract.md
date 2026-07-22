# OCPM And Full-HTIR Baseline Contract

Status: proposed, frozen for independent plan review.

## Evaluation-Only OCEL Adapter

OCEL 2.0 is evaluation glue, not a shipping IR or production dependency.
`agent-session` remains the native source abstraction.

- event: every source Agent action, including zero-file-effect actions;
- event ID: canonical native action ID;
- event type: normalized source Agent/tool category and name;
- objects: artifact/file, directory/workspace, top-level/child session, goal,
  harness artifact, evaluator/run;
- event-object relations: source/system-backed read, write, create, delete,
  rename, validate, execute-on-path, session membership, goal membership;
- object-object relations: path hierarchy, source-backed rename identity,
  parent session, goal succession, other typed raw relation; and
- attribute history: path, existence, content hash, mode/type at action or exact
  boundary time.

Arbitrary Bash does not become a file effect without raw path evidence. A
directory argument is weak directory access, not a file read. Git is an optional
milestone, never event time, state truth, or goal boundary.

## Frozen OCPM Baseline

Pin `pm4py==2.7.23.3`, `ocpa==1.3.4`, hashed dependency lock, command/config,
and OCEL hash. Before labels, freeze these official feature families:

1. OC-DFG activity/node/edge frequencies, unique-object counts, and performance;
2. per-object lifecycle traces, variants, length distribution, and entropy;
3. object-interaction graph degree, components, and type-pair tables;
4. event/object type counts and duration summaries; and
5. object-centric Petri-net discovery and official replay/conformance outputs.

Families 1--4 and process discovery run on every eligible scientific interval.
Conformance may be `not_applicable` only when no normative constraint exists in
a task/evaluator/skill/harness specification frozen before capture. Human labels
cannot create constraints or select features. Any other execution failure fails
the OCPM obligation and is reported by target, domain, and cluster.

OCPM outputs cite OCEL/raw hashes and are exposed as fixed tables/JSON through
the shared broker. A hand-written count table cannot stand in for OCPM.

## Frozen Full-HTIR Baseline

The field contract and published ladder follow HarnessFix revision
`9167a0b9a58748c73b56c3ee04fdc3437ba0c56e`. Its official benchmark compilers
cannot accept this experiment's frozen Raw interface faithfully: they read
adapter-supplied external paths and evaluator outputs, and some derive effects
from command text. The prospective AgentSight intervals therefore use one
field-by-field fixed reproduction. The official runtime is never selected after
capture; its incompatibility disposition is frozen before registry creation.

The published ladder is mandatory on identical membership:

1. Raw;
2. Raw + data/context-flow;
3. Raw + data/control-flow; and
4. Full HTIR.

Full HTIR requires:

- recoverable model/tool/environment/finalization TraceSteps with request,
  response, role, execution status, and artifact/state effect;
- data/context-flow links with source/target spans and reuse relation;
- control-flow links with source/target, triggering logic, and condition/status;
- effect entity, observed transition (including no-effect/unknown), and support;
- concrete implementation anchors with artifact reference, anchor relation, and
  supporting raw evidence; and
- responsibility-layer mapping when the pinned implementation supplies it.

### Constructor freeze before capture and labels

Full HTIR construction is deterministic and model-free. The constructor model is
`none`, the constructor prompt is the empty byte string
(`sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`),
and temperature/reasoning/output-token parameters are not applicable. The
HarnessFix diagnosis Agent (`openai/gpt-5-mini` in the public artifact) is **not**
an HTIR constructor and is not run here. Downstream diagnosis uses the same
tested supervisor and broker as every other condition.

The upstream source is fixed at revision
`9167a0b9a58748c73b56c3ee04fdc3437ba0c56e`. Audited constructor inputs are:

- `failure_analysis/htir.py`,
  `sha256:cff97f21d89978a5236ee7c8025970ec1ae79ff806af5238940f0b32fdf31d25`;
- `failure_analysis/run_analysis.py`,
  `sha256:bacfac921a6a9b96e6b8526bcbee8978602346f0586dc1faf039eab5d154d9bf`;
- `requirements.txt`,
  `sha256:9dd68f7b89c3cc6bb336d8b94d5dc0391893b20b57406f796e7e4b98b2bd46fc`.

Before registry capture or scientific-label inspection, dependency
implementation must freeze and hash `construct_htir.py`, `htir-map-v1.json`, the
Python 3.11 lock/environment, and the following command template:

```text
python3 construct_htir.py --manifest <run-manifest> --registry <registry.json> --scope full \
  --mode auto --config htir-map-v1.json --output <bundle.json>
```

`--mode auto` is not discretionary and resolves only to the frozen fixed
reproduction. There is no alternate runtime route, target-scope fallback, or
post-capture compatibility choice. The validator accepts only `scope=full`,
recomputes the frozen registry artifact hash, requires exactly one matching
`run_id` row predeclared compatible, binds the row hash into provenance, and
never observes
labels, evaluator success, supervisor output, Trajectory/OCPM output, or
pathology frequency.

The reproduction mapping is frozen now:

| Full-HTIR field | permitted source mapping |
|---|---|
| TraceStep request/response/role/status | complete `native` call and tool-result records sharing source call ID |
| model/tool/environment/finalization type | native role/tool category plus recorded lifecycle kind; unknown remains `unknown` |
| artifact/state effect | matching `system` effect or exact adjacent boundary delta; unsupported remains `unknown`, never inferred from command text alone |
| data/context-flow | explicit source/target call IDs, source/target spans, exact reuse relation, and Raw support IDs only |
| control-flow | explicit source/target call IDs, triggering logic, condition/status, typed relation, and Raw support IDs only |
| implementation anchor | exact `spec` artifact/version/path, source span, implementation identity, anchor relation, bound TraceStep, and Raw support ID |
| responsibility layer | official HarnessFix layer rule applied to that exact anchor; otherwise `unknown` |

No LLM, embedding model, learned classifier, command-text heuristic, or human
judgment fills the mapping. Raw records have a strict family-specific schema,
origin allowlist, full-scope marker, boundary/time, family-consistent canonical
ID, and a hash covering metadata, payload, and relations. The constructor
rejects label, success, condition-output, Trajectory, and OCPM fields. The
constructor parses source/target byte spans, recomputes exact-span/hash reuse,
checks controlled control/effect vocabularies, requires relation support to
include the owner and both call endpoints, and binds each anchor identity to a
matching quiescent snapshot path/content hash and valid byte range. Its four
ladder projections carry identical Raw membership and content hashes for every
included component. The
pre-label compatibility decision is a conjunction of the required source
families in the Label-Independent Compatibility section and these schema
predicates. A registry row declared compatible but missing a required field,
flow, effect, or bound anchor exits nonzero; it cannot be reclassified after
labels. Execution is one process, one CPU, at most 8 GiB RAM and 10 minutes per
interval, with no network access. Timeout, resource overrun, hash mismatch, or a
post-label adapter change is an HTIR failure, not a reason to change the
constructor.

Every present field cites raw native/system/evaluator/spec IDs available to Full Raw.
An unsupported responsibility layer is explicitly `source_unsupported`, never
filled heuristically. The bundle declares the fixed Raw, Raw+data/context,
Raw+data/control, and Full-HTIR component ladder over identical membership.
Human target/prior labels, intervention records, OCPM, and Workspace Trajectory
are forbidden construction inputs. Constructor hashes, selected official
incompatibility disposition, resource use, latency, and failures are reported
for every interval.

## Label-Independent Compatibility

Before capture, a registry row is HTIR-compatible only when it will retain:

- full model/tool/environment/finalization request-response steps;
- corresponding system effects and evaluator records;
- exact harness, skill, prompt, tool-schema, and orchestrator artifacts; and
- implementation identity sufficient for concrete anchors.

Compatibility never references pathology, success, or condition output. The
registry has at least 20 scheduled compatible runs/domain across at least four
clusters. Full HTIR runs on every eligible compatible interval.

## Fidelity And Coverage Gates

For every compatible interval, a field-level report marks each required item
`present`, `source_unsupported`, or `implementation_incompatible`, plus raw IDs.
Ordered actions/file effects alone are not Full HTIR.

The obligation passes only if:

- every emitted item passes raw-byte linkage;
- at least 80% of eligible compatible intervals execute successfully;
- successful Full HTIR covers at least 12 scientific **target intervals** and
  four clusters/domain; and
- among those compatible successful intervals, independent **target-goal** truth
  has at least two positives/domain for `validation_gap` and at least two
  positives/domain for `harness_waste`.

Prior-goal positives never contribute shared-target coverage. Failure of
compatibility supply, execution, fidelity, domain/cluster coverage, or target-
positive coverage fails the baseline obligation and returns the whole plan to
the idea gate. One successful or label-convenient example cannot pass.
