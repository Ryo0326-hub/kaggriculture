# Submission registry

| Checkpoint | Artifact SHA-256 | Kaggle submission | Status |
| --- | --- | --- | --- |
| Step 2 | `fc50a8154b898f95e6baae8a0f2918fadb77a8cf933753b53ae8df921a9303a3` | `56132050` | Uploaded September 9, 2026; validation episode `107272004` completed |
| Step 3 | `ddd775729432e51be0ecf4462866ca4c75673fb1b55a0b12c0395c40d0a5114a` | `56132659` | Validation episode `107286447` completed; supplied replay exactly reproduced locally |
| Step 4 | `0024dc48be607636775eba055eea8bde54d3c0679e5e851439791b5d6cb741f9` | Not uploaded | Exact copied artifact passed isolated local self-play |
| Step 5 | `70fa2f8a16316bb51fc2ce9eb01b08259fdb83c256359ffc29e847dd459d5816` | `56148466` | Uploaded September 10; validation episode `107533896` and awarse match `107536016` reproduce exactly; our runtime actions match the frozen source |
| Step 6 | `d545236b1045fa522676931380ba68517eb2d359252783ea997156bb0f6f13ac` | `56149269` | Uploaded September 10; validation episode `107547593` completed at 63,524 per farm, exactly reproduced locally with all 1,438 runtime actions matching the source |
| Step 7 | `5ec112bd59eae75b2da53b4a35754a1d9c4261a6eb35677fef0b1d231e5b7a41` | `56156207` | Server confirmed; validation `107665260` and supplied ladder episodes reproduce exactly; September 11 public snapshot: 9 wins / 13 losses |
| Step 8 | `63dbf4381d8607cbd681f5296749f4f8af4cc37d0181f97d6b8931f6078d3f72` | `56157664` | Uploaded September 11 at 03:29:35 UTC; validation `107689872` passed, all 1,438 decisions match source; [server audit](benchmarks/step-8-server.json) |

Step 2's initial displayed rating was 600. Its server validation was self-play, with 13,297 coins per farm and no agent stderr. A local resimulation matched all actions and economic state; [audit and input hashes](benchmarks/step-2-server.json).

Step 3's validation self-play earned 15,355 coins per farm with no stderr. Its initial displayed rating was 600. A subsequent CLI snapshot during Step 4 work showed Step 3 at 436.8 and Step 2 at 366.7. These are time-specific ratings, not current promises or profit measures. [Step 3 server audit](benchmarks/step-3-server.json).

The historical submissions are frozen in `baselines/step_2.py`, `baselines/step_3.py`, and `baselines/step_5.py`. Step 4 is preserved separately. The Step 6 local release path was `artifacts/submission-step-6/main.py`; [Step 6 results](STEP_6_RESULTS.md) record its evaluation and isolated check. Local artifacts and raw logs are ignored by Git. A source push or local validation is not a Kaggle upload.

Step 5's supplied validation self-play earned 69,761 per farm. The user reported a later rating of 504.2; a subsequent September 10 CLI snapshot showed 573.3. [The Step 5 server audit](STEP_5_SERVER_ANALYSIS.md) separates those changing ratings from match cash and documents the 42,798–62,980 loss to awarse.

In the earlier snapshot, the latest two submissions were Steps 5 and 3. Step 6 has subsequently been uploaded, so that historical latest-two snapshot became **Steps 6 and 5**. At approximately September 11, 01:01 UTC (September 10 in Toronto), the CLI reports Step 6 complete at 590.8 and Step 5 at 506.5. These ratings are time-specific. A further upload would displace Step 5 unless another upload intervenes.

[The Step 6 server audit](STEP_6_SERVER_AND_LEADER_ANALYSIS.md) records the new validation, exact source match, log hashes, and comparison with the supplied SpaTaro–ymg_aq game. No Step 6 ladder match against another team was supplied in that audit. The strategy revision leaves the uploaded policy unchanged.

Step 7 was subsequently uploaded by the user. Its submission ID is 56156207. The September 11, 03:21 UTC official snapshot contains 22 completed public games: 9 wins and 13 losses. The supplied episode 107665260 is validation self-play (82,812 per farm), not another independent ladder match. [Snapshot](benchmarks/step-7-live-snapshot.json).

Step 8 was uploaded as 56157664 on September 11 at 03:29:35 UTC (September 10, 23:29 Toronto), description `Step 8 - conditional expansion - 9e7139a - 63dbf4381d86`. The latest-two pair is now **Steps 8 and 7**, displacing Step 6. Its validation episode 107689872 completed at 03:34:05 UTC: 94,876 / 95,069 cash, both DONE, all 1,438 decisions source-matched, no stderr or economic execution losses, maximum server action time 0.206756 seconds. At the 03:36:22 UTC snapshot there were no public games; its initial 600 rating establishes no competitive gain. [Exact-file server evidence](benchmarks/step-8-server.json).

First Step 8 public snapshot at September 11, 03:43:17 UTC: **0 wins / 0 draws / 1 loss**. Episode 107691005 ended 80,484–102,430 against Noobykiller16. All 719 actions match the source; execution and inventory checks remain clean. The loss exposes a production/staffing gap, not a runtime failure. [Audit](benchmarks/step-8-public-first.json). No automatic monitoring was scheduled.
