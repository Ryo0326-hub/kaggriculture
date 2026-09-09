# Submission registry

| Checkpoint | Artifact SHA-256 | Kaggle submission | Status |
| --- | --- | --- | --- |
| Step 2 | `fc50a8154b898f95e6baae8a0f2918fadb77a8cf933753b53ae8df921a9303a3` | `56132050` | Uploaded September 9, 2026; validation episode `107272004` completed |
| Step 3 | `ddd775729432e51be0ecf4462866ca4c75673fb1b55a0b12c0395c40d0a5114a` | Not uploaded | Exact copied artifact passed isolated local self-play |

Step 2's initial displayed rating was 600. Its server validation was self-play, with 13,297 coins per farm and no agent stderr. A local resimulation matched all actions and economic state; [audit and input hashes](benchmarks/step-2-server.json).

The live Step 2 code is preserved in `baselines/step_2.py`. The prepared Step 3 file is `artifacts/submission-step-3/main.py`; [its results](STEP_3_RESULTS.md) identify the local validation evidence. Local artifacts and raw logs are ignored by Git. Do not treat a source-code push or local validation as a Kaggle upload.

After the next authorized upload, record its ID, exact artifact hash, validation episode/status, and later competitive results. Track the latest-two window deliberately. The user-supplied September 9 screenshot and logs establish the Step 2 checkpoint, not its subsequent live rating.
