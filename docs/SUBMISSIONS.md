# Submission registry

| Checkpoint | Artifact SHA-256 | Kaggle submission | Status |
| --- | --- | --- | --- |
| Step 2 | `fc50a8154b898f95e6baae8a0f2918fadb77a8cf933753b53ae8df921a9303a3` | `56132050` | Uploaded September 9, 2026; validation episode `107272004` completed |
| Step 3 | `ddd775729432e51be0ecf4462866ca4c75673fb1b55a0b12c0395c40d0a5114a` | `56132659` | Validation episode `107286447` completed; supplied replay exactly reproduced locally |
| Step 4 | `0024dc48be607636775eba055eea8bde54d3c0679e5e851439791b5d6cb741f9` | Not uploaded | Exact copied artifact passed isolated local self-play |
| Step 5 | `70fa2f8a16316bb51fc2ce9eb01b08259fdb83c256359ffc29e847dd459d5816` | `56148466` | Uploaded September 10; validation episode `107533896` and awarse match `107536016` reproduce exactly; our runtime actions match the frozen source |
| Step 6 | `d545236b1045fa522676931380ba68517eb2d359252783ea997156bb0f6f13ac` | Not uploaded | Locally prepared: 251/300 validation wins, 90 tests passed, isolated copied artifact passed full self-play; server validation pending upload |

Step 2's initial displayed rating was 600. Its server validation was self-play, with 13,297 coins per farm and no agent stderr. A local resimulation matched all actions and economic state; [audit and input hashes](benchmarks/step-2-server.json).

Step 3's validation self-play earned 15,355 coins per farm with no stderr. Its initial displayed rating was 600. A subsequent CLI snapshot during Step 4 work showed Step 3 at 436.8 and Step 2 at 366.7. These are time-specific ratings, not current promises or profit measures. [Step 3 server audit](benchmarks/step-3-server.json).

The historical submissions are frozen in `baselines/step_2.py`, `baselines/step_3.py`, and `baselines/step_5.py`. Step 4 is preserved separately. The new local release path is `artifacts/submission-step-6/main.py`; [Step 6 results](STEP_6_RESULTS.md) record its evaluation and isolated check. Local artifacts and raw logs are ignored by Git. A source push or local validation is not a Kaggle upload.

Step 5's supplied validation self-play earned 69,761 per farm. The user reported a later rating of 504.2; a subsequent September 10 CLI snapshot showed 573.3. [The Step 5 server audit](STEP_5_SERVER_ANALYSIS.md) separates those changing ratings from match cash and documents the 42,798–62,980 loss to awarse.

The latest two submissions in that snapshot are Steps 5 and 3. If there is no intervening upload, submitting Step 6 would displace Step 3, retaining Step 5 alongside the new candidate. Record the exact file hash, submission ID, validation episode, and later ladder results after upload. Step 6 currently has no server result.
