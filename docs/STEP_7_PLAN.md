# Revised plan: joint opening and dated production bundles

Prepared September 10, 2026, following [Step 6 server validation and the SpaTaro–ymg_aq audit](STEP_6_SERVER_AND_LEADER_ANALYSIS.md). **Proposal only.** The released Step 6 agent remains unchanged. This plan supersedes the earlier recommendation to focus narrowly on waiting versus buying a seed before broader allocation work.

## Decision

Make the next agent choose **complete production schedules that can turn into cash**, beginning on Day 1. Keep a small, explicit menu of alternatives. A crop schedule includes its seed, tile occupancy, watering, optional fertilizer, harvest, delivery, and cash timing. Animal purchases, crop purchases, and workers must compete within the same operating budget.

The leading-player evidence identifies several structural limits in Step 6: crops start late, crop count is tied to herd size, only eight plots are admitted, and fertilizer is absent from new-crop valuation. Tuning the two-coin work allowance while retaining all those restrictions is unlikely to close the observed strategy gap. The implementation should still proceed through small tested checkpoints rather than one replacement of the whole agent.

## First implementation: opening and production packages

Use the current 25-tile farm initially. Compare a bounded opening menu with, for example, 0/4/8/12 melons and several small cow/sheep allocations. Include the existing opening as a fallback/control. Those counts define experiments, not a predetermined best farm. The crop limit should follow executable schedules and available land rather than the installed herd count. Permit dedicated early crop work instead of waiting for every animal route to finish.

Compare these dated activities:

- Melon planted early, watered sparsely for survival and then through its yield window, harvested at age ten, delivered and sold promptly.
- Wheat harvested at age two, three, or four, with and without a feasible fertilizer application. Early harvest can release capital, land, or labor; maximum yield per plant is not always best.
- Strawberry with no fertilizer and strawberry with reserved applications around ages nine and thirteen. Count only production events recoverable before termination.
- Wait, retain cash, or leave a plot unused when current activity displaces a better later schedule.
- Short sequences such as an early melon followed by strawberries or wheat. Include removal/setup time and an executable delivery schedule; calendar dates alone do not prove feasibility.

Do not copy SpaTaro's zero-cash Day 2. Replace the fixed reserve rule experimentally with a dated cash budget that protects obligations until the next conservatively timed receipts. Failed or delayed deliveries need a buffer. Current cash and known inventory determine what can actually be purchased now.

## CO250 formulation

Let `x_j` select an integer activity or route template `j`. Its column specifies input/output quantities, cash payments, occupied tile-days, and worker actions by time. Include all complementary inputs in the template or explicit linking constraints. For example, a fertilized strawberry alternative cannot claim extra yield without reserved fertilizer, water, and application capacity.

The planning objective approximates expected terminal bank. Constraints include:

```text
x_j ∈ {0, 1} or a bounded integer lot count
one activity per occupied tile at a time
worker actions and travel fit each scheduled interval
inventory[next] = inventory[now] + delivered production + buys − sales − internal use
cash[next] = cash[now] + realized/planned sale receipts − purchases − wages − land
cash and inventory stay nonnegative at every relevant boundary
fertilized output requires a feasible application and watered production transition
harvest precedes deposit, deposit precedes sale, sale occurs before termination.
```

Use fine time buckets around purchases, delivery, daily refresh, and the final day. Daily totals alone can hide an inability to buy feed before a later receipt. The simulator executes unit actions before market orders, so newly bought goods or hired workers cannot be used in that same unit phase.

Market prices depend on both agents' sales. With frozen price forecasts, a bounded integer model is a local approximation. Revalue the selected bundle through the actual marginal price curve, including its effect on our other planned sales. A piecewise approximation or iterative repricing can improve this later; neither should be called an exact solution of the whole stochastic game.

**LP/duality connection:** a binding land, labor, cash, or fertilizer constraint creates an opportunity cost. If an offline LP relaxation is used, its dual values can diagnose which capacity is scarce. Otherwise label heuristic resource charges as estimates, not computed dual prices. Compare whole-bundle contribution after those resource costs rather than independent profit per crop.

The objective of winning remains distinct from expected cash. Use economic forecasts to propose policies; choose releases by paired win/draw/loss evidence. Do not infer win probability from the bank lead alone.

## Market competition and delivery

Generate rival-supply scenarios from visible planted crops and animals: earliest feasible delivery, a delayed delivery, and additional plausible supply. Do not import future replay actions or shop outcomes. Melon sales have little recurring town demand, so an early glut can make a later cycle unattractive.

A delivery task's benefit includes the expected price difference from arriving sooner and the purchases it can finance. Avoid rewarding faster delivery when the same worker would sacrifice more valuable watering or harvest work. Initial scheduling can enumerate short routes; a later time-expanded network or assignment model can benchmark the heuristic. Travel, task precedence, optional jobs, and shared inventories add constraints beyond basic minimum-cost flow.

The goal is robust performance against both early and late rival sellers. A fixed twelve-melon opening could perform poorly when both sides crowd the same market. Include smaller openings, alternative crops, and waiting in the tested menu.

## Conditional scale follows a feasible schedule

After the opening/bundle change is evaluated, remove the remaining arbitrary land-use restrictions and test 25 → 50 → 75 tiles. The first two purchases cost 1,000 and 2,000 coins. Approve one only if the additional activities can repay the land, seeds/animals, extra hires, travel, and displaced work before termination.

Capacity estimates alone are insufficient. Use actual route feasibility and shed capacity; produce stranded on the farm has no terminal cash value. More workers face nonlinear wages. Twelve hired hands cost 376 per day; adding a thirteenth costs another 233. Expansion must use integrated routes rather than imply one worker per new asset.

Land ownership has no terminal salvage value. Prefer an unexpanded feasible farm over a purchased quadrant that cannot be serviced. Conversely, a hard eight-crop or ten-animal cap should not reject clearly feasible, profitable capacity without an economic comparison.

## Maintenance and endgame, as a separate later experiment

For installed animals, compare full care, survival-only feeding, and retirement using remaining saleable output, fertilizer, feed, work, and terminal dates. Acquisition cost is sunk. The engine permits minimum-survival schedules that differ from daily feeding; missed care and feeding can change future output.

Keep the reliable Step 6 policy as a control. Record intended maintenance decisions before execution. Tests should flag missed **planned** obligations and unplanned escapes; they should not automatically reject every explicitly modeled retirement. Recover existing valuable output before abandonment when the route is worthwhile. Clearing an empty structure after escape also takes a DIG action before a crop can occupy that tile.

## Evaluation must become harder

The old 83.67% result is useful evidence against a related internal pool. It does not test an early, expanding, flexible rival at the level shown by SpaTaro. Add independently implemented reactive controls for:

| Control | Failure it should expose |
| --- | --- |
| Early melon seller with a feasible opening | Late production and delivery |
| Expanding sheep plus fertilized crops | Capacity caps and poor use of complementary inputs |
| Cow-heavy supplier | Milk oversupply and rival response |
| Delayed seller / inventory accumulator | Forecast sensitivity to unknown delivery times |
| Minimum-maintenance operator | Spending on low-value animal service |
| Frozen Step 6 and current melon specialist | Regression against existing strengths and weaknesses |

These are strategy-family approximations, not reconstructions of private source code. Replaying SpaTaro's fixed action list remains an accounting or scenario tool, never the decisive head-to-head benchmark. Actual Step 6 ladder losses are valuable missing evidence; the supplied self-play cannot substitute for them.

Use controlled states to isolate yield, fertilizer, route, and liquidity claims. Equal seeds do not hold future shops fixed in this engine because weed RNG consumption precedes shop selection. Final promotion must use the unmodified official simulator, both player seats, fresh seeds, and matched candidate/reference pools. Record the realized town regimes to explain failures, without giving that future information to the agent.

Before each validation run, freeze source, controls, seeds, hypotheses, and gates. Start with 30 fresh seed blocks across the agreed pool in both seats; budget runtime from measured CPU throughput. Report per-opponent scores, lower-tail margins, runtime, and operational incidents. Resample whole seeds for the paired score difference. A favorable overall score must not hide a substantial regression in one opponent family.

A release requires no execution errors, no missed committed tasks or unplanned losses, and evidence of improvement over Step 6 on the harder pool. Validate the exact standalone file. Record deliberate retirements separately; keep unused seeds, terminal stock, and overflow visible. The latest two eligible submissions currently hold Steps 6 and 5, so a new upload would replace Step 5 unless another upload intervenes.

## Work blocks at three hours per day

| Block | Main work | Completion gate |
| --- | --- | --- |
| 1 | Freeze Step 6; build early-seller control and dated crop-template checks | Legal full-season control; base/fertilized yields and cash timing independently checked |
| 2–3 | Implement bounded joint opening and crop-bundle valuation on 25 tiles | No input double counting or unfunded obligations; source-matched decision explanation; development advantage |
| 4 | Broaden controls, freeze candidate, run fresh paired evaluation and packaging | Promotion gates pass or retain Step 6 with a documented failure |
| 5–6 | Conditional land and integrated routes | Additional land demonstrably supports profitable schedules and survives the harder pool |
| 7 | Maintenance/endgame ablation | Intended retirements distinguished from defects; improvement on fresh comparisons |

This is a planning estimate, not a promise that every block will pass on its first attempt. Preserve evaluation and server validation if implementation takes longer. Use local CPU processes; no cloud instance or expiring credit is required for this plan. Keep CO notes and one concrete explained decision for every implemented checkpoint.
