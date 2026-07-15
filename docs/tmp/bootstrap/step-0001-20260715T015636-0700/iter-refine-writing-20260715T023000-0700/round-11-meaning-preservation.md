# Round 11: Meaning Preservation

Reviewer mode: independent fresh read-only comparison of the user instruction,
initial narrative, entry snapshot, and current paper

## Reviewer Finding

The reviewer found one must-fix meaning loss. The current Git evidence model
retained commits, renames, additions/deletions, and endpoint survival but no
longer explicitly promised file birth and death intervals. The user instruction
and Initial Narrative both require agent-session evidence to be cross-checked
with Git history and file creation/survival history.

No other must-fix loss was found. The current paper retains all seven classic
families and roughly sixteen projections, real multi-day histories, experiments,
the paper deliverable, playback and draggable time navigation, stable layout,
semantic zoom, linked interaction, on-demand detail, reusable libraries and
external tools, and the event--Git--survival cross-check.

## Root Decision And Applied Fix

Restored file birth and death intervals in the formal Git evidence model and in
Joining and Aggregation. The paper now explicitly states that those intervals
feed the evolution matrix, repository-growth playback, and endpoint-survival
projections.

The reviewer classified the following changes as valid scientific
clarifications rather than meaning loss: causal coupling became ordered read-
before-edit evidence; agent authorship became a candidate association; verified
code became a recorded verification action; survival became a current-tree
endpoint; and RQ1 confidence strata gate event-to-outcome claims in RQ2/RQ3.
None removes the requested view or experiment; each prevents the representation
from claiming evidence that the inputs cannot establish.

## Verification

`make -C docs/paper` completed successfully without undefined citations or
references. The current paper differs from the entry snapshot by 473 insertions
and 164 deletions; the final manual contract trace confirms that each requested
artifact and research obligation remains explicit.
