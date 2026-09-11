# Cycle 8 — decisions have continuation value

This cycle adds an **offline diagnostic**, not a new decision rule in the submitted bot. It measures what follows a purchase when both agents keep operating and investing. [Results](CYCLE_8_RESULTS.md), [implementation](../scripts/benchmark_continuation.py).

## From a CO250 objective to a sequential decision

In a static integer program, choosing a crop column consumes money, land and labor and earns an estimated return. Our current investment heuristic similarly enumerates discrete crop/livestock batches, tests resource constraints, and ranks marginal values. Its forecast describes the current portfolio plus one purchase. It does not solve a complete integer program, and it does not include the future purchases that the live agent will actually make.

The relevant comparison is instead the value of an immediate decision **followed by a policy**:

\[
Q^{\pi,\rho}(s,a)=\mathbb{E}[U(C_T^{own},C_T^{rival})\mid s,\ a\text{ now},\ \pi\text{ afterward},\rho\text{ for the rival}].
\]

Here \(s\) is a game state, \(a\) a purchase or defer action, \(\pi\) our continuation policy and \(\rho\) the opponent's policy. Both keep reacting to their observations. The win objective uses \(U=1\) for a win, \(1/2\) for a draw and zero for a loss; cash margin is an additional diagnostic. Each run here evaluates one realized continuation, not the expectation or the optimal value function.

Buying a melon now can reduce money available for a sheep tomorrow. Waiting can preserve that opportunity, but delays production and changes the farm's later workload. Giving only the waiting alternative a later purchase overstates its advantage. In this evaluator, both alternatives can invest later. Our early buy-now control makes fourteen more capital-order turns; its waiting competitor resumes at the next shop and makes seventeen.

## What a fair local intervention preserves

The evaluator replays historical joint actions only up to the selected observation and verifies both players' game state after every step. It then starts fresh instances of the frozen policies through Kaggle's loader. Only our capital orders are replaced; unit commands, feed, fertilizer, hires and sales remain in place. The official runner gives each player its own observation and the shared turn counter. The full replay and resolved seed remain evaluator data.

The unchanged control must reproduce every recorded future action and economic state. That check establishes compatibility for these deterministic, observation-based policies. It would not restore arbitrary hidden Python memory in a stateful policy; such a policy needs a different reconstruction procedure. Runtime overage bookkeeping is excluded from state equality because measured execution time varies.

Waiting has an explicit release time. A one-turn omission resumes immediately afterward; waiting for a shop resumes at observation 72. The latter chooses its eventual purchase from the observation available then. It does not receive the shop identity in advance. This respects nonanticipativity: a decision cannot use information that has not arrived.

## Opportunity costs, cash feasibility and shadow prices

LP duality gives a useful interpretation of scarce resources: a shadow price expresses how much the objective could improve with an additional unit of a binding resource. Our heuristic does not compute true dual variables. The analogy still helps distinguish a cheap purchase from one that uses scarce working capital, installation capacity or harvest labor.

The late state has roughly 20,000 coins of forecast cash headroom. Saving 70 on a wheat seed is unlikely to have the same opportunity value as saving 70 in an early farm with only hundreds available. At the early branch's later sheep purchase, the forecast minimum is 155 but realized cash drops to 64. The difference is mostly two extra feed purchases and another worker before receipts arrive.

A daily balance is insufficient to prove intra-day feasibility. A valid working-capital constraint must account for costs when they are paid:

\[
C_{t+1}=C_t+R_t-B_t-W_t-I_t,\qquad C_t\geq b_t.
\]

\(R_t\) is realized sales revenue, \(B_t\) operating inputs, \(W_t\) wages and \(I_t\) capital purchases. Future sales cannot fund an earlier feed order. Fibonacci hiring also makes the next worker a discrete marginal cost, rather than an average wage. The next experiment should correct measured missing obligations first, rather than increase a reserve constant without evidence.

## Competition and uncertainty

The late wheat intervention loses 833 own coins but improves margin by 520 because the rival loses more. Both versions already win, so the win objective does not improve. This illustrates why own-profit optimization, margin optimization and win-probability optimization are related but distinct.

It does not prove a deliberate market-denial strategy. The game's weed and shop draws share an RNG stream: occupancy changes can change the later shop list. Early waiting changes the first shop; late wheat changes the final opening. These paired runs establish outcomes of the full simulated interventions on this seed, but cannot attribute the effect solely to production timing or market supply at fixed demand.

No secret shop sequence or replay seed should enter the deployed policy. Broader calibrated evidence is required before selecting a challenger. For now, the useful output is a reproducible evaluator and a specific cash-forecast defect, while the proven Cycle 3 stays deployed.
