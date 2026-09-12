# Cycle 15 — repaired custom agent, original release record

**Server update:** both newly supplied games finish cleanly but lose at 81,939 and 86,193 final coins. See the [growth diagnosis and revised plan](CYCLE_15_SERVER_ANALYSIS.md). The original packaging/verification record below is retained as history.

This implements Ryo's request to fix all six findings in the
[Cycle 13 logic audit](CYCLE_13_LOGIC_AUDIT.md), including the earlier land
admission failure. It is a repaired **custom Cycle 13 descendant**. The separate
public V36 / Cycle 14 candidate and its notices remain byte-identical.

| Audit finding | Repair | Bounded evidence |
| --- | --- | --- |
| Land cannot reach valuation | Remove the arbitrary vacant-field gate, allow funded purchases through hour 20, defer a preferred two-order bundle intact when slots are crowded, and admit land-plus-animal options | Recorded step 336 now emits BUY_LAND and eight tomato seeds despite more than four vacant existing fields; a constructed crowded-order case retries after hour six |
| Urgent jobs override terminal cargo return | Reserve returning workers before newborn, urgent and fertilizer assignments; retain shared deposit/sale accounting | Original fixture now returns EAST; final shed delivery is sold in the same action |
| WATER ignores its subsequent harvest/delivery deadline | Budget water, harvest, travel and deposit together; harvest immediately if only that shorter chain fits | With four/five/six actions remaining, empty-handed wheat fixture returns PASS/HARVEST/WATER |
| Tomato harvest overrides fatal watering | Water first when the dry counter threatens a plant with production remaining; retain harvest after the final event or on the final day | Original hour-23 fixture now returns WATER |
| Labor forecast differs from requested hiring | One model retains coordinates and prices livestock/crop routes and installation crews in forecasts, reserves and hiring; infeasible requirements stay visible above twelve workers | Recorded step 384 now agrees at nine workers; the added-wheat case agrees at ten and charges 34 more coins |
| Existing tomato fertilizer omitted | Use the previous day's fertilizer expiry for each production night, without assuming new fertilizer | All fifteen previously identified recorded transitions now agree at two units |
| Profit/work ratio rejects greater net value | Choose maximum total estimated net cash among funded feasible options; use work only to break ties | The recorded land decision selects the highest-valued eligible alternative |

The table separates two terminal manifestations of one audited dispatch defect.
It does not attribute the original loss to every constructed regression, or
claim an exhaustive proof that the whole agent is bug-free.

## Exact artifact and upload

`artifacts/submission-cycle-15-repairs/main.py`

SHA-256: `ce4444126f5ef7e0ee01a22f395ae87ee442ec2f329c4feb6aedf0687af45f1a`.

The artifact is already built locally. **Use this path**: root `main.py` is
still the protected Cycle 3 source. The installed Kaggle CLI accepts the
competition name as a positional argument:

```bash
/Users/ryokitano/.local/bin/kaggle competitions submit kaggriculture \
  -f /Users/ryokitano/Documents/Projects/kaggriculture/artifacts/submission-cycle-15-repairs/main.py \
  -m "Cycle 15 - audited logic repairs - ce4444126f5e"
```

No automatic upload was made. Kaggle validation, submission ID and competitive
performance are pending. These repairs do not establish a rating or revenue
improvement; the next supplied server games provide that evidence.

## Verification completed

- 45 bounded tests pass: 26 repair tests plus the 16 frozen Cycle 13 and three
  unchanged-public-source packaging tests.
- 54 isolated decisions pass on both seats at nine fixed observations in each
  of episodes 107984963, 107972592 and 107970619. They check serialization,
  worker/action counts, order limits and observation immutability.
- Isolated loading selects `agent` as the last callable. Startup was 0.0308
  seconds and the slowest sampled callback 0.0911 seconds against a one-second
  action limit. This is sampled timing, not a worst-case runtime guarantee.
- All fifteen earlier tomato fertilizer comparisons agree with recorded
  successor states. The checker never generates successor states.
- Repository Ruff, formatting and Python compilation pass. Exact hashes verify
  that root Cycle 3, Cycles 12–14 and vendored V36 are unchanged.

[Check summary](benchmarks/cycle-15-repair-checks.json) ·
[Recorded regression observations](examples/cycle-15-repair-observations.json) ·
[Tests](../tests/test_repairs.py) · [CO/economics notes](CYCLE_15_OPTIMIZATION.md).

**No local games, counterfactual episodes, engine imports, training, cloud
spending or API calls were used.** Calling the candidate on an opponent's
recorded farm is an interface stress check, not a match against that opponent.

Rebuild into a new output path; the builder refuses overwriting:

```bash
uv run --no-sync python -m scripts.make_repaired_agent \
  --output artifacts/submission-cycle-15-repairs/main.py
```

The builder first reproduces Cycle 13 and checks its hash, then applies repairs.
Tests use temporary paths. Artifacts remain ignored by Git; committed source,
builder and documented hash reproduce the upload in a fresh checkout.

## What to inspect after resubmission

Return Kaggle's validation and gameplay logs. Check whether land purchases
execute, seeds/animals leave the installation queue, the added area produces
saleable output, and cash growth repays extra wages. Inspect terminal cargo,
watering losses, actual staffing and market fills. The pending-input gate is
retained intentionally to avoid funding overlapping uninstalled batches.

Daily service routes and two demand scenarios remain estimates. Crop dispatch
is greedy and is not guaranteed to execute the estimated tours exactly. The
fixed candidate menu does not value every future reuse of land or every crop
sequence. More features or these correctness checks alone do not prove that
Cycle 15 beats the unchanged public V36 baseline.
