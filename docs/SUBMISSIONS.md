# Submission registry

| Checkpoint | Artifact SHA-256 | Kaggle submission | Status |
| --- | --- | --- | --- |
| Step 2 | `fc50a8154b898f95e6baae8a0f2918fadb77a8cf933753b53ae8df921a9303a3` | `56132050` | Uploaded September 9, 2026; validation episode `107272004` completed |
| Step 3 | `ddd775729432e51be0ecf4462866ca4c75673fb1b55a0b12c0395c40d0a5114a` | `56132659` | Validation episode `107286447` completed; supplied replay exactly reproduced locally |
| Step 4 | `0024dc48be607636775eba055eea8bde54d3c0679e5e851439791b5d6cb741f9` | Not uploaded | Exact copied artifact passed isolated local self-play |
| Step 5 | `70fa2f8a16316bb51fc2ce9eb01b08259fdb83c256359ffc29e847dd459d5816` | Not uploaded | September 10: copied 30,864-byte artifact passed isolated local self-play; 240-game paired evaluation passed promotion criteria |

Step 2's initial displayed rating was 600. Its server validation was self-play, with 13,297 coins per farm and no agent stderr. A local resimulation matched all actions and economic state; [audit and input hashes](benchmarks/step-2-server.json).

Step 3's validation self-play earned 15,355 coins per farm with no stderr. Its initial displayed rating was 600. A subsequent CLI snapshot during Step 4 work showed Step 3 at 436.8 and Step 2 at 366.7. These are time-specific ratings, not current promises or profit measures. [Step 3 server audit](benchmarks/step-3-server.json).

The live Steps 2 and 3 are preserved in `baselines/step_2.py` and `baselines/step_3.py`. Step 4 is frozen in `baselines/step_4.py`; [its results](STEP_4_RESULTS.md) identify the local evidence. The current release is `artifacts/submission-step-5/main.py`; [Step 5 results](STEP_5_RESULTS.md) record its paired evaluation and isolated validation. Local artifacts and raw logs are ignored by Git. A source push or local validation is not a Kaggle upload.

The September 10 CLI snapshot still listed Steps 2 and 3 only, at 373.8 and 349.4 respectively. Those historical ratings do not evaluate Steps 4 or 5. After the next upload, record its ID, exact artifact hash, validation episode/status, and later competitive results. If no intervening upload occurs, uploading Step 5 would displace Step 2 from the latest-two window. Two Step 3 ladder losses are recorded in [the ladder audit](benchmarks/step-4-ladder-audit.json); the validation replay itself does not contain those matches.
