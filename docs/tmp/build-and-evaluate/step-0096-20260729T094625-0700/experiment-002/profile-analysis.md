# Independent Profile-Only Analysis

The analyst was allowed to query only `before-profile.pb.gz` with stock pprof
and read the experiment plan. It did not receive raw conversations or outcome
summaries.

Verdict: the priority defect is tool-call ID integrity in the agent
compatibility layer, not a general prohibition on no-progress retries.

Evidence read from the profile:

- 5 of 21 tool operations (23.8%) ended in `invalid-call-id`, across five of
  eight scenarios and five distinct tools.
- Four were followed by the same tool and arguments and then completed; these
  account for all four `exact-repeat` samples.
- The fifth affected `search_holiday` and was not retried.
- The only `other-error` was a send attempt with cellular disabled followed by
  enabling cellular and a successful send, which is useful recovery.

Recommended repair: before official ToolSandbox role parsing, replace an
invalid assistant tool-call ID with a new unique opaque ID accepted by the
interface. Do not change tool name, arguments, order, scenario state, or the
official evaluator.

Expected effects: eliminate invalid-call-ID operations, remove most of the four
recovery repeats, reduce agent calls/turns/tokens, keep similarity unchanged on
already recovered cases, and possibly improve the unrecovered holiday case.
The analyst explicitly judged the profile sufficient to prioritize this test
but insufficient to claim an outcome gain without a paired rerun.
