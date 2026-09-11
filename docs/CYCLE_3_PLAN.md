# Cycle 3 — fertilizer and harvest timing

Hypothesis, before experiments: Step 8 misses profitable strawberry fertilization after watering and when urgent watering bypasses the fertilizer branch. The engine accepts fertilizer after watering for overnight strawberry production; this does not retroactively boost wheat. A separate early-wheat-harvest comparison will price current receipts against the yield and prices lost by not waiting.

Keep the Step 8 investment functions, opening, hiring calculation, livestock routes and sale-price rules fixed. Different crop commands can change future cash, stock, market prices and therefore later decisions under those same rules; identical realized purchases are not claimed. Keep the exact Step 8 artifact as the reference. Develop outside `main.py`.

Screen at most three challengers: fertilizer timing, harvest timing, and both. Protect newborn watering, survival work, animal care, crop decay and final delivery. Fertilizer requires positive incremental value after its sale opportunity cost and action allowance. Do not spend fertilizer on capped output or production beyond the season.

First check action timing against the actual engine, including fertilizer before/after water, expiry and final-night boundaries. Run installed one/two/three-quadrant portfolios on development seeds 17/43 in both seats, with capital purchases disabled and executed cash/output accounting. Then run standard starts on those seeds against Step 8 and the larger mixed control. Carry out only justified bounded fixes for observed defects.

Freeze a clean promising candidate before an independent matched evaluation, using fresh seeds 9201–9220 in both seats against Step 8, scaled_mixed and expanding_mixed. Evaluate the reference on the identical pool. Inspect opponent-specific and whole-seed results, operational losses and runtime. Do not promote an unchanged, tied or materially regressing candidate. Record rejected variants if none qualify.

Local CPU only; no new spending. Preserve implementation notes connecting incremental revenue, input opportunity cost, scarce actions, and integer resource reservations. Save and push the verified work; a code push is distinct from a Kaggle submission.
