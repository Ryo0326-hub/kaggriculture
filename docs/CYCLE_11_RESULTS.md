# Cycle 11 — carrot experiment, no promotion

**The challenger is implemented and tested, but not qualified for release.** Its development match score ties Cycle 3 at 75.0% across 24 games per policy. It earns 745.5 more own coins on average, but the draw/win/loss changes cancel in match score. All operational checks pass. The audit identifies an incomplete connection between fertilizer forecasts and actual urgent crop work, documented below rather than treated as successful fertilizer integration.

`main.py`, `baselines/cycle_3.py` and the submitted Cycle 3 artifact remain byte-identical (`47c281bfb411…`). No fresh seeds, isolated release preparation or Kaggle upload; reserved seeds 9401–9420 remain unused. [Plan](CYCLE_11_PLAN.md), [economic/CO notes](CYCLE_11_OPTIMIZATION.md), [evidence](benchmarks/cycle-11-carrots.json), [all 18 unit actions and their purposes](ACTIONS.md).

## Implementation and verification

The candidate adds carrot growth, watering/harvest decisions, fertilizer marginal value, dated production columns and same-turn inventory accounting. New purchases require a visible PET_CAFE or FARMERS_MARKET. Both plain and fertilized batches enter the existing investment comparison; the original opening, other crop rules, hiring and routing algorithms remain unchanged. Ordinary carrot growth yields three units, not the four-unit fertilized maximum. The engine loses one unit every two turns after the crop's lifespan threshold; it does not delete all yield at once.

Candidate SHA-256: `16bb5ba43889df22d931383f84eb288b12380a66091be086ea3aa4dacf768415`.

The related carrot-pressure control grows carrots in every third field and retains the scaled control's other crop mix, animals, staffing and expansion. Its initial seed mix is four melons, six wheat and five carrots, with the same four animals; acquisition costs are 2,280. This is a related supply variant, not an independent reconstruction of a top player. SHA-256: `b923d6cb8ed0db12a7b4849e529586d59524d717e7e2d0468db949feed2700eb`.

Both generated files reproduce exactly. Nineteen new engine-backed cases check yield, fertilizer timing/caps, planting-day survival, gradual decay, terminal salvage, ledger water/harvest/drop/sale behavior, demand gating, source isolation and control execution. The full suite passes **240 tests**, plus lint and formatting. Those checks establish component correctness and recorded runtime behavior; the full-agent fertilizer integration gap remains a separate limitation.

## Complete development results

Consumed seeds 17/43/9310, both seats, four controls, two CPU processes, 48 complete games total. The eighteen common reference games reproduce previous economics and outcomes. Reusing these three seed blocks is not fresh evidence. This pool replaces Cycle 10's wheat-pressure variant with carrot pressure, so its scores should not be directly compared with Cycle 10's differently composed pool.

| Measure | Carrot challenger | Cycle 3 |
| --- | ---: | ---: |
| Wins / draws / losses | 17 / 2 / 5 | 16 / 4 / 4 |
| Match score, draw = 0.5 | 75.0% | 75.0% |
| Mean own terminal cash | 92,046.7 | 91,301.1 |
| Mean cash margin | +7,900.0 | +7,158.4 |
| Mean wages | 7,173.6 | 7,029.4 |
| Mean peak productive tiles | 35.7 | 35.7 |
| Maximum observed decision time | 0.421652 s | 0.292642 s |

Both policies score 50.0% against Cycle 3, 100% against Step 8, 66.7% against scaled mixed and 83.3% against carrot pressure. Two draws become wins in seed 17, while one narrow win becomes a loss in seed 43. The descriptive whole-seed bootstrap interval spans −12.5 to +12.5 percentage points. The preregistered strict improvement gate fails; no post-result tuning or fresh evaluation follows.

All own operational totals are zero: crop loss, unfed animals, escapes, seed overrequests and duplicate crop targets. All terminal shed goods, carried goods and unused seeds are zero. Exact audits of the two preregistered extreme-margin cases reproduce every economic state and reconcile all **eight cash accounts**.

## What changed in actual games

**Largest gain: seed 17, seat 1 versus scaled mixed.** The first changed purchase is observation 409 (day 17, hour 1). With three PET_CAFEs visible, the challenger chooses four carrot seeds instead of four wheat. Forecast marginal values are 512.6 versus 273.6. It eventually grows 37 carrot plots and harvests 111 carrots, selling them for 13,981 at an average 125.95. Own terminal cash rises from 77,898 to 86,204; the rival rises only 161, so margin improves by 8,145. The result was already a win. Both policies reach the same peak footprint of 32 productive tiles. Their entire shop sequences are identical, so this particular gain does not depend on a different town draw.

**Largest regression: seed 43, seat 0 versus Cycle 3.** At observation 553 (day 23, hour 1), the challenger chooses one carrot instead of one wheat, forecasting marginal value 303 versus 260. Over the remaining game it replaces two wheat plantings with two carrot plantings. Six carrots generate 521 sales coins, but wages rise by 89, wheat harvest falls by four and strawberry harvest falls by one. Our cash rises only 21, while the reactive rival gains 194. The original 86,030–86,006 win becomes an 86,051–86,200 loss. Shop sequences are identical here too. This is evidence of coupled prices and policy responses, not proof of a single isolated price-externality mechanism.

## Fertilizer forecast versus execution

The most profitable diagnostic also exposes a fixable gap. All 37 carrot plots produce the ordinary three-unit yield, with **zero carrot fertilizer applications**, although fertilized columns win some forecast comparisons. The inherited urgent watering branch only substitutes fertilizer for strawberries; carrot dry-day and maturity jobs bypass that substitution and the usual fertilizer-loading path. Isolated tests that supply the worker with fertilizer do not establish that the full policy schedules its delivery and application.

The archived source-matched follow-up at observations 481, 482, 625 and 627 records urgent carrot work, carried/shed fertilizer and retained-input targets. At 481, a small positive fertilizer value triggers an eight-unit purchase costing 583. At 482, after the purchase changes the fertilizer quote, the positive target disappears and all eight units are sold for 583. The pair nets zero direct cash and does not fertilize a carrot. Gross sales therefore include some input resale, not just farm production.

These findings do not justify deploying the candidate or claiming fertilized carrot production is complete. Preserve its frozen bytes and report the limitation. The mechanically valid plain-carrot production is useful evidence, but its present planning and delivery policies are not fully consistent.

## Next priority

**Make carrot fertilizer procurement and application executable.** Before crediting four-unit yield, check a funded pickup/application/watering sequence that fits the worker's deadline, including urgent jobs. Use post-purchase input prices when deciding whether to buy, and avoid reserving inputs the policy will immediately sell. When that sequence cannot be executed profitably, value the ordinary three-unit schedule. Keep the existing opening and hiring rules fixed, preserve Cycle 3, and preregister a separate bounded challenger with an unchanged Cycle 11 ablation. Do not revise this failed screen retroactively.

Also retain the seed-43 regression as a later test for opponent-sensitive investment value: more own cash alone does not ensure a better result. Input execution is the immediate concrete issue; adding another crop before resolving it would enlarge the same forecast gap.

## Reproduction

Use the locked environment and new output directories. These documented artifact names are the reporter's defaults. Raw replays remain local and ignored by Git; the committed report carries hashes, decisions and summarized audits.

```bash
uv run python -m scripts.make_carrot_control --output artifacts/cycle-11-carrot-dev/main.py
uv run python -m scripts.make_carrot_control --pressure --output artifacts/cycle-11-carrot-pressure/main.py
uv run python - <<'PY'
import json
from pathlib import Path
recorded = json.loads(Path("docs/benchmarks/cycle-11-carrots.json").read_text())
with Path("artifacts/cycle-11-freeze.json").open("x") as file:
    json.dump(recorded["freeze"], file, indent=2)
PY
uv run python evaluate.py --agent artifacts/cycle-11-carrot-dev/main.py --opponents baselines/cycle_3.py baselines/step_8.py opponents/scaled_mixed.py artifacts/cycle-11-carrot-pressure/main.py --seeds 17 43 9310 --workers 2 --replays all --output artifacts/cycle-11-carrot-development
uv run python evaluate.py --agent baselines/cycle_3.py --opponents baselines/cycle_3.py baselines/step_8.py opponents/scaled_mixed.py artifacts/cycle-11-carrot-pressure/main.py --seeds 17 43 9310 --workers 2 --replays all --output artifacts/cycle-11-reference-development
uv run python -m scripts.audit_replay artifacts/cycle-11-carrot-development/replay-0003.json artifacts/cycle-11-carrot-development/replay-0014.json --output artifacts/cycle-11-candidate-audit
uv run python -m scripts.audit_replay artifacts/cycle-11-reference-development/replay-0003.json artifacts/cycle-11-reference-development/replay-0014.json --output artifacts/cycle-11-reference-audit
uv run python -m scripts.report_carrots --output artifacts/cycle-11-reproduced-report.json
```

Restoring the committed freeze record reproduces the original protocol; it does not select a new candidate. No Kaggle rating or latest-two snapshot was refreshed during this cycle. A source push and local benchmark are separate from a Kaggle upload/server validation.
