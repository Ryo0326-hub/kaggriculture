# Kaggriculture

An optimization-based agent for Kaggle's farming simulation, developed in explicit, testable steps.

**Research-led test extension:** [137 additional cases, sources and scenario analysis](docs/RESEARCH_SCENARIO_TESTS.md), written after external research: 132 pass and five expose three additional policy gaps. Together with the [original 245 optimization cases](docs/OPTIMIZATION_TESTS.md), this is 382 cases: 373 pass and nine strict expected failures document seven unresolved gaps. Current policy and submission bytes are unchanged.

**Current work: Fresh Cycle 1**, independently implemented at the user's request without a reference policy. [Release, checks and upload command](docs/FRESH_CYCLE_1_RESULTS.md) · [Economics and CO notes](docs/FRESH_CYCLE_1_OPTIMIZATION.md). Source: `experiments/fresh_cycle1.py`; builder: `scripts/make_fresh_cycle1.py`. Packaged for user-run Kaggle submission, with bounded tests and recorded histories only. Upload and server validation are pending. Historical root `main.py` and all prior releases remain preserved.

**Historical handoff:** [Cycle 22 handoff](docs/HANDOFF_CYCLE_22.md). Its instruction to derive from Cycle 19 is superseded by the user's fresh-Cycle-1 request. The prior release reports below are historical evidence.

**Cycle 21 server regression confirmed; preserve Cycle 19 as the recovery baseline.** Cycle 21 passes validation but two source-matched ladder games lose 57,930–104,432 and 88,858–123,317. Deadline preemption interrupts feasible routes for jobs assigned to other workers; movement, missed animal service and weak strawberry bonus coverage undermine production. All 2,876 own decisions across the supplied validation and these public games match the artifact when policy memory is retained. [Server review and recovery direction](docs/CYCLE_21_SERVER_REVIEW.md) · [Cycle 19 release](docs/CYCLE_19_RESULTS.md). No agent code or artifact changed, and no new upload or local simulation was run during this review. [Historical Cycle 21 release](docs/CYCLE_21_RESULTS.md) · [Implementation notes](docs/CYCLE_21_OPTIMIZATION.md).

**Preserved Cycle 19:** [its reviewed Baen match](docs/SERVER_REVIEW_108335136.md) matches all 719 decisions and ends 92,606–98,585. Routing continuity, animal care and final delivery work; crop deadlines, safe watering skips and opening cash timing remain priorities. Cycle 19 and Cycle 20 source/artifacts are unchanged by this review. [Cycle 19 release](docs/CYCLE_19_RESULTS.md).

**Latest opponent study:** [Majkel versus THIRD FARM CLUB and four-game portfolio comparison](docs/MAJKEL_108290604_STUDY.md). A repeated opening leads to different cow/sheep/goose and crop allocations as the economy changes. Majkel wins 129,821–110,448 through stronger livestock output and economic execution, while the opponent has a better berry-watering calendar. The comparison separates visible-demand adaptation from unproven opponent prediction and identifies the remaining gaps with Cycles 19/20. Review only; both candidates remain unchanged.

**Historical server checkpoint: Cycle 18 — two reviewed losses expose an execution regression.** It enhances Cycle 15 through the shared-route work from Cycle 17, adds route-specific feed/fertilizer credit and next-day fertilizer staging, protects ongoing-crop watering, and reserves carried-stock capacity. The second audit also repairs worker-specific service deadlines, optional step metadata and partial animal deposits. Reviewed artifact: `artifacts/submission-cycle-18-final/main.py`, SHA-256 `65e0e1f6f12e…`. [Upload command and checks](docs/CYCLE_18_RESULTS.md) · [Strategy and CO notes](docs/CYCLE_18_OPTIMIZATION.md).

**Cycle 15 is server validated, but five reviewed losses expose production limits.** Sergey, Julian, Chloe, Ahmed and Soumic show why feasible expansion, input deadlines, market saturation and terminal delivery matter. All own decisions in those reviews match Cycle 15. The latest Soumic game ends 85,532–94,176 despite our 4,209 lead entering the final day. Selected losses and early rating changes do not establish overall ladder strength.

The final Cycle 18 passes 40 bounded tests and 140 isolated recorded-observation checks; the largest sampled callback is 0.414 seconds. [Second audit findings](docs/CYCLE_18_AUDIT.md). Both supplied server games now finish normally and all 1,438 own decisions match this artifact, but both are losses. The [server review](docs/CYCLE_18_SERVER_REVIEW.md) identifies route oscillation, a seed backlog that blocks investment, and full-care forecasts that execution does not deliver. The user reports a 545.3 ladder rating. Cycle 19 now packages an execution-focused replacement for server evaluation. No local matches, training, cloud spending or automatic upload. The complete public V36 remains available unchanged as the separate [Cycle 16 baseline](docs/CYCLE_16_RESULTS.md).

Root `main.py` remains protected Cycle 3. Custom Cycle 15 and all earlier artifacts remain unchanged. The [150K budget](docs/CYCLE_15_SERVER_ANALYSIS.md) is an illustrative favorable-economy target, not a demonstrated result or guaranteed score.

**Cycle 3 fertilizer timing is running on Kaggle as submission 56158876.** Three supplied public games match all 2,157 own decisions: one win and two losses, with clean execution. Read the [server analysis](docs/CYCLE_3_SERVER_ANALYSIS.md). Its earlier fresh local score was 86.7% versus Step 8's 60.8%; local and ladder outcomes are separate evidence. [CO notes](docs/CYCLE_3_OPTIMIZATION.md), [source-matched decision](docs/examples/cycle-3-post-water-fertilizer.json). No new spending on compute.

**Cycle 4 completed without promotion.** The location-aware expansion challenger scored 74.2% versus Cycle 3's 73.3% on its fresh matched pool, with an inconclusive interval and fewer wins against the strongest control. `main.py` remains the exact submitted Cycle 3 file. [Results](docs/CYCLE_4_RESULTS.md) · [CO notes](docs/CYCLE_4_OPTIMIZATION.md).

**Cycle 5 completed without promotion.** The future-demand challenger forecasts investments across eight possible shop sequences. It improved against the strongest local control but tied overall development match score at 66.7%, with lower average cash and regressions against the other controls. Cycle 3 remains the submitted policy; no new upload or fresh evaluation was performed. [Results](docs/CYCLE_5_RESULTS.md) · [Scenario modeling and CO notes](docs/CYCLE_5_OPTIMIZATION.md).

**Cycles 6 and 7 completed without promotion.** Waiting for the next shop with rival supply stress scored 38.9% versus 72.2% for Cycle 3 and lacked runtime headroom. A separate wheat-conservation correction tied at 72.2%, changing only one game's decisions without improving its outcome. No new upload or fresh evaluation was warranted. [Cycle 6 results](docs/CYCLE_6_RESULTS.md) · [Cycle 7 results](docs/CYCLE_7_RESULTS.md) · [CO notes](docs/CYCLE_6_OPTIMIZATION.md).

**Cycle 8 completed the purchase-continuation evaluator.** Six continuations from two inspected states preserve reactive opponents and future reinvestment. Both unchanged controls reproduce the original games exactly. The diagnostic exposes a cash forecast of 155 versus 64 actually available after additional feed and repair labor, making current-day investment obligations the next priority. These are conditional diagnostics, not a new release benchmark; Cycle 3 remains unchanged. [Results](docs/CYCLE_8_RESULTS.md) · [Continuation value and CO notes](docs/CYCLE_8_OPTIMIZATION.md).

**Cycle 9 completed without promotion.** Remaining-day cash admission reduced calibration error but scored 61.1% versus Cycle 3's 72.2%. Smaller crop batches sometimes paid the same extra wages. The newly supplied Ace Team loss is source-matched and operationally clean, but exposes a larger production/worker-efficiency gap. That evidence motivated the bounded wheat-opening experiment below. [Experiment results](docs/CYCLE_9_RESULTS.md) · [Server analysis](docs/CYCLE_9_SERVER_ANALYSIS.md) · [CO notes](docs/CYCLE_9_OPTIMIZATION.md).

**Cycle 10 completed without promotion.** The wheat-inclusive opening generated earlier crop receipts but scored 50.0% versus Cycle 3’s 79.2% across 24 development games each. It increased average wages and reduced average cash. Both exact diagnostic comparisons changed later shops; all eight player accounts reconcile. That evidence motivated the carrot experiment below. [Results](docs/CYCLE_10_RESULTS.md) · [CO notes](docs/CYCLE_10_OPTIMIZATION.md).

**Cycle 11 completed without promotion.** Carrot production after visible shop demand ties Cycle 3 at 75.0% development match score, with 745.5 more average coins. Exact audits expose a fertilizer forecast that urgent carrot work does not execute, making input delivery/application the next priority. Cycle 3 stays unchanged. [Results](docs/CYCLE_11_RESULTS.md) · [CO notes](docs/CYCLE_11_OPTIMIZATION.md) · [All unit actions explained](docs/ACTIONS.md).

**Cycle 12 is packaged for a user-run Kaggle test.** Fertilizer now follows explicit worker/input assignments, and future carrot forecasts no longer assume unassigned fertilizer. Development improved to 83.3% versus 75.0%; the user stopped the final local reference run and chose Kaggle-based evaluation, so no final paired qualification is claimed. Cycle 3 stays protected. [Results and upload command](docs/CYCLE_12_RESULTS.md) · [CO notes](docs/CYCLE_12_OPTIMIZATION.md).

**Current workflow:** strategy and implementation informed by server logs; no local match simulations without an explicit request. Default CI runs static checks, with simulation tests available only by manual opt-in.

Step 8 remains server validated and preserved byte-for-byte in `baselines/step_8.py`; Cycle 3 is preserved in `baselines/cycle_3.py`. The latest-two pair at September 11, 11:28 UTC was Cycle 3 and Step 8; Cycles 5–12 did not refresh that snapshot. The [calibration report](docs/SERVER_AND_BENCHMARK_CALIBRATION.md) separates server evidence from local tests; the [active plan](docs/PERFORMANCE_PLAN.md) replaces the old fixed feature sequence. Cycle 2's [staffing experiments](docs/CYCLE_2_RESULTS.md) were rejected; Cycle 3 retains the old harvest rule after its early-harvest experiment failed to add value.

## Historical local simulation commands — explicit opt-in only

Use the Cycle 19 build/upload instructions above for the current workflow. The following commands include tests and matches that run the simulator; do not launch them without a new explicit request.

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then:

```bash
uv sync --locked
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv run python evaluate.py --seeds 17 43 --opponents baselines/step_8.py opponents/scaled_mixed.py --workers 2 --output artifacts/local-check
```

Python 3.12 and `kaggle-environments==1.32.7` are pinned. `uv.lock` fixes transitive dependencies. The official simulator brings dependencies for other games; the actual submitted `main.py` uses only the standard library and makes no network calls.

The match runner loads the actual Python artifact through Kaggle's agent loader, plays every seed in both player positions, and writes:

- `manifest.json`: agent hashes, environment/version/source hashes, resolved configuration, seeds, runner hash, and process concurrency.
- `matches.csv` / `matches.jsonl`: outcomes, cash, statuses, runtime, and remaining stock. JSONL also includes crop/animal output, hire/seed/animal order costs, feed quantities, idle work, escapes, missed feeding, and resource-conflict diagnostics for both agents. Unplanned crop losses are reported separately from expiration of exhausted ongoing crops with no held output.
- `summary.json`: overall and per-opponent results. Errors are reported separately and are never counted as economic wins.
- `replay-0001.json` / `logs-0001.json`: the first replay and logs. Use `--replays all` to save every game; error games are always saved.

Choose a new output directory for each experiment; existing directories are not overwritten. The built-in `random` agent is deliberately excluded because its own unseeded RNG prevents deterministic comparisons. A file can be passed as an opponent instead. Run only trusted agent files: the simulator executes their Python code.

`--workers N` runs independent games in CPU processes, retaining deterministic result order and saving full replays only when requested or needed for errors. It defaults to one process. Match concurrency between paired runs; observed latency under local load is not a server runtime guarantee.

## What the protected custom Cycle 3 agent does

The planner retains twenty joint openings, then compares no purchase, a cow/sheep, and batches of 1/4/8/12 wheat, melons, or strawberries. A batch can also pay for the next land quadrant. The forecast reprices both visible portfolios, charges dated inputs and Fibonacci wages, preserves a cash buffer, and rejects infeasible route estimates. It compares up to 75 owned tiles and retains ten nearby animal sites.

The dispatcher keeps livestock on bounded shared routes, protects first feeding and newborn watering, and gives released workers nearby crop tasks. Seed placement follows the investment geometry. Small harvest batches share return trips and fertilizer pickups can serve multiple plots. Actual execution can hire a thirteenth total worker for repair; the investment forecast admits at most twelve.

Cycle 3 permits profitable strawberry fertilization after watering, because its bonus is applied overnight. When a worker already carries fertilizer at an urgently dry strawberry, it can fertilize first if both actions fit; a last-hour worker waters instead. Wheat's fertilizer timing remains unchanged because its water bonus is immediate. The investment functions and hiring calculation are unchanged, although improved output can alter later cash and purchases under those rules.

This is an optimization-informed heuristic, not a global farm optimizer or a Nash-equilibrium solver. Crop tours estimate staffing and wages; actual tasks are replanned. Selective maintenance, additional crop species, and advanced sale timing remain future work. Read [Step 8](docs/STEP_8_OPTIMIZATION.md) for assumptions, limits, and CO connections.

Historical agents are preserved byte-for-byte in `baselines/step_1.py` through `baselines/step_8.py`. Steps 2, 3, 5, 6, 7, and 8 have server episodes that reproduce locally. Step 7's [MugaBros loss and Jaikrishna win](docs/STEP_7_SERVER_ANALYSIS.md) also match all 719 of our runtime decisions per episode.

## Historical full-season preparation — explicit opt-in only

The active server-first workflow uses the Cycle 13 builder and upload command above, which do not run matches. The following older command runs local self-play; do not use it without a new request for local simulation.

```bash
uv run python prepare_submission.py --output artifacts/submission-cycle-3
```

This creates `main.py`, `validation.json`, and `validation.log` in a new directory. It checks the **copied file** in full-season self-play using the official loader, in a separate Python process with the repository removed from the import path. The report records its hash, environment, statuses, inventory, and maximum observed decision time. Existing release directories are never overwritten.

**Only the generated `main.py` is the submission artifact.** It needs no supporting repository files. The command does not upload to Kaggle. For future releases, upload that exact file when ready, inspect Kaggle's validation status and logs, and record its submission ID and hash. Local validation cannot certify the server environment or competitive rating. Remember that a new upload changes the latest-two submission window.

Cycle 3's uploaded file is `artifacts/submission-cycle-3-fertilizer/main.py`, SHA-256 prefix `47c281bfb411`. Source control preserves its exact bytes in `baselines/cycle_3.py`; the generator can reproduce it from `experiments/timing.py` using `--mode fertilizer --bake-default`.

## Reproduce and understand Step 8

The [Step 8 results](docs/STEP_8_RESULTS.md) record the frozen protocol, hashes, and local/server status. After the local check above:

```bash
uv run python explain_turn.py \
  --replay artifacts/local-check/replay-0001.json --state 0 --player 0
uv run python scripts/make_expansion_control.py --source baselines/step_8.py --max-land 1 \
  --output artifacts/controls/no-expansion.py
```

The explanation verifies the current source and recorded action before presenting alternatives; `local-check` above uses the current Cycle 3 agent. The explicitly frozen Step 8 ablation keeps its other decisions while disabling land purchases. `opponents/expanding_mixed.py` is an independent reactive four-animal and expanding-crop control; it is not a copy of private leaderboard code. Historical Step 7 bundle controls remain available through `scripts/make_bundle_control.py --source baselines/step_7.py`.

## Historical Step 4 reproduction

```bash
uv run python scripts/make_livestock_control.py --source baselines/step_4.py --animal COW --output artifacts/controls/cows.py
uv run python scripts/make_livestock_control.py --source baselines/step_4.py --animal SHEEP --output artifacts/controls/sheep.py
uv run python scripts/make_livestock_control.py --source baselines/step_4.py --herd-limit 6 --output artifacts/controls/six.py
uv run python scripts/make_economics_control.py --optimistic-prices --output artifacts/controls/crop-no-buffer.py
uv run python evaluate.py --agent baselines/step_4.py --seeds 17 43 83 \
  --opponents baselines/step_3.py artifacts/controls/crop-no-buffer.py \
    artifacts/controls/cows.py artifacts/controls/sheep.py artifacts/controls/six.py \
  --output artifacts/livestock-comparison
```

These controls restrict species or herd size while retaining Step 4 investment and execution logic. The historical economics generator defaults to the frozen Step 3 source. See [the saved Step 4 example](docs/examples/step-4-decision.json) and [Step 4 evidence](docs/STEP_4_RESULTS.md). Earlier experiments remain documented in [Step 2](docs/STEP_2_RESULTS.md) and [Step 3](docs/STEP_3_RESULTS.md).

## Learning and implementation checkpoints

The starting mathematical background is CO250: linear programming, duality, and integer programming. Network flow and graph theory will be introduced as needed.

1. **Foundation — complete:** game model, small exact routing example, feasible baseline, reproducible comparisons.
2. **Worker assignment — complete:** binary assignment model, exact bounded solver, resource checks, matched greedy comparison, and isolated artifact validation.
3. **Production and hiring — complete:** integer lot/workforce enumeration, cash and estimated labor constraints, price-impact valuation, supply stress case, and finite-horizon crop value. Land was outside that checkpoint.
4. **Competition and capital economics — complete:** audit actual ladder losses, introduce livestock and fertilizer revenue with a liquidity constraint, broaden the pool, and compare against Step 3 on matched fresh games.
5. **Shared livestock routes — complete:** exact bounded route cover, production-day delivery protection, controlled wage/output comparison, paired fresh-seed evaluation, and isolated artifact validation.
6. **Mixed production — server validated:** bounded wheat/melon/strawberry allocation, dated wages, fertilizer/feed opportunity costs, crop deadlines, shared resources, and fresh-seed evaluation.
7. **Joint opening and production bundles — server confirmed:** twenty opening portfolios, dated base/fertilized crop templates, conditional crop sequences, shared cash/inventory accounting, and complete installation service. Independent early/delayed crop controls broaden supply timing.
8. **Conditional expansion — server validated:** fund additional land and crop batches with dated cash and spatial work estimates; preserve shared routes, delivery checks, and installation feeding. Add an expanding mixed opponent and a source-matched no-land ablation.

The remaining work is organized by evidence: server/benchmark calibration (implemented), staffing experiments (rejected), fertilizer/harvest timing (fertilizer-only locally qualified), then server validation and actual ladder evidence. See the [active plan](docs/PERFORMANCE_PLAN.md); the original numbered roadmap is historical.

See [the CO250-to-implementation explanation](docs/OPTIMIZATION.md), [engine findings](docs/MECHANICS.md), [Step 1 evidence](docs/STEP_1_RESULTS.md), and [the competition plan](COMPETITION_PLAN.md).

## Files

| File | Role |
| --- | --- |
| `main.py` | Protected historical Cycle 3; use the Cycle 18 artifact path above for the new submission |
| `experiments/production.py` | Cycle 18 deadline inputs, shared dispatch and equivalent faster route costs |
| `scripts/make_production_agent.py` | Reproducible standalone Cycle 18 builder with frozen-parent hash checks |
| `scripts/check_production_agent.py` | Independent recorded-observation checks without running games |
| `baselines/` | Frozen Steps 1–8; Steps 2, 3, 5, 6, 7, and 8 have server evidence |
| `evaluate.py` | Official-simulator matches, provenance, and result files |
| `compare_results.py` | Matched common-pool scores and whole-seed bootstrap intervals |
| `scripts/replay_timing.py` | Crop-age, planting-date, and sale-timing evidence from reconciled replay audits |
| `prepare_submission.py` | Copy and validate an isolated, self-contained release |
| `explain_turn.py` | Reconstruct and explain a decision from a matching replay |
| `scripts/make_greedy_ablation.py` | Generate the controlled greedy comparison |
| `scripts/make_economics_control.py` | Generate matched staffing, crop, and forecast controls |
| `scripts/make_livestock_control.py` | Generate matched species and herd-size controls |
| `scripts/make_mixed_control.py` | Generate historical Step 6 crop controls |
| `scripts/make_bundle_control.py` | Generate Step 7 opening, fertilizer, and crop-area ablations |
| `opponents/scaled_mixed.py` | Reactive larger-farm stress control; same lineage as expanding_mixed |
| `scripts/benchmark_profiles.py` | Reconciled production, resale and overnight-work profiles |
| `scripts/benchmark_staffing.py` | Controlled installed portfolios and executed cash/output accounts |
| `scripts/make_staffing_control.py` | Reproduce the six rejected Cycle 2 challengers |
| `scripts/report_staffing.py` | Validate and archive the complete staffing development screen |
| `experiments/staffing*.py` | Frozen experimental policy sources; not the submission |
| `scripts/benchmark_timing.py` | Controlled fertilizer/harvest timing and dated executed accounts |
| `scripts/make_timing_control.py` | Generate timing ablations and the qualified fertilizer-only artifact |
| `scripts/report_timing.py` | Archive complete development games and verify the frozen comparison protocol |
| `experiments/timing.py` | Reproducible timing source with experiment flags disabled by default |
| `opponents/expanding_mixed.py` | Independent expanding farm control with shared-source dairy variant |
| `scripts/make_expansion_control.py` | Source-matched land-limit ablation |
| `opponents/early_crops.py` | Independent twelve-melon opening and crop rotation control |
| `scripts/make_early_control.py` | Freeze early/delayed sale controls |
| `tests/test_expansion.py` | Land geometry, cash timing, routes, installation feed, and independent expanding supply |
| `tests/test_bundles.py` | Dated inputs, working capital, opening execution, and installation regression |
| `scripts/audit_replay.py` | Resimulate supplied episodes and reconcile executed transactions |
| `tests/test_mixed_production.py` | Crop growth, opportunity costs, deadlines, staffing, and full-season resources |
| `scripts/benchmark_routes.py` | Controlled installed-herd scheduling and actual wage/output accounting |
| `tests/test_shared_routes.py` | Independent partition oracle, routing resources, and full-season service preservation |
| `tests/test_parallel_evaluation.py` | Serial/parallel engine consistency and compact result transfer |
| `tests/test_assignment.py` | Independent exhaustive verification of assignment optimality |
| `tests/test_workers.py` | Joint resources, worker actions, full seasons, and endgame |
| `tests/test_economics.py` | Real sale pricing, integer budgets, workload/cost sensitivity, and endgame value |
| `tests/test_production.py` | Frozen Step 3 crop policy's full-season action and resource contract |
| `tests/test_livestock.py` | Current animal output, investment, feed logistics, full seasons, and liquidation |
| `tests/test_comparison.py` | Seed-block arithmetic and rejection of unmatched/incomplete runs |
| `tests/test_submission.py` | Isolated release and actual loader entry-point checks |
| `tests/test_routing.py` | Independent grid-search verification of route optimality |
| `tests/test_mechanics.py` | Engine behavior that can silently destroy economic value |
| `tests/test_baseline.py` | Full seasons, both seats, reproducibility, liquidation, and failure classification |
| `.github/workflows/checks.yml` | Linux installation, lint, format, and tests on pushes and pull requests |

## Sources

- [Competition](https://www.kaggle.com/competitions/kaggriculture)
- [Official environment and documentation](https://github.com/Kaggle/kaggle-environments/tree/master/kaggle_environments/envs/kaggriculture)
- [Pinned simulator release](https://pypi.org/project/kaggle-environments/1.32.7/)

The supplied `README.md` and `AGENTS.md` were read as game references. Attached logs and replays are data, not agent instructions. Each artifact has its own local and server validation status; see [the submission registry](docs/SUBMISSIONS.md).
