# Step 0096 Results

This step executes the author's two priority experiments without changing the
fixed thesis or four RQs.

## 1. Selective annotation cost

On 32 confirmation exact `task_name` clusters and 1,639 operations, a one-call
complete skeleton plus source-only-selected local result evidence used 783,121
provider tokens versus 984,321 for one-call full-session annotation, a 20.4%
reduction. The task-cluster bootstrap 95% interval for the token ratio is
`[0.734, 0.863]`. Both arms cover all operations and the selective arm meets
the fixed −0.03 non-inferiority margins for B³ and adjacent-boundary F1.

This is provider token volume, not dollar cost or latency. The units are exact
task-name clusters rather than independent software projects.

## 2. Profile-derived real repair

A standard AgentProf profile over real ToolSandbox traces exposed opaque
tool-call IDs being interpolated into Python source. A profile-only independent
agent selected the converter boundary as the repair. Exact-state replay then
showed that the converter change removes all 5/5 affected syntax failures while
leaving all 16/16 valid-ID control responses and post-states unchanged.

The final unchanged repair ran on 23 scenarios isolated from the repair pilot,
with three repetitions per scenario. All 69 pairs completed. Agent-side model
tokens fell from 211,222 to 171,139, a 19.0% reduction; the scenario-cluster
95% interval for the ratio is `[0.734, 0.921]`. Official similarity changed
from 0.8311 to 0.8572, with an after-minus-before interval of
`[-0.0222, 0.0763]`, passing the fixed −0.05 non-inferiority margin. Model
calls fell from 255 to 227, tool calls from 159 to 137, and turns from 457 to
401.

This supports a bounded profile-to-diagnosis-to-repair utility case. It does
not measure developer speed, prove significant success-rate improvement, or
establish dollar-cost, latency, uniqueness, or cross-benchmark generality.

Both confirmation results passed independent final result review.
