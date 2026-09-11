# Reproducible policy experiments

These sources are preserved for reproducibility and further diagnosis. Cycle 2's staffing policies did not qualify for upload; see [its results](../docs/CYCLE_2_RESULTS.md). Cycle 3's fertilizer-only variant qualified locally and is now `../main.py`; server upload is pending. See [Cycle 3 results](../docs/CYCLE_3_RESULTS.md).

- `staffing_dispatch.py`: first experimental source, with optional open livestock routes and dated crop staffing.
- `staffing.py`: second experimental source, adding separate staffing forecast controls.

Both have the experimental flags disabled at their default `agent` entry point. Use `python -m scripts.make_staffing_control` to select a tested mode. Supplying `--source experiments/staffing_dispatch.py` reproduces the three dispatch-only files; the generator defaults to `experiments/staffing.py` for the forecast variants. Sources retain the original Step 8 module description to preserve their recorded bytes; that description is not a promotion claim.

`timing.py` holds the Cycle 3 source with its flags disabled by default. Generate the qualified fertilizer-only artifact using `python -m scripts.make_timing_control --mode fertilizer --bake-default --output NEW_DIRECTORY/main.py`. `--bake-default` also makes direct `expansion_turn` explanations use the selected mode. The harvest and combined modes are preserved for reproduction; the selected behavior retains Step 8's harvest rule. Module descriptions retain the historical Step 8 foundation wording to preserve frozen source hashes.
