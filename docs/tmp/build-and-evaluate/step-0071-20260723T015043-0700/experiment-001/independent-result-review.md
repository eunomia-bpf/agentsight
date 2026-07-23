# Independent result review: Experiment 001

Verdict: **PASS**
Role: dependency-only RQ3 compatibility replay

The reviewer independently recomputed:

- 5,537 old names to 1,434 canonical IDs;
- 1,151 first-stage plus eight second-stage source-only refinements;
- 717 initial to zero remaining adjacent display-path collisions;
- all 1,434 emitted names are unique per ID, action-first, and two or three
  words;
- identical 5,752-mark sequence/start/depth skeleton;
- 20,866 independently expanded predictions with the accepted temporal
  occurrence partition exactly equal;
- stock pprof readback with mass 20,866;
- B-cubed P/R/F1 0.839025/0.606577/0.704113 and boundary F1 0.393916;
- identical adjacent-pair rows and 10,000 bootstrap draws, with
  candidate-minus-recurrence interval [0.021367, 0.060596].

No target, outcome, or score-informed name choice was found.
