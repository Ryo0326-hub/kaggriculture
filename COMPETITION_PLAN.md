# Kaggriculture: two-person medal plan

Prepared September 9, 2026, revised September 10 after the Otter Vibe and SpaTaro replay analysis. **The current strategy and calendar are in [Revised competitive strategy](docs/REVISED_STRATEGY.md).** That document supersedes the original staffing assumptions, experimental priorities, and calendar below. Ryo leads development with approximately three hours per day; teammate help is optional to the critical path. Plan around 60 focused hours through September 29, plus September 30 as a buffer. Ryo has $48.39 in AMD Developer Cloud credit expiring today and an account ready for droplet creation; no droplet is assumed active, and expiry timezone is unconfirmed. The sustained plan assumes the existing Mac and no out-of-pocket cloud spending.

The project has frozen crop baselines, coordinated operations, economic models, a livestock investment policy, evaluation, and isolated submission preparation; see [the status](README.md), [CO connections](docs/OPTIMIZATION.md), and [livestock capital notes](docs/STEP_4_OPTIMIZATION.md). Steps 2 and 3 passed server validation. The September 10 CLI check still lists only those two submissions. [Step 5 shared-worker scheduling](docs/STEP_5_RESULTS.md) is now locally validated with a prepared release; its controlled herd experiment preserves output while reducing wages. The next implementation is mixed crops and fertilizer/feed economics, followed by opponent-aware production and delivery. Preserve evaluation and release work if the schedule tightens.

**Recommendation.** Build a reliable deterministic policy with an explicit economic model, coordinated worker scheduling, and automated parameter experiments. Add short-horizon planning only after the baseline is competitive. Use AI assistants during development for engine review, implementation, and replay analysis; keep the submitted policy self-contained.

The official timeline gives September 23 as the entry/team-merger deadline and September 30 as the final submission deadline, both at 23:59 UTC (19:59 Toronto time). Post-deadline games continue approximately October 1–15. Confirm the two-person team is registered well before September 23. Source: [competition timeline](https://www.kaggle.com/competitions/kaggriculture/overview).

**Define the target.** Kaggle's published thresholds for competitions with at least 1,000 teams are top 10% for bronze, top 5% for silver, and top 10 plus one additional gold place per 500 teams. The final eligible field determines the actual cutoffs. Use top 5% as the working target to create room above the bronze boundary; this is a planning target, not a forecast. Source: [competition medal criteria](https://www.kaggle.com/progression/competitions).

**Divide ownership by interface.**

| Responsibility | Teammate A: agent and operations | Teammate B: economics and evaluation |
| --- | --- | --- |
| First deliverable | Valid agent, coordinated worker actions, replayable baseline | Reproducible full-season tournament runner and mechanics notes |
| Main ownership | Observation parsing, task scheduling, routes, inventory, action validation, packaging | Market valuation, investment rules, experiment design, opponent pool, reports |
| Shared contract | Executes prioritized tasks within resource and time constraints | Supplies production targets, spending limits, and sale quantities |
| Daily review | Explain operational losses and integration changes | Explain experiment results and recommend one next hypothesis |

Agree on a small Python interface on day one. Keep one working agent in the main branch. Make each experiment a separate commit/configuration, integrate daily, and assign one person as submission coordinator. Avoid two independently evolving full agents until the common baseline is stable.

**Build the agent in this order.**

1. Parse the observation into cash, units, tiles, private stock, market inventory, active shops, and remaining time.
2. Generate feasible maintenance, harvest, transport, production, and sale tasks.
3. Rank tasks by urgency and expected contribution to terminal bank balance, accounting for travel and prerequisite actions.
4. Assign tasks to workers, reserving tiles, seeds, feed, fertilizer, stock, and cash so simultaneous commands do not overcommit resources.
5. Produce the farmer/hand commands and ordered market queue; validate before returning them.
6. Reconcile against the next observation and repair failed or stale plans.

Step 2 uses a small exact assignment solver and a matched greedy control, with the initial quadrant as its bounded work area. Longer routes and stable worker zones remain experiments. Test predictable route templates against fully dynamic assignment; combine stable routes with local repair if that improves results. Monitor workers switching targets without completing work. A full general-purpose optimization framework is unnecessary for the first release.

The published environment specifies `actTimeout = 1`. Measure p99 and worst-case decision latency with comfortable headroom, and verify the configuration used by the competition. No external information may enter or leave a submission during an episode. Sources: [environment specification](https://github.com/Kaggle/kaggle-environments/blob/master/kaggle_environments/envs/kaggriculture/kaggriculture.json), [competition rules, section 2.12](https://www.kaggle.com/competitions/kaggriculture/rules).

**Audit the mechanics before tuning strategy.**

Read the official engine, specification, and documentation together. Pin the environment version and record its source hash. Compare local behavior with server replays after the first submission; a newer GitHub version is not proof of the version deployed on Kaggle.

Write small scenario tests for these economically consequential behaviors:

- A freshly planted crop must be watered that day.
- Excess simultaneous planting requests can cancel all planting of that crop.
- Feed and fertilizer must be in the acting worker's inventory.
- Worker actions occur before market actions; newly purchased supplies and newly hired workers are therefore not generally usable in that turn's worker phase.
- End-of-day inventory transfer can overflow the shed.
- Harvested goods only contribute to score once sold.
- Determine the last actionable observation and verify harvest → transport/drop → sale against actual termination. The current engine checks `step >= episodeSteps - 2`; do not assume an extra final-day deposit and sale opportunity.

These are tests of engine behavior and resource flow, not assertions that the first strategy is competitive. Sources: [official engine](https://github.com/Kaggle/kaggle-environments/blob/master/kaggle_environments/envs/kaggriculture/kaggriculture.py), [official game documentation](https://github.com/Kaggle/kaggle-environments/blob/master/kaggle_environments/envs/kaggriculture/README.md).

**Use an economic model that accounts for time and market impact.**

For each proposed investment, compare expected additional cash banked before termination with all additional costs: purchase, feed, hired labor, displaced work, and expected inventory losses. Model when revenue arrives so the farm can still fund maintenance before its first harvest. Land has value only when the added production can be staffed, sold, and paid back in time.

Use marginal decisions: hire another worker only if the work that worker can actually finish is worth more than the hire price. Include movement, pickups, drops, and the hours remaining after hiring. Hiring costs reset daily and grow with the Fibonacci sequence, so a productive farm can still lose money by retaining too many hands. Source: [hiring rules](https://github.com/Kaggle/kaggle-environments/blob/master/kaggle_environments/envs/kaggriculture/README.md#hiring).

Value sale batches through the actual price curve. Multiplying today's quoted price by the entire batch overvalues sales that move the market. Include the opponent's likely production and the demand of observed shop instances. Future shop unlocks should remain uncertain rather than being treated as known from an evaluation seed.

Premium products can collapse to the price floor under oversupply; current town demand and rival production matter more than their advertised base prices. Test immediate sales, demand-timed sales, and bounded inventory retention. Splitting a sale into smaller orders alone does not remove market impact; any benefit must come from changed timing or intervening demand. Source: [market mechanics and price curves](https://github.com/Kaggle/kaggle-environments/blob/master/kaggle_environments/envs/kaggriculture/README.md#market-mechanics).

Treat the following as hypotheses to evaluate, not a predetermined optimal farm:

| Priority | Experiment | What to measure |
| --- | --- | --- |
| 1 | Wheat/carrot opening with a few cheap workers | Time to first cash, wasted movement, liquidity, baseline win rate |
| 2 | Small livestock allocation | Complete setup/feed/care/collection cost and terminal cash improvement |
| 3 | Fertilizer collection and sale versus application | Marginal sale proceeds versus additional crop proceeds, including worker time |
| 4 | Bounded premium crops and mixed production | Price impact, opponent overlap, cash tied up, shed pressure |
| 5 | Land expansion and daily workforce sizing | Incremental net profit and maintenance coverage |
| 6 | Shop- and opponent-aware adjustment | Held-out wins across different demand and rival regimes |
| 7 | Endgame investment cutoffs and liquidation | Cash captured before termination and unrecoverable spending |

Fertilizer deserves its own experiment because it can be sold as well as applied. Do not assign it zero opportunity cost merely because an animal produced it. Source: [official agent guide](https://github.com/Kaggle/kaggle-environments/blob/master/kaggle_environments/envs/kaggriculture/AGENTS.md) and [game market rules](https://github.com/Kaggle/kaggle-environments/blob/master/kaggle_environments/envs/kaggriculture/README.md#buying-inventory-from-the-market).

**Make evaluation the main development loop.**

Use the official simulator as the scoring authority. Initially use local CPU processes to run independent games; measure episodes per minute before considering more compute. Store results in CSV/JSON and save diagnostic replays. A custom dashboard or GPU training system is not a prerequisite.

Maintain an opponent pool containing the built-in starter, the current champion, earlier agents, and several deliberately different competent strategies: crop-heavy, livestock-heavy, premium-product oversupplier, and conservative operator. Add suitably licensed public executable agents where available. Build counter-strategies from public replay observations, but do not treat replayed fixed action sequences as equivalent to a rival that reacts to changed markets.

For each candidate:

1. Run roughly 20–40 complete smoke-test episodes, including self-play and both player seats.
2. Screen its single intended change against the champion and a varied opponent pool on development seeds.
3. For promising candidates, run 50–100 fresh seeds per opponent in both seats. Four opponents means 400–800 games. Scale this after measuring throughput.
4. Report win/draw/loss by opponent, overall pool-weighted match score, final cash margin, lower-tail outcomes, runtime, errors, and unintended no-ops. Use cash margin to diagnose and screen; select on evidence relevant to winning matches.
5. Compare candidate and champion against the same pool/seeds. Estimate uncertainty in their difference by resampling whole seed blocks, preserving paired seats and opponents.
6. Promote only when the improvement is credible and no major opponent class regresses materially. If the result is inconclusive, keep the champion or run a larger preplanned test.

Keep development and validation seeds separate. Reserve one untouched set for final selection. Repeatedly adjusting a policy after looking at a holdout turns it into development data. Avoid counting repeated deterministic reruns as additional evidence.

Review losses with a short operational report: first cash divergence, worker cost by day, travel/idle/no-op share, missed maintenance, produce decay, shed overflow, sales near the price floor, and cash spent too late to recover. Each experiment should state one hypothesis, its code/config hash, seeds, environment version, outcome, and decision.

**Use learning only where it earns its complexity.**

After the core policy is stable, run small parameter searches over workforce caps, reserves, production mix, investment cutoffs, and sale thresholds. Start with random or coordinate search; expand only if needed.

If a specific decision remains costly, try short-horizon planning over a small set of high-level alternatives such as holding versus selling a batch or hiring one more hand. Simulate plausible rival actions and demand scenarios; execute the first decision and replan. Account for consequences beyond the short horizon so long-growth crops are not systematically undervalued.

A small learned value function or strategy selector is an optional final experiment. Gate it on a demonstrated held-out gain. With three weeks, end-to-end reinforcement learning has significant implementation, reward-design, and validation costs; it should not consume the baseline schedule. An LLM generating every in-game action is likewise outside the recommended approach.

**Calendar and completion gates.**

| Dates | Teammate A | Teammate B | Gate |
| --- | --- | --- | --- |
| Sep 9–10 | Agent entry point; minimal crop loop; packaging | Environment pin; mechanics probes; seeded runner | Reproducible full games, valid self-play, replay output |
| Sep 11–13 | Worker assignment; resource reservations; maintenance and liquidation | Opening economics; opponent pool; loss report | Reliable baseline; first valid ladder submission; clear advantage over starter |
| Sep 14–18 | Livestock/logistics and route improvements | Crop/animal/fertilizer experiments; hiring/land tuning | First statistically supported improvement over the internal champion |
| Sep 19–23 | Demand-aware and rival-aware policy integration | Fresh-seed league; public replay analysis; parameter tuning | Broad improvement across opponents; official team confirmed by Sep 23 |
| Sep 24–27 | Reliability and endgame fixes | Finalists, ablations, untouched evaluation set | Release candidates pass full-season, runtime, and packaging checks |
| Sep 28–29 | Rebuild exact artifacts and validate server episodes | Review live evidence and final local results | Both intended final bots occupy the latest two eligible submission positions |
| Sep 30 | Buffer for verified defects or platform issues | Confirm final statuses and archive evidence | No speculative last-minute policy changes |

If behind schedule on September 18, stop adding subsystems. Improve scheduling, economy, and endgame behavior in the strongest existing agent. If already comfortably above the medal boundary, reduce experimentation risk and focus on the failure modes that can erase that margin.

**Manage the submission ladder deliberately.**

The evaluation page says five submissions per team per day and uses the latest two for final evaluation. Maintain a local champion/challenger registry with artifact hashes, submission IDs, status, and episode results. Each new upload shifts that latest-two window; it can displace the champion. Do not assume an older high-rated bot remains protected. Source: [competition evaluation](https://www.kaggle.com/competitions/kaggriculture/overview#evaluation).

Prefer one meaningful daily candidate over spending all five slots on untested changes. Preserve capacity for a corrected package or restoring a known-good agent. Read server logs and complete episodes after validation. A validation pass establishes execution reliability in that episode, not competitive strength. Avoid reacting to a few ladder wins or losses against differently rated opponents.

Choose the final two on broad performance and reliability. Distinct strategies are useful only if both are strong independently; they are not an ensemble whose scores combine. Rebuild and test the exact uploaded files, then ensure both intended bots are the latest two eligible submissions before the deadline.

**Working files and the next implementation checkpoint.**

- `main.py`: submission entry point and assembled policy.
- The active livestock investment model and station execution live inside `main.py`; packaging remains self-contained.
- Frozen crop agents and their assignment/production models remain in `baselines/`.
- `evaluate.py`: full-season matches, reproducible seeds, and result collection.
- `tests/`: mechanics, terminal liquidation, and submission-contract scenarios.
- `prepare_submission.py`: isolated full-season validation of the exact copied artifact.
- `explain_turn.py`: decisions reconstructed from a source-matched replay.
- `docs/benchmarks/`: committed hypotheses, hashes, metrics, and promotion evidence.
- `artifacts/`: local releases, replays, and diagnostic logs, excluded from source control.

Step 3 implemented the small production/workforce model, marginal hiring comparisons, cash and estimated labor constraints, and an isolated release gate. Its [results](docs/STEP_3_RESULTS.md) show improvement over Step 2 and a forecast weakness: the control without a supply buffer beats it head-to-head on most fresh seeds. The buffer is not established as a competitive improvement.

Step 4 audited two actual ladder losses: Step 3 earned roughly 21–22 thousand coins while livestock/premium-crop rivals earned 92–123 thousand. That evidence changed the immediate priority from tuning the crop buffer to modeling productive assets. The resulting cow/sheep policy includes fertilizer receipts, feed and wage costs, market impact on existing production, a liquidity gate, and executable station routes. The no-buffer crop policy remains in the broader pool; [Step 4 results](docs/STEP_4_RESULTS.md) compare the candidate and frozen Step 3 on matched fresh games.

Step 5 should improve labor utilization and mixed production. Test shared-worker routes against the current one-worker-per-animal policy, then evaluate productive use of remaining plots. Add land only when incremental receipts cover purchase, setup, operating, logistics, and displaced-work costs before termination. Preserve both server-validated artifacts, write CO explanations, and use new validation seeds. The internal pool still does not include the actual reactive code of the stronger ladder rivals, and local results do not establish medal strength.

Keep competition collaboration within the registered team, preserve third-party license attribution, and follow the competition's public-sharing rules if publishing code. Source: [competition rules](https://www.kaggle.com/competitions/kaggriculture/rules).

**First 48-hour target.** One working full-season agent, one reproducible comparison command, one replay explaining where money was lost, and one valid initial ladder submission. That gives both teammates a concrete platform for every subsequent improvement.
