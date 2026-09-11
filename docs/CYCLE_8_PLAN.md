# Cycle 8 — calibrate purchases with reactive continuation

Recorded before implementing or running this diagnostic. The submitted Cycle 3 remains protected. Cycles 6 and 7 showed that a one-purchase forecast can misrank choices and that higher own cash need not improve the match outcome.

Build an offline evaluator that reconstructs a recorded prefix in the pinned interpreter, checking both players' economic observations at every state. At a named observation, replace only our capital orders; retain maintenance, hiring, sales and unit commands. Thereafter both sides use their reactive policies and may invest again. Load the same own continuation policy for every alternative. An unchanged control must reproduce every recorded future action and economic state before interpreting differences.

Use two already inspected seed-17 states, with three continuations each (six total):

| Source in `artifacts/cycle-6-reference-development` | Observation / own seat | Reactive opponent | Alternatives |
| --- | --- | --- | --- |
| `replay-0001.json` | 48 / 0 | Cycle 3 | Original one melon; omit capital this turn only; suppress capital until observation 72, the next shop opening |
| `replay-0013.json` | 409 / 0 | scaled mixed | Original one melon; one wheat instead; omit capital this turn only |

All own continuations use the frozen Cycle 3. The one-turn omission permits investment from the next observation. Waiting for the shop permits investment at observation 72; it does not prescribe a later purchase or use the future shop identity. Both retain feed, fertilizer and hiring during the wait. This tests a specific defer-and-resume policy, not the optimal value of waiting or of information.

Record exact source/replay/engine/runner hashes, interventions and release times, terminal own/rival cash, cash margin and outcome, executed cash flows, physical production, later capital orders, operational losses, and first divergence in shops/actions. Reconcile each continuation's starting cash plus executed sales minus expenses to its ending cash. Reject controls that fail reconstruction, action reproduction or full-season completion; never count errors as wins. Keep full local replays and compact committed evidence.

Compare original and corrected one-purchase forecast rankings at the late state with realized continuation differences. Inspect the early wait comparison for effects of later reinvestment and liquidity. Matched seed does not fix future shops because tile occupancy changes the RNG draws consumed by weed generation. Do not freeze recorded rival actions, insert hidden state into a live policy, or call these six continuations independent games or a release benchmark.

Success for this cycle means a verified reusable evaluator and a concrete, bounded next hypothesis supported by its diagnostics. No live-policy change or new upload is required. No tuning, fresh evaluation seeds, or paid compute; seeds 9401–9420 remain reserved. Use two local CPU processes. Add focused tests for prefix/seat/clock correctness, intervention boundaries, future reactivity and rejected invalid evidence. Save and push implementation, evidence and CO notes.
