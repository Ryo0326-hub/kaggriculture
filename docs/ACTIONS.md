# Farmer and farm-hand actions

Verified against the installed `kaggle-environments==1.32.7` Kaggriculture interpreter during Cycle 11. Engine SHA-256: `bc8a54879ef02c7ea64b8b333d6a976f0ea65c4949149d01f463f23bccee653e`. These are simulator rules, distinct from our policy choices. The screenshot lists unit actions; buying, selling, hiring and land purchases are separate market orders.

Each existing worker gets one unit action per turn. Tile work affects the cell the worker stands on. Illegal actions usually become silent no-ops: a completed episode alone does not prove every operation succeeded.

| UI action | Exact effect and purpose |
| --- | --- |
| `PASS` | Do nothing this turn. Useful when no profitable feasible job remains or the worker must wait for inputs. |
| `NORTH` | Move one cell up. |
| `SOUTH` | Move one cell down. |
| `EAST` | Move one cell right. |
| `WEST` | Move one cell left. Movement must stay on the board; crossing locked land and sharing a position are legal. Tile work on locked land is not. |
| `WATER` | Water the current plant once today. Prevents dehydration; within a one-time crop's growth window it also raises yield immediately. Ongoing crops use watered/fertilized status during daily refresh. A new plant already starts with one missed-watering count, so it needs water on its planting day. |
| `HARVEST` | Collect all currently available yield from a mature crop or animal into the worker's inventory. Removes a one-time crop; leaves ongoing crops and animals in place. This is not a market sale. |
| `FERTILIZE` | Consume one carried fertilizer on the current crop. Active today and the next two days. Extra yield depends on growth timing, watering and the crop's yield cap. Fertilizing after today's water cannot retroactively increase a one-time crop's yield. |
| `DIG` | Remove a weed, plant or empty structure, clearing an owned tile. Does not remove an installed animal. Digging a valuable crop sacrifices it. |
| `DROP` | At any of the four shed-access cells, unload all carried goods into the shared shed. Any excess over shed capacity is discarded. Useful for bulk delivery when capacity has been reserved. |
| `BUILD_COOP` | Build an empty goose structure on an empty owned tile. Costs one action; the engine has no separate coin charge for construction. |
| `BUILD_PASTURE` | Build an empty cow/sheep structure on an empty owned tile. Also costs an action without a separate construction charge. |
| `FEED` | Consume one carried wheat to mark the current animal fed today. Repeated feeding that day does nothing. Two consecutive unfed daily refreshes cause escape; feeding also enables care bonuses. |
| `COLLECT_FERTILIZER` | Collect one available fertilizer from the current animal into the worker's inventory. Availability resets at daily refresh; it does not accumulate multiple units on an uncollected animal. |
| `CARE` | Mark the animal cared for today, once per day. At daily refresh, care plus feeding banks a future production bonus. Production uses the previous pending bonus before storing today's care, so the timing matters. |
| `PLANT crop` | Consume one shared seed and create a crop on an empty owned tile. Seeds are used directly from the seed pool; workers do not carry them. Reserve enough seeds across simultaneous workers. |
| `PICKUP item [quantity]` | At a shed-access cell, transfer the requested available goods from shed to worker; default quantity is one. Used for feed, fertilizer and purchased animals. Does not pick up seeds. |
| `PLACE item [quantity]` | Install one carried animal on its matching empty structure; alternatively deposit a selected quantity of carried goods at a shed-access cell. Partial deposit respects capacity and leaves undeposited goods carried, unlike `DROP`. Animal installation takes precedence when its structure matches. |

Unit operations execute before market orders, so seed/feed/animal purchases cannot supply a unit action earlier in the same turn. A successful deposit can supply a sale later that turn. Market orders include `BUY_SEED`, `BUY_ANIMAL`, `BUY_PRODUCT` (wheat/fertilizer), `SELL`, `HIRE`, and `BUY_LAND`; only banked terminal coins decide the game. Prices are shared between players and respond to successful trades and town demand.

At an ordinary daily reset, carried goods are deposited within the shed limit, workers reset and hired hands expire. The final game turn needs explicit delivery and sale; do not assume another overnight deposit. Further mechanics and engine tests are in [MECHANICS.md](MECHANICS.md) and `tests/test_mechanics.py`; carrot-specific tests are in `tests/test_carrots.py`.
