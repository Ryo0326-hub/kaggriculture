# Reproducible policy experiments

These sources are preserved for reproducibility and further diagnosis. Cycle 2's staffing policies did not qualify for upload; see [its results](../docs/CYCLE_2_RESULTS.md). Cycle 3's fertilizer-only variant qualified locally and runs as Kaggle submission 56158876; its exact source is preserved in `../baselines/cycle_3.py`. See [Cycle 3 results](../docs/CYCLE_3_RESULTS.md) and [server evidence](../docs/CYCLE_3_SERVER_ANALYSIS.md).

Cycle 4's isolated spatial-admission candidate is generated from frozen Cycle 3 by `python -m scripts.make_spatial_control --output NEW_DIRECTORY/main.py`. Only two candidate-menu conditions change; dispatch, forecasts and hiring retain their exact behavior. It **did not qualify for promotion**: its fresh improvement was uncertain and it regressed against the strongest control. Read the [results](../docs/CYCLE_4_RESULTS.md), [plan](../docs/CYCLE_4_PLAN.md) and [CO notes](../docs/CYCLE_4_OPTIMIZATION.md). `main.py` remains Cycle 3.

- `staffing_dispatch.py`: first experimental source, with optional open livestock routes and dated crop staffing.
- `staffing.py`: second experimental source, adding separate staffing forecast controls.

Both have the experimental flags disabled at their default `agent` entry point. Use `python -m scripts.make_staffing_control` to select a tested mode. Supplying `--source experiments/staffing_dispatch.py` reproduces the three dispatch-only files; the generator defaults to `experiments/staffing.py` for the forecast variants. Sources retain the original Step 8 module description to preserve their recorded bytes; that description is not a promotion claim.

`timing.py` holds the Cycle 3 source with its flags disabled by default. Generate the qualified fertilizer-only artifact using `python -m scripts.make_timing_control --mode fertilizer --bake-default --output NEW_DIRECTORY/main.py`. `--bake-default` also makes direct `expansion_turn` explanations use the selected mode. The harvest and combined modes are preserved for reproduction; the selected behavior retains Step 8's harvest rule. Module descriptions retain the historical Step 8 foundation wording to preserve frozen source hashes.
