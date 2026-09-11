# Submission registry

Cycle 3 fertilizer timing was uploaded as **56158876**, September 11 at 05:02:52 UTC. Its artifact is `artifacts/submission-cycle-3-fertilizer/main.py`, hash `47c281bfb411…`, preserved in `baselines/cycle_3.py`. The September 11, 11:28 UTC official CLI snapshot marks it COMPLETE at **734.6**, with Step 8 at 672.4; the latest-two pair is **Cycle 3 / Step 8**. Ratings are time-specific, not profit or a guarantee of strength. [Snapshot](benchmarks/cycle-4-submissions-snapshot.json).

Three supplied public games match all 2,157 own source decisions and reproduce every economic state: one win and two losses, clean own execution, maximum server decision time 0.254936 seconds. The separate validation replay was not supplied in this cycle. [Server analysis](CYCLE_3_SERVER_ANALYSIS.md). No upload is performed as part of Cycle 4's spatial-admission experiment; a future upload would displace Step 8 if the pair remains unchanged.

Cycle 4 is complete **without promotion or upload**. Challenger `a9adaa81f622…` scored 74.2% versus Cycle 3's 73.3%, with an inconclusive whole-seed interval and a strongest-control regression (25/40 versus 28/40 wins). It remains an archived experiment, not a qualified release. `main.py` remains `47c281bfb411…`. [Decision and evidence](CYCLE_4_RESULTS.md).

Cycle 5 is complete **without promotion or upload**. Future-demand challenger `3f2691bf2761…` tied Cycle 3 at 66.7% development match score, with lower mean cash and regressions against two controls. It did not advance to fresh evaluation or isolated release validation. The submitted Cycle 3 artifact remains unchanged, and this cycle did not refresh the server snapshot. [Results](CYCLE_5_RESULTS.md), [scenario and CO notes](CYCLE_5_OPTIMIZATION.md).

Cycles 6 and 7 completed **without promotion, release preparation or upload**. The waiting/supply-stress challenger (`6365a19af351…`) scored 38.9% versus 72.2% and exceeded the one-second target. The separate wheat correction (`232a0293ed5a…`) tied 72.2% without improving outcomes. The original Cycle 3 source remains unchanged; no new server status was queried. Fresh seeds 9401–9420 remain unused. [Cycle 6](CYCLE_6_RESULTS.md), [Cycle 7](CYCLE_7_RESULTS.md).

Cycle 8 completed an **offline purchase-continuation diagnostic, with no live-policy change or upload**. Six continuations on two consumed states preserve reactive play and later investment, reproduce both unchanged controls exactly and reconcile all cash accounts. Its next hypothesis is remaining-day feed/labor costs missing from an investment cash forecast. This is not a qualified release or six independent benchmark games. No server snapshot was refreshed, and seeds 9401–9420 remain unused. [Results](CYCLE_8_RESULTS.md).

Cycle 9 completed **without promotion or upload**. Cash-admission challenger `f789bc00a15f…` improves cash calibration but scores 61.1% versus 72.2%, failing development. Cycle 3 remains byte-identical. New supplied public episode 107928511 is a 73,860–122,954 loss to Ace Team; all 719 own decisions match Cycle 3, with no stderr and maximum server decision time 0.302481 seconds. Its replay does not identify a submission ID. No latest-two/rating query or fresh evaluation was performed. [Experiment](CYCLE_9_RESULTS.md), [server analysis](CYCLE_9_SERVER_ANALYSIS.md).

Cycle 10 completed **without promotion, release preparation or upload**. Wheat-opening challenger `823841703561…` scored 50.0% versus Cycle 3’s 79.2% on the new four-control development grid. Its runtime and operational checks pass, but competitive gates fail. `main.py` and the submitted artifact remain unchanged, seeds 9401–9420 remain unused, and no server snapshot was refreshed. [Results](CYCLE_10_RESULTS.md), [CO notes](CYCLE_10_OPTIMIZATION.md).

Cycle 11 completed **without promotion, release preparation or upload**. Carrot challenger `16bb5ba43889…` ties Cycle 3 at 75.0% on its four-control development grid. Higher average cash does not clear the match-score gate, and the audit finds fertilizer forecast/execution inconsistency. All incumbent copies remain unchanged; reserved seeds are unused and no server snapshot was refreshed. [Results](CYCLE_11_RESULTS.md).

Cycle 12 is **packaged for a user-run Kaggle test, with upload/server validation pending**. Candidate `555c312fc2c0…` is at `artifacts/submission-cycle-12-carrot-inputs/main.py`. The user requested stopping local simulations; the fresh reference stopped at 148/160 games, so there is no final paired qualification. Packaging only checked syntax and exact bytes, without another simulation. Cycle 3 remains unchanged in `main.py` and its preserved artifacts. No latest-two snapshot was refreshed; the prior recorded pair is historical. [Results and exact upload command](CYCLE_12_RESULTS.md).

Cycle 2 staffing experiments completed locally without a release. None of six candidates improved the matched development match score, so `main.py` was retained as Step 8 at that checkpoint. No additional upload or server-validation result was recorded for Cycle 2. [Evidence and decision](CYCLE_2_RESULTS.md).

| Checkpoint | Artifact SHA-256 | Kaggle submission | Status |
| --- | --- | --- | --- |
| Step 2 | `fc50a8154b898f95e6baae8a0f2918fadb77a8cf933753b53ae8df921a9303a3` | `56132050` | Uploaded September 9, 2026; validation episode `107272004` completed |
| Step 3 | `ddd775729432e51be0ecf4462866ca4c75673fb1b55a0b12c0395c40d0a5114a` | `56132659` | Validation episode `107286447` completed; supplied replay exactly reproduced locally |
| Step 4 | `0024dc48be607636775eba055eea8bde54d3c0679e5e851439791b5d6cb741f9` | Not uploaded | Exact copied artifact passed isolated local self-play |
| Step 5 | `70fa2f8a16316bb51fc2ce9eb01b08259fdb83c256359ffc29e847dd459d5816` | `56148466` | Uploaded September 10; validation episode `107533896` and awarse match `107536016` reproduce exactly; our runtime actions match the frozen source |
| Step 6 | `d545236b1045fa522676931380ba68517eb2d359252783ea997156bb0f6f13ac` | `56149269` | Uploaded September 10; validation episode `107547593` completed at 63,524 per farm, exactly reproduced locally with all 1,438 runtime actions matching the source |
| Step 7 | `5ec112bd59eae75b2da53b4a35754a1d9c4261a6eb35677fef0b1d231e5b7a41` | `56156207` | Server confirmed; validation `107665260` and supplied ladder episodes reproduce exactly; September 11 public snapshot: 9 wins / 13 losses |
| Step 8 | `63dbf4381d8607cbd681f5296749f4f8af4cc37d0181f97d6b8931f6078d3f72` | `56157664` | Uploaded September 11 at 03:29:35 UTC; validation `107689872` passed, all 1,438 decisions match source; [server audit](benchmarks/step-8-server.json) |
| Cycle 3 fertilizer | `47c281bfb4118a9755f1759930b162de007efdfef3b23144457eccbaac42da0c` | `56158876` | Uploaded September 11 at 05:02:52 UTC; COMPLETE; three public games source-matched and reconciled, 1 win / 2 losses; [server evidence](benchmarks/cycle-3-public-three.json) |

Step 2's initial displayed rating was 600. Its server validation was self-play, with 13,297 coins per farm and no agent stderr. A local resimulation matched all actions and economic state; [audit and input hashes](benchmarks/step-2-server.json).

Step 3's validation self-play earned 15,355 coins per farm with no stderr. Its initial displayed rating was 600. A subsequent CLI snapshot during Step 4 work showed Step 3 at 436.8 and Step 2 at 366.7. These are time-specific ratings, not current promises or profit measures. [Step 3 server audit](benchmarks/step-3-server.json).

The historical submissions are frozen in `baselines/step_2.py`, `baselines/step_3.py`, and `baselines/step_5.py`. Step 4 is preserved separately. The Step 6 local release path was `artifacts/submission-step-6/main.py`; [Step 6 results](STEP_6_RESULTS.md) record its evaluation and isolated check. Local artifacts and raw logs are ignored by Git. A source push or local validation is not a Kaggle upload.

Step 5's supplied validation self-play earned 69,761 per farm. The user reported a later rating of 504.2; a subsequent September 10 CLI snapshot showed 573.3. [The Step 5 server audit](STEP_5_SERVER_ANALYSIS.md) separates those changing ratings from match cash and documents the 42,798–62,980 loss to awarse.

In the earlier snapshot, the latest two submissions were Steps 5 and 3. Step 6 has subsequently been uploaded, so that historical latest-two snapshot became **Steps 6 and 5**. At approximately September 11, 01:01 UTC (September 10 in Toronto), the CLI reports Step 6 complete at 590.8 and Step 5 at 506.5. These ratings are time-specific. A further upload would displace Step 5 unless another upload intervenes.

[The Step 6 server audit](STEP_6_SERVER_AND_LEADER_ANALYSIS.md) records the new validation, exact source match, log hashes, and comparison with the supplied SpaTaro–ymg_aq game. No Step 6 ladder match against another team was supplied in that audit. The strategy revision leaves the uploaded policy unchanged.

Step 7 was subsequently uploaded by the user. Its submission ID is 56156207. The September 11, 03:21 UTC official snapshot contains 22 completed public games: 9 wins and 13 losses. The supplied episode 107665260 is validation self-play (82,812 per farm), not another independent ladder match. [Snapshot](benchmarks/step-7-live-snapshot.json).

Step 8 was uploaded as 56157664 on September 11 at 03:29:35 UTC (September 10, 23:29 Toronto), description `Step 8 - conditional expansion - 9e7139a - 63dbf4381d86`. The latest-two pair is now **Steps 8 and 7**, displacing Step 6. Its validation episode 107689872 completed at 03:34:05 UTC: 94,876 / 95,069 cash, both DONE, all 1,438 decisions source-matched, no stderr or economic execution losses, maximum server action time 0.206756 seconds. At the 03:36:22 UTC snapshot there were no public games; its initial 600 rating establishes no competitive gain. [Exact-file server evidence](benchmarks/step-8-server.json).

First Step 8 public snapshot at September 11, 03:43:17 UTC: **0 wins / 0 draws / 1 loss**. Episode 107691005 ended 80,484–102,430 against Noobykiller16. All 719 actions match the source; execution and inventory checks remain clean. The loss exposes a production/staffing gap, not a runtime failure. [Audit](benchmarks/step-8-public-first.json). No automatic monitoring was scheduled.
