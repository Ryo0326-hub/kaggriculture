# From CO250 to a farming agent

Your CO250 background is directly useful. We can model actions as decision variables, express scarce resources as constraints, use integer variables for indivisible choices, and use duality to reason about resource values. What we cannot honestly claim is that one ordinary LP exactly solves the full competition.

Implementation history: [Step 1 routing](STEP_1_RESULTS.md), [Step 2 assignment](STEP_2_OPTIMIZATION.md), [Step 3 production/hiring economics](STEP_3_OPTIMIZATION.md), and [Step 4 livestock capital and liquidity](STEP_4_OPTIMIZATION.md). Step 3 adds an enumerated integer lot model and marginal workforce comparisons; it does not calculate LP dual prices.

## 1. State the real objective

Let `C_T` be our terminal cash and `C'_T` the opponent's terminal cash. Against a distribution of opponents and game randomness, the competition objective is to maximize

```text
P(C_T > C'_T) + 0.5 P(C_T = C'_T).
```

Expected terminal cash and cash margin are useful development objectives, but neither is identical to win probability. Full-game evaluations therefore retain win/draw/loss outcomes as well as cash.

Only observations available to the agent belong in its decisions. Opponent inventory and future shop unlocks are not known. Evaluation seeds and complete replay state are evaluation tools, not policy inputs.

## 2. Recognize the familiar optimization structure

For a planning interval, let `x_j` indicate whether candidate task `j` is selected. A simplified model is:

```text
maximize    sum_j v_j x_j
subject to  sum_j a_rj x_j <= b_r       for each resource r
            x_j in {0, 1}              for indivisible tasks
```

Here `v_j` estimates the task's additional terminal cash, `a_rj` measures required labor, cash, seeds, feed, or storage, and `b_r` is available capacity. Add precedence constraints for dependencies, such as planting before watering or dropping produce before selling it. Travel and deadlines must also be represented before a proposed task plan is executable.

This resembles the integer programs you have seen in CO250. It is a useful starting model, not the complete game: task values interact, market prices depend on both players' sales, and decisions consume time at specific positions.

## 3. Step 1's exact optimization: a tiny routing problem

Suppose the farmer is at `s` and a selected task batch occupies distinct tiles `p_1, ..., p_k`, with `k <= 4`. Tiles can be traversed without obstacles, so the shortest movement distance between two tiles is

```text
d(a, b) = |a_x - b_x| + |a_y - b_y|.
```

For a permutation `pi` of the targets, minimize

```text
d(s, p_pi(1)) + sum_{i=1}^{k-1} d(p_pi(i), p_pi(i+1)).
```

`shortest_route` in the frozen `baselines/step_1.py` enumerates every permutation and returns a minimizer, using deterministic tie-breaking. With four targets there are only 24 candidate orders. Because the enumeration covers every possible order and each inter-target distance is exact, the chosen route is optimal for the stated open-route problem.

An alternative CO250 formulation would introduce binary arc variables describing which target follows which, plus connectivity constraints. For just four targets, explicit enumeration is simpler than adding a solver dependency.

The independent test oracle performs breadth-first search over `(grid position, set of targets already visited)`. You do not need prior graph theory for the interpretation: it explores all reachable states after zero moves, then one move, then two, until every target has been visited. This checks the route result using a different method.

The proof does **not** extend to the whole farming policy. The route ignores different task values, deadlines, return-to-shed requirements, and future tasks. The baseline handles those with simple outer priorities. Even the best route through a bad task selection is a bad farm strategy.

## 4. Step 2: worker assignment — now implemented

The current agent implements a bounded exact assignment solver with a shared seed quota. [The Step 2 notes](STEP_2_OPTIMIZATION.md) explain the implemented model, dynamic program, execution rules, and replay explanations. The following model introduces that checkpoint.

Let `x_wj = 1` mean worker `w` is assigned task `j`. With estimated net benefit `v_wj`, the basic assignment model is:

```text
maximize    sum_w sum_j v_wj x_wj
subject to  sum_j x_wj <= 1            for every worker w
            sum_w x_wj <= 1            for every task j
            x_wj in {0, 1}.
```

Calculate `v_wj` after considering distance, worker inventory, deadlines, and the opportunity cost of time. Remove infeasible worker-task pairs. Add explicit shared-stock and cash constraints before issuing actions.

The pure bipartite assignment model has an integral LP relaxation and a network-flow interpretation. This is a natural bridge from CO250 to your upcoming network-flow course. Adding arbitrary shared resource constraints or dependencies can destroy that integrality; then the same guarantee no longer applies. We will explain that distinction before selecting an algorithm.

## 5. Duality: how much is one more unit of a resource worth?

For a chosen linear relaxation

```text
primal:  max v^T x  subject to A x <= b, x >= 0
dual:    min b^T y  subject to A^T y >= v, y >= 0,
```

the dual variables price scarce resources in that relaxation. A labor dual value can help estimate the benefit of another available worker-action; a land dual value can indicate whether extra growing space is the current bottleneck.

These are model-dependent marginal values, not universal game prices. The value of a finite land purchase, a worker with a particular position, or an extra hand late in the day requires checking the actual integer decision. Simply multiplying an LP shadow price by 24 does not prove a hire is profitable.

For the same correctly specified linear objective and feasible set, relaxing integrality gives an upper bound on the integer maximization optimum. An optimistic price forecast is not automatically an upper bound on the actual game's win probability.

## 6. Why the complete game needs more than LP

- Quantities, workers, tiles, and actions are discrete.
- Production and routing introduce dependencies across time.
- Revenues are nonlinear and affected by the opponent's sales.
- Future demand is uncertain and opponent inventory is hidden.
- Decisions must return within the runtime budget.

The intended strategy is to solve useful restricted problems well, execute feasible actions, and replan after new observations. Later, scenario-based planning can represent uncertainty. We will only retain the additional complexity when full-game comparisons justify it.

## Step 1 acceptance criteria

- A self-contained Python artifact completes full seasons using the official loader.
- Tiny route instances match the independent exact oracle.
- Mechanics tests establish action order, resource location, storage loss, and terminal timing.
- Seeded matches reproduce outcomes and work in both player positions.
- Final carried/shed produce is sold in tested normal episodes.
- Reports preserve environment and artifact provenance and distinguish errors from wins.

Coordinated assignment is implemented in [Step 2](STEP_2_OPTIMIZATION.md), and two-crop allocation, hiring economics, and a finite supply stress case in [Step 3](STEP_3_OPTIMIZATION.md). Land acquisition and broader uncertain-demand planning remain future work. These notes preserve Step 1's routing example; they do not claim the current agent solves that same route problem.

The active Step 4 policy uses a binary capital choice, marginal whole-herd cash flows, and a liquidity constraint. It executes distinct worker stations. Earlier routing and assignment algorithms remain in the frozen crop baselines; Step 4 does not claim their optimality guarantees for its station policy.
