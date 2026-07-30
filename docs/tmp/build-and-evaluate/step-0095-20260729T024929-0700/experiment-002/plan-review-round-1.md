# Independent plan review, round 1

Reviewer: `/root/utility_iteration2_plan_review`

Verdict: **AMEND**

The reviewer found the adaptive follow-up scientifically recoverable because
experiment 001 remains a visible negative, all new analyst calls are fresh,
prior outputs are excluded, and no ToolSandbox outcome was observed.

Required amendments:

1. The 1.05 token and 0.90 time thresholds lacked justification independent
   of experiment 001. Delete the argument based on being twenty times the
   observed 0.40%; absent an external criterion, keep the original `K <= 1.00`
   primary rule and make 1.05 sensitivity-only.
2. Specify the bootstrap estimators, whole-block resampling, simultaneous
   bound construction, centering/studentization or alternative exact method,
   quantile/tie rules, and missing/zero usage handling. Freeze literal analysis
   code before calls.
3. Redact timing, usage, schedule, and replicate data from validity review.
   Lock validity decisions before unblinding. Preassign rank 1 per arm as the
   sole downstream policy and stop without substitution if it is invalid.
4. Define downstream agent-token scope, paired estimators, complete-scenario
   cluster resampling, seed, and joint bound algorithm. Limit the claim to a
   held-out consequence of the selected PROFILE policy versus NO-POLICY; do
   not imply superiority over RAW-POLICY without a registered direct contrast.

Disposition: all four amendments were accepted before any experiment-002
model call.
