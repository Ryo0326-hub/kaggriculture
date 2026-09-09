# Step 2: assigning workers without conflicting actions

Implemented September 9, 2026. This checkpoint connects CO250's binary decision variables and resource constraints to an executable multi-worker agent. The next checkpoint will address production economics and investment. [Step 1's routing notes](OPTIMIZATION.md) remain available, and its original code is preserved in `baselines/step_1.py`.

## What changed in the farm

The agent can hire up to four hands and operate the 25 tiles in the initially owned northwest quadrant. It still grows only wheat. Every turn it constructs useful tasks, removes infeasible worker-task pairs, chooses a joint assignment, and issues one immediate command per existing worker. It replans from the next observation rather than storing an unverified schedule.

The policy first protects crops that need water, then collects mature crops, banks carried wheat, and establishes new production. A task's priority and travel cost jointly determine its score; these priorities are heuristic, not measured profit or LP dual variables. Hiring up to four hands is also a heuristic. With default costs, four hires cost `1 + 1 + 2 + 3 = 7` coins per day. Whether an additional hand pays back depends on the work it actually completes.

The code keeps three boundaries explicit:

| Decision | Method | Guarantee |
| --- | --- | --- |
| Generate tasks, choose wheat, set workforce and priorities | Handwritten policy | Tested behavior, no optimality guarantee |
| Match existing workers to feasible tasks, reserving seeds | Exact bounded dynamic program | Maximum total supplied assignment score |
| Convert assignments to commands, reserve storage, order trades | Deterministic execution rules | Resource and timing checks; no global scheduling guarantee |

## The CO250 integer model

Let `W` be existing workers and `J` the generated tasks. Define:

- `x_wj = 1` if worker `w` is assigned task `j`, otherwise zero.
- `v_wj = priority(j) - 100 * ManhattanDistance(worker, target)`.
- `P` as the subset of planting tasks and `S` as the seeds currently available.
- `E` as worker-task pairs that satisfy the feasibility checks.

The subproblem is:

```text
maximize    sum_(w,j in E) v_wj x_wj
subject to  sum_j x_wj <= 1                 for every worker w
            sum_w x_wj <= 1                 for every task j
            sum_w sum_(j in P) x_wj <= S    shared planting-seed quota
            x_wj = 0                       for (w,j) outside E
            x_wj in {0, 1}.
```

The first two inequalities prevent one worker receiving two targets and two workers receiving the same task. The task generator emits at most one crop task per tile, so task uniqueness also prevents conflicting crop actions there. Several workers may legitimately use different private deposit tasks at the same shed access point; storage is reserved separately.

The seed constraint matters because the engine rejects **all** planting requests for a crop when their combined request exceeds available seeds. Purchased seeds arrive after worker actions, so they cannot increase `S` for this solve. A selected planting target reserves a seed even while the worker is travelling. This is conservative; it prevents overcommitment but may leave another useful planting choice unavailable for that turn.

Infeasible pairs include another worker's private deposit task, a job that cannot be reached and performed within the day's remaining actions, or planting without enough time for its subsequent watering. Near termination, harvest and watering edges must also leave time to reach the shed, deposit, and sell. A worker carrying wheat must return when its banking deadline becomes urgent.

## Why choose the assignment jointly?

Consider two workers and two tasks:

| Score | Task A | Task B |
| --- | ---: | ---: |
| Worker 0 | 10 | 9 |
| Worker 1 | 9 | 0 |

A worker-order greedy method gives A to worker 0, producing a total score of 10. Joint assignment gives B to worker 0 and A to worker 1, producing 18. The small sacrifice by one worker makes the entire assignment better.

That argument proves a property of this score matrix. It does not prove an eight-coin improvement or a higher game win rate. Task scores are proxies, and future states depend on the immediate actions. We therefore compare the policy with a control that changes only the assignment algorithm, keeping the workforce, crop area, task scores, and trade rules identical.

## How the exact algorithm works

`maximum_assignment` in `main.py` scans tasks one at a time. Its state is `(mask, seeds_used)`, where `mask` records which workers already received a task. Each state retains the highest score and its assignment.

For each next task, there are two choices:

1. Skip the task and retain the state.
2. Assign it to one eligible, unassigned worker, provided its seed requirement fits; update that worker's bit and the seed count.

Only the best score for each resulting state is needed. Every future choice sees the same remaining tasks, available workers, and seeds, so a lower-scoring path to that same state cannot improve the final result. Induction over the task list gives optimality for the stated model. Strict-improvement updates and stable input order provide deterministic tie-breaking.

There are at most five workers, 30 tasks, and six distinct seed-use counts. The transition count is bounded by `O(|J| * |W| * 2^|W| * (min(S, |W|) + 1))`. Assignment tuples add a small bounded copying cost. Keeping the problem tiny lets the submission use only Python's standard library; it needs no external solver or model files.

`tests/test_assignment.py` compares the result with an independent exhaustive enumeration over small random matrices, including negative values, forbidden edges, zero seeds, and ties. This checks optimization correctness separately from game performance.

## Execution details that affect validity and cash

| Mechanism | What the code does | Why it matters |
| --- | --- | --- |
| New hands | Hire in the market queue; assign only workers already present | A hand hired now cannot act earlier in that turn |
| Crop maintenance | Prioritize unwatered crops; reserve a follow-up action when planting | A new crop can die at the first day boundary |
| Shared seed stock | Constrain all selected planting jobs together | Avoid atomic cancellation of simultaneous planting |
| Shed storage | Reserve actual `PLACE` amounts in engine worker order | A worker keeps wheat that does not fit, unlike a `DROP` that discards excess |
| Market order | Sell existing shed wheat plus actual planned deposits | Unit actions happen before market actions |
| Funding | Budget hires and seed purchases from observed cash | No dependence on a speculative sale price |
| Endgame | Stop new growth conservatively; retain harvest labor and return produce before step 718 | Only cash counts at termination |

Storage allocation happens **after** the assignment solve. If multiple depositing workers compete for the last storage space, later commands may be reduced to `PASS`. Thus the solver's optimum is a statement about the assignment matrix and seed constraint, not an optimum including every shared-storage interaction. Full-season tests check whether these safeguards work in actual engine trajectories.

The policy does not yet solve multi-turn worker routes, enforce all future maintenance obligations jointly, optimize seed lot sizes, or model demand and opponent supply. Assignments may switch between turns. These are reasons to evaluate complete games rather than infer success from a correct assignment solver.

## Where LP duality and network flow fit

Without the extra resource constraints, bipartite worker-task assignment has an integral LP relaxation. It also has a flow interpretation: send units of flow from workers to tasks through capacity-one edges. That is a concrete bridge to your upcoming network-flow course.

Adding arbitrary shared-resource or precedence constraints does not preserve integrality automatically. We do not rely on an integrality claim for this implementation; the dynamic program enforces the integer choices and seed quota directly. We also do not calculate dual prices here. A future economic model can estimate marginal labor and capital values, but those values must be tied to the model that produced them.

## Inspect an actual decision

`plan_turn` returns both the executable action and an explanation. Kaggle's `agent` entry point returns only the action. To reconstruct a saved decision:

```bash
uv run python explain_turn.py \
  --replay artifacts/step-2-development-v2/replay-0001.json \
  --state 30 --player 0
```

The script verifies the candidate source hash against the run manifest and checks that the reconstructed command equals the recorded action. A different code version or opponent seat can cause it to refuse the explanation. Replay state index 30 describes the observation used to produce the action stored at index 31.

[The saved example](examples/step-2-decision.json) shows day 1, hour 6: five workers receive five distinct watering targets. Two water immediately and three move one tile toward their targets. Their scores are `20000, 19900, 20000, 19900, 19900`, totaling 99,700. This is an assignment score, not coins earned.

See [Step 2 results](STEP_2_RESULTS.md) for full-game evidence and [the README](../README.md) for preparing the exact submission artifact. Local validation is necessary preparation; Kaggle's server validation remains a separate checkpoint.
