# Cycle 15 — constraints before investment forecasts

The prior agent's economic calculations did not consistently describe its
executing policy. This repair keeps our existing opening, market-impact
valuation, shared inventory ledgers and dispatch framework, while reconciling
the six audit findings. It uses no trained model or LLM.

## 1. Deadline feasibility is a hard resource constraint

For a loaded worker, let `r` be remaining actions and `d` the distance to the
closest shed entrance. Depositing requires `d + 1` actions. The repaired policy
reserves returning workers with one action of headroom before assigning crop,
fertilizer or newborn-watering work. It builds the deposit and sale ledger
from those final commands, so it cannot sell cargo merely because an earlier
version of the command would have deposited it.

For a ripe one-time crop, improving yield by watering requires the whole chain:

`travel_to_crop + WATER + HARVEST + travel_to_shed + DROP <= remaining_actions`.

If that fails but harvesting and returning fits, harvest now. If neither fits,
do not start an unsellable harvest. This is a small scheduling feasibility
test. Increasing a heuristic urgency score cannot create missing actions.

A tomato's dry counter adds another deadline: at two unwatered nights it dies
before producing again. When production remains and the counter is already
one, watering takes priority over harvesting a nearly full plant. Final-day
and exhausted-plant harvests remain eligible because continuation value is
then absent.

## 2. Integer labor must be priced from the same model that requests hires

The previous aggregate model estimated five workers where the dispatcher
requested nine. Applying Fibonacci wages to the wrong integer cannot give a
consistent investment cost.

The repaired model retains every asset's coordinates. It covers animal and
crop service separately using the existing deterministic insertion-route
heuristic, including travel and pickup/deposit allowances. Crop service uses
stable daily allowances as current jobs finish. Animal installation temporarily
reserves station crews. Purchased seeds and animals are included in execution's
pending-work calculation; proposed investments enter dated future work.

Admission, next-day cash reserves and actual hiring all call this model. The
execution target has a twelve-worker cap. Admission sees the uncapped required
count and route feasibility, so thirteen required workers cannot be silently
reported as a feasible twelve.

At step 384, the shared model requests nine workers. Adding the audited wheat
plot requires ten. The extra ninth paid worker costs 34 coins that day. We
subtract this discrete marginal wage, rather than a fractional cost per plot.
Additional same-day installation hires are also charged when morning hiring
can still occur. A greedy regrouping is not credited as a wage saving.

This resembles integer resource allocation from CO250. An LP relaxation could
underprice a crop that crosses a crew threshold; the implemented accounting
keeps the actual integer wage step. The insertion tours are a heuristic, not
an optimal network-flow or routing solution, and the live crop dispatcher does
not literally follow every estimated tour.

## 3. Choose total net value under constraints

Each candidate `j` consists of actual purchase orders and dated production
assets. We compare:

`V_j = 0.75 * min_scenario(marginal portfolio receipts) - purchase_cost - added_wages`.

Marginal receipts retain our previous two scenarios: visible demand versus
weaker demand with greater rival supply. They include the effect of our extra
sales on prices received by existing production, and charge animal feed.
These are conservative accounting scenarios, not probabilities learned from
data or a solved equilibrium with the opponent.

At each purchase decision, the small discrete problem is to maximize `V_j`,
subject to funded purchase and operating reserves, worker/route limits,
installation space and order capacity. At most one complete bundle is admitted.
Work breaks a value tie; it no longer replaces the objective with `V_j/work_j`.

The distinction matters: a smaller investment may have a better profit/work
ratio while producing less total cash with the same paid crew. In duality
language, labor should carry the marginal value of a binding capacity
constraint. Assigning every action an arbitrary denominator is not a computed
dual price. We charge wages explicitly and enforce the remaining capacity.

New purchases use banked cash after existing commitments. An optimistic
same-turn sale forecast cannot fund them. Reserves include incumbent and new
animal feed and the full next-day crew. Pending seeds/animals block another
batch until installation has cleared.

## 4. Land is a fixed-cost investment, not a vacancy-count reward

The vacancy gate previously prevented every land candidate from reaching
valuation in the supplied game. It is removed. New land must still support
the actual proposed crop or animal placements and repay its full charge.
Animal expansion can now pay for land directly, without waiting for a crop
bundle to subsidize access to a pasture.

The purchasing window extends through hour 20. If a two-order land bundle is
best but morning sales/hires leave only one slot, defer it intact and reconsider
on the next observation. Do not buy an inferior one-order seed batch that then
locks the queue. Essential existing orders remain unchanged. Reconsideration
uses current prices and cash; it does not blindly execute a stale commitment.

The fixed menu still considers only bounded batch sizes and limited future
land use. Removing a software blocker is not proof that every expansion is
profitable or that three quadrants will always be purchased.

## 5. Distinguish known inputs from uncertain future purchases

Tomato production on date `d` uses watering and fertilizer from date `d - 1`.
Existing fertilizer therefore gives two units when its expiry includes that
prior day, reverting to one afterward. The forecast does not assume buying
more fertilizer. Existing held yield is credited once under the established
daily-harvest forecast; maintenance and timely harvesting remain assumptions
costed through the service model.

This correction reconciles all fifteen audited, already-watered night
transitions. It does not make longer-horizon prices, future task execution or
held-yield timing certain. Server evidence is still required to evaluate the
complete production policy.
