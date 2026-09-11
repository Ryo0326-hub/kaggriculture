# Cycle 13 — Majkel1337, Gekkotron and the remaining competitive gap

September 11, 2026. Seven user-supplied episodes, read passively without replaying actions through a simulator. Rankings and Gekkotron's approximately 2760 rating were supplied by the user; these files do not establish a current leaderboard snapshot. Four selected wins are not an estimate of Majkel's overall win probability. A 3000 rating is a target, not a forecast or guarantee.

## Recorded results

| Player | Episode | Opponent | Own final coins | Opponent coins | Margin | Peak productive tiles | Confirmed wages |
|---|---|---|---:|---:|---:|---:|---:|
| Majkel1337 | 107972592 | ymg_aq | 91,583 | 81,921 | +9,662 | 73 | 4,929 |
| Majkel1337 | 107968626 | Unknown Mother-Goose | 125,915 | 123,730 | +2,185 | 74 | 4,929 |
| Majkel1337 | 107968632 | SpaTaro | 89,087 | 81,136 | +7,951 | 74 | 4,874 |
| Majkel1337 | 107964504 | SpaTaro | 147,606 | 141,413 | +6,193 | 74 | 4,929 |
| Majkel1337 | 107932236 | feel the agi | 113,841 | 118,804 | −4,963 | 73 | 4,929 |
| Gekkotron | 107970619 | Subin An | 66,698 | 65,802 | +896 | 75 | 3,630 |
| Gekkotron | 107974608 | kyy666 | 135,532 | 138,354 | −2,822 | 75 | 4,939 |

The two bots in each episode share one market; raw coins across different games are not a controlled comparison. In particular, Gekkotron's 135,532 is not evidence that it is stronger than Majkel's 91,583.

## Majkel's observable policy

**A repeatable opening, followed by adaptive production.** All five games begin with a cow and five wheat, followed by a second cow, three sheep and four hires. Animal installation, feeding and care precede most crop activity. It orders twelve melon seeds in every game and realizes twelve six-unit melon harvests at age ten. Early cash sometimes falls to roughly 17–25 coins around observation 72. This is aggressive reinvestment; it does not prove that a near-zero reserve is safe for our different dispatcher.

The first land purchase succeeds at decision step 149 in all five games. The next succeeds at steps 217–223. Majkel therefore opens its third quadrant earlier than Gekkotron, whose land purchases occur at steps 150 and 265 in both games. These are zero-based decision steps, not display-day labels.

**A highly consistent staffing schedule.** Majkel starts with four paid hands, progresses through six, eight, nine and ten, and generally uses eleven from day index 10 through 27. There are 285–286 accepted hires over a season; requested hire counts are sometimes greater. Eleven paid hands cost 232/day; the next hand alone costs 144. Its 73–74 productive plots are serviced by twelve units including the farmer for much of the season.

**Wheat is working capital, feed and renewable production.** The five games contain 257 verified daytime wheat harvests of five units at age three. Ordinary wheat harvested at age three has at most three units after watering, so these five-unit harvests demonstrate fertilizer-supported growth. Both earlier two-unit harvests and later age-four harvests also occur. Majkel is not following a universal 'always wait for six' rule. Releasing a plot earlier can finance inputs and start the next planting sooner; maximizing one harvest's yield is a different objective from maximizing season cash.

**Production responds to the town.** Across the five games, requested seed quantities vary from 29–47 strawberries, 0–81 carrots and 0–8 tomatoes, while wheat remains substantial. In the milk/strawberry-heavy town in 107964504 it requests thirteen cows, forty-seven strawberry seeds and no carrots. In 107972592, two PET_CAFEs and two YARN_STOREs accompany more carrots and sheep, with geese present as well. Observed behavior supports demand adaptation, but does not reveal the exact formula or prove that every purchase was optimal. Purchase requests and per-type peak counts are not equivalent to simultaneous installed herd size.

**Animals support both products and fertilizer.** No fertilizer purchase orders appear in these five Majkel games. It collects animal fertilizer, applies some to crops and sells the remainder. Fertilizer is not free: applying it sacrifices its sale value and takes worker actions. Buying an animal for fertilizer alone eventually encounters fertilizer oversupply, feed expense and service costs.

**It is not operationally flawless.** Animals disappear in all five games; some disappear late enough to be intentional retirement, while others still contain output. Without its source, intent is unknown. The loss to feel the agi occurs despite Majkel's lower wage bill: the rival pays 8,052 and wins. A hard rule to minimize wages cannot be the whole strategy.

## What Gekkotron changes about the diagnosis

Gekkotron also fills three quadrants, grows substantial wheat, combines livestock and crops, and fertilizes strawberries. Large farms and mixed production distinguish this group from our earlier small-footprint submissions, but **do not by themselves distinguish Majkel from these opponents**: the seven opposing farms also reach 74–75 productive tiles.

Gekkotron's requested crop purchases are identical in its two games: twelve melons, 163 wheat, thirty-three strawberries and thirty-one carrots. It adjusts its livestock mix and staffing, but this pair is consistent with a more fixed crop schedule than Majkel's. One game has no carrot-buying shop at all. Majkel's more variable crop menu is a reason to retain and extend our visible-demand investment rules, not copy either bot's quantities.

Gekkotron's verified wheat harvests are mainly two units at age two, three at age three, or four at age four. Neither game contains a verified five-unit age-three wheat harvest. It buys 36–46 fertilizer units and issues 61 fertilizer actions per game, versus Majkel's 148–181 fertilizer actions. These are different input-allocation choices, not a general proof that every fertilizer application pays.

The most informative comparison is **Gekkotron versus kyy666, episode 107974608**:

- All **719 farmer/hand decision sets are identical**.
- All **719 non-sale market order sequences are identical** after removing empty placeholders and SELL orders.
- Confirmed daytime harvest totals match for every product, wages are 4,939 each, and both finish with empty sheds, carries and seed stocks.
- Sale orders differ. Gekkotron finishes **2,822 coins behind**.
- Accumulated saleable-product shed stock is 5,364 unit-turns for Gekkotron and 2,695 for kyy666, excluding wheat, fertilizer and animals. This measures inventory waiting in the shed, not price-weighted wealth or a fitted causal coefficient.

This pair isolates market decisions unusually well: physical commands and non-sale order sequences do not explain the final gap. Order timing/quantities and their shared-price consequences matter. It does **not** prove that immediate sales always win, or that the bots have identical source code. Our existing policy already promptly sells available surplus, so that behavior is preserved. Adding an unverified stockpiling rule would move away from this evidence.

## How our candidate adapts the existing strategy

The source remains a reproducible extension of Cycle 12, which itself extends the protected Cycle 3. It preserves the existing joint opening, crop-worker dispatcher, carrot input assignments, strawberry fertilizer timing, shared shed ledger, feed reservations, surplus sales and final-day delivery logic.

Changes respond to specific constraints in our code:

1. **Stage livestock space with land ownership.** Five animal sites leave twenty starting crop sites. Seven additional animal sites become available in the northeast quadrant. This replaces the reservation of ten starting animal sites, many of which remained empty during the opening. The herd ceiling becomes twelve, and total land remains capped at three quadrants.
2. **Keep our opening, add four cheap wheat seeds.** The normal opening remains eight melons, two cows and two sheep; wheat uses free crop space. This does not reinstate Cycle 10's replacement of melons with wheat, which failed earlier comparisons.
3. **Apply our existing insertion-tour method to livestock.** A producing animal's harvest is charged as work, without automatically assigning it a dedicated full-day worker. Actual hiring also accounts for crop work and pending seeds. The candidate ceiling is twelve workers including the farmer; it is a design bound, not proof of the optimal crew.
4. **Price production against demand, rival supply and scarce labor.** Compare discrete animal/crop/land batches with two conservative demand/supply scenarios. Include the price impact on our existing output and discrete extra wages. Tomatoes and carrots require visible shop demand. Geese now participate in the actual purchase menu alongside cows and sheep.
5. **Accelerate selected wheat turnover.** Five-unit wheat at age three may be harvested if another full wheat cycle can still fit; late-season wheat retains the existing completion/salvage rules. Tomato watering, repeated harvests, fertilizer opportunity cost and exhaustion are implemented too.

Full implementation details, limits and the CO connections are in [CYCLE_13_OPTIMIZATION.md](CYCLE_13_OPTIMIZATION.md). This is a complete runnable challenger, not a demonstrated 3000-rated agent. Its performance must be judged from its own Kaggle episodes.

## LLMs, trained models and compute

The replays cannot establish whether either author used an LLM to write code, an optimizer to tune parameters, a learned value function, or entirely handwritten rules. A repeated opening and stable action patterns are compatible with a deterministic policy or template followed by adaptive calculations. They are also compatible with several learned systems. There is no direct evidence here of an LLM making each move or of any particular training method.

This candidate uses standard-library Python and deterministic economic heuristics. It makes no API calls and needs no training, GPU or Featherless key. Keep the $0 compute budget. A later learned value model would need a defined target, enough diverse server evidence and separate validation; seven selected games do not supply optimal-action labels.

## Reproducible evidence and limitations

[Passive analyzer](../scripts/study_recorded_games.py), [Majkel data](benchmarks/cycle-13-majkel-study.json), [Gekkotron data](benchmarks/cycle-13-gekkotron-study.json), [opponents](benchmarks/cycle-13-opponents-study.json). Source hashes are recorded for each supplied replay. The analyzer imports neither the engine nor an agent, and never advances state.

Wages use observed changes in accepted hires; there are no unresolved overnight hire requests for the two focal players. Harvest totals use verified within-day increases in carried products and are explicitly lower bounds: overnight collection and unusual same-tile action interactions are not reconstructed. Seed/order quantities under `requested_orders_not_fills` are requests, not executed trades. Gekkotron frequently uses oversized SELL quantities; summing those requests would grossly overstate actual sales. Crop-to-weed counts include exhausted crops and cannot be labeled crop losses wholesale.

Mechanics were checked against the installed, pinned kaggle-environments 1.32.7 engine, source SHA-256 `bc8a54879ef02c7ea64b8b333d6a976f0ea65c4949149d01f463f23bccee653e`. Our agent consumes only the current observation/configuration, own private stocks and public farms/market/town. Replay IDs, hidden seeds and future states are absent from its source.
