# Round 2 — Insight (Attack/Defend/Re-attack)

**Date:** 2026-07-08

## 2a Attack
Core: "obvious engineering + pprof already does it minus labeling." Cross-layer framing wasn't in the attack because it was new.

## 2b Defense
Added: "Unlike CPU profiling, which aggregates within a single layer, this record connects high-level prompts to the low-level system effects they trigger."

## 2c Re-attack
- Defense partially effective: blocks "just pprof" attack
- New vulnerability: cross-layer connection belongs to AgentSight (prior work), not this paper
- Assessment: solid workshop, not full-paper

## Resolution
- Removed the overclaim sentence (cross-layer as novelty)
- Kept the descriptive "spans both agent intent and system effects" 
- Paper's contribution is the profiling model on top, not the cross-layer bridge
- Novelty level: workshop-appropriate (combination in new domain + evaluation methodology)
