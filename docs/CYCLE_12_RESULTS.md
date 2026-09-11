# Cycle 12 — executable carrot fertilizer

**Ready for a user-run Kaggle test; server validation is pending.** The user changed the workflow during evaluation: stop local simulations and use Kaggle games as competitive evidence. The reference run was stopped at 148/160 games; no final paired local qualification is claimed. The unchanged challenger is packaged for upload, while submitted Cycle 3 and `main.py` remain protected. [Original frozen plan](CYCLE_12_PLAN.md), [updated active workflow](PERFORMANCE_PLAN.md), [CO/economics and non-crop feature status](CYCLE_12_OPTIMIZATION.md).

Candidate SHA-256: `555c312fc2c09c61c5f0081c4b4148446f5794eddaa1a71427a07b11d4057d34`. The Cycle 11 ablation remains `16bb5ba43889df22d931383f84eb288b12380a66091be086ea3aa4dacf768415`. The incumbent is `47c281bfb4118a9755f1759930b162de007efdfef3b23144457eccbaac42da0c`. Neither policy bytes nor the preregistered plan changed after the development screen began.

## Implementation

The candidate reserves feasible carrot fertilizer bundles for currently available workers, protects urgent animal/crop work, prices buying at the final post-purchase quote and checks the shared input/cash ledger. It can obtain fertilizer from carried stock, shed pickup or a funded purchase available next turn. New carrot investments forecast ordinary yield; an application actually executed in the planning snapshot can justify enhanced yield. Other crop forecasts, opening, actual hiring, land admission and investment ranking remain fixed.

Eleven new interpreter-backed tests exercise complete input-to-harvest sequences, urgent work, purchased input retention, final-day deposit/sale, post-buy prices, competing workers, animal obligations, funding limits and source isolation. The complete suite passes **251 tests**, plus lint and formatting. Two early test fixtures were corrected before freezing: the carrot hinge price is nonlinear, and the first two hires each cost one coin. No strategy parameters were changed from comparative game outcomes.

The previously inspected Cycle 11 observation 481 no longer triggers an eight-unit fertilizer purchase without an executable carrot assignment. Observations 625/627 expose explicit shed-pickup assignments instead of unexecuted scalar targets. These are engineering diagnostics on known states, not fresh game outcomes.

## Development results

Consumed seeds 17/43/9310, both seats and four reactive controls; 24 games for the new challenger. The unchanged Cycle 11 and Cycle 3 grids are reused only after verifying complete pairing, source/engine/runner/lock hashes, configuration, opponents and parallelism. Reuse avoids 48 redundant games; those results do not become fresh evidence.

| Measure | Cycle 12 | Cycle 11 ablation | Cycle 3 incumbent |
| --- | ---: | ---: | ---: |
| Wins / draws / losses | 19 / 2 / 3 | 17 / 2 / 5 | 16 / 4 / 4 |
| Match score, draw = 0.5 | 83.3% | 75.0% | 75.0% |
| Mean own terminal cash | 92,286.7 | 92,046.7 | 91,301.1 |
| Mean cash margin | +8,098.3 | +7,900.0 | +7,158.4 |
| Mean wages | 7,218.7 | 7,173.6 | 7,029.4 |
| Mean peak productive tiles | 35.7 | 35.7 | 35.7 |
| Maximum decision time | 0.602682 s | 0.421652 s | 0.292642 s |

Against Cycle 3 the challenger scores 83.3% versus both controls' 50%. Scores against Step 8, scaled mixed and carrot pressure remain 100%, 66.7% and 83.3%. There is no opponent-stratum regression. Execution, crop-loss, feed, escape, seed-conflict, duplicate-target and terminal-stock checks pass. The development gate therefore advances the frozen candidate to the preregistered fresh evaluation.

Across the development grid, observed successful carrot fertilizer applications rise from **2 to 76**; all 76 precede watering. These counts inspect actual changes to fertilizer expiry, not merely requested actions. The detailed audits below reproduce every economic state and reconcile all eight player cash accounts.

## Largest audited changes versus Cycle 11

**Gain: seed 17, seat 1 versus scaled mixed.** Own cash rises by 3,685, from 86,204 to 89,889; the rival gains 573, so margin increases by 3,112. Both were wins. First differing action follows observation 457: the new ordinary-yield forecast chooses four carrot seeds instead of one fertilized forecast column. Eventually 45 carrot plots produce 171 units, versus 37 plots and 111 units. The 60-unit increase decomposes into 24 ordinary units from eight more plots and 36 successful fertilizer bonuses.

Carrot sales rise by 6,361. Fertilizer sales fall by 3,198 and fertilizer purchases fall by 1,383; wages increase by 555 and carrot seeds cost 160 more. Other product sales also change. Total sales rise by 3,017 and total expenses fall by 668, reconciling the 3,685 cash gain. Physical output, input resale and net cash are reported separately. The entire town-shop sequence is identical in both branches.

**Regression: seed 17, seat 0 versus Step 8.** Own cash falls by 71 and the rival gains 202, reducing margin by 273; both remain wins. The first difference follows observation 529, where the challenger omits a fertilizer purchase while all current workers are committed to livestock. Later, two successful applications raise carrot output from six to eight units. Carrot sales increase by 135, but lost fertilizer and other-product receipts more than offset that gain after the 100-coin reduction in fertilizer purchases. Wages are identical. Town shops are identical throughout. More crop yield is not sufficient evidence of better profit or match margin in the coupled market.

## Fresh evaluation and release decision

Before the user stopped local simulations, the challenger completed 160 games: 118 wins, four draws and 38 losses, or 75.0% match score. Mean own cash was 89,148.6; maximum decision time was 0.831346 seconds. All recorded operational checks and terminal inventory checks passed. Its scores were 67.5% against Cycle 3, 100% against Step 8, 55% against scaled mixed and 77.5% against carrot pressure.

The reference run was interrupted at 148/160 completed games and its worker processes were terminated. That incomplete run is archived as partial evidence, not used to claim a complete paired improvement, confidence interval or passed release gate. Seeds 9401–9420 are consumed evidence. The original preregistration remains unchanged as history; the user's explicit server-first direction supersedes its remaining simulation gate.

The exact frozen file is copied to `artifacts/submission-cycle-12-carrot-inputs/main.py`, with syntax and hash checks only; no additional self-play was run for packaging. Its 160 completed local games and the earlier correctness tests are existing evidence, not Kaggle validation. `main.py`, `baselines/cycle_3.py` and the submitted Cycle 3 artifact stay byte-identical. No new server snapshot or upload was performed. The [archived evidence](benchmarks/cycle-12-inputs.json) includes the interruption and packaging status.

Run the installed CLI, whose positional competition argument was verified with `--help`:

```bash
kaggle competitions submit kaggriculture -f artifacts/submission-cycle-12-carrot-inputs/main.py -m "Cycle 12 - executable carrot fertilizer - 555c312fc2c0"
```

Then review Kaggle's validation and provide the resulting game logs. The next analysis should test whether executed carrot bonuses repay labor and fertilizer opportunity cost under actual opponents, and identify the next farm-wide bottleneck. Goose admission, shared livestock/crop labor, expansion economics and sale/feed timing remain candidate advantages; they are hypotheses to investigate from engine rules and server evidence, not guaranteed winning tricks.

## Reproduction

**Historical protocol only: do not run the simulation commands below without a new explicit user request.** The updated workflow uses server games for competitive evaluation. Building the source with `scripts.make_carrot_input_control` does not simulate games.

Use the locked environment and new output directories. Reproduce the Cycle 11 candidate, pressure control and complete reference grids using [its instructions](CYCLE_11_RESULTS.md#reproduction); they are unchanged controls for this cycle. Restore the committed protocol instead of selecting a new candidate from these results.

```bash
uv run python -m scripts.make_carrot_input_control --output artifacts/cycle-12-input-dev/main.py
uv run python - <<'PY'
import json
from pathlib import Path
recorded = json.loads(Path("docs/benchmarks/cycle-12-inputs.json").read_text())
with Path("artifacts/cycle-12-freeze.json").open("x") as file:
    json.dump(recorded["freeze"], file, indent=2)
PY
uv run python evaluate.py --agent artifacts/cycle-12-input-dev/main.py --opponents baselines/cycle_3.py baselines/step_8.py opponents/scaled_mixed.py artifacts/cycle-11-carrot-pressure/main.py --seeds 17 43 9310 --workers 2 --replays all --output artifacts/cycle-12-input-development
uv run python -m scripts.audit_replay artifacts/cycle-12-input-development/replay-0007.json artifacts/cycle-12-input-development/replay-0014.json --output artifacts/cycle-12-candidate-audit
uv run python -m scripts.audit_replay artifacts/cycle-11-carrot-development/replay-0007.json artifacts/cycle-11-carrot-development/replay-0014.json --output artifacts/cycle-12-ablation-audit
uv run python -m scripts.report_carrot_inputs --output artifacts/cycle-12-reproduced-development.json
```

The freeze preserves the original reference manifest hashes. The reporter verifies them against the committed Cycle 11 evidence and allows a reproduction to have its actual new creation timestamp; every substantive manifest field must still match. `compare_results` separately verifies matching fields and complete game pairing. Do not rewrite the recorded freeze or backdate a new run.

For the fresh phase, run `evaluate.py` separately for the frozen candidate and `baselines/cycle_3.py`, using the same four opponents, all integer seeds 9401 through 9420, both seats, `--workers 4 --replays all`, and output directories `artifacts/cycle-12-input-evaluation` / `artifacts/cycle-12-reference-evaluation`. Then run `uv run python -m scripts.report_carrot_inputs --fresh --output artifacts/cycle-12-reproduced-full.json`. These seeds are consumed evidence, not a new holdout. The committed report contains source/protocol hashes, complete match metrics, comparisons and reconciled development audits; raw replays remain local and ignored by Git.
