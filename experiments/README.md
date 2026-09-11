# Archived Cycle 2 policies

These sources are preserved for reproducibility and further diagnosis. None qualified for a Kaggle upload; `../main.py` is the unchanged Step 8 submission. See [the results](../docs/CYCLE_2_RESULTS.md).

- `staffing_dispatch.py`: first experimental source, with optional open livestock routes and dated crop staffing.
- `staffing.py`: second experimental source, adding separate staffing forecast controls.

Both have the experimental flags disabled at their default `agent` entry point. Use `python -m scripts.make_staffing_control` to select a tested mode. Supplying `--source experiments/staffing_dispatch.py` reproduces the three dispatch-only files; the generator defaults to `experiments/staffing.py` for the forecast variants. Sources retain the original Step 8 module description to preserve their recorded bytes; that description is not a promotion claim.
