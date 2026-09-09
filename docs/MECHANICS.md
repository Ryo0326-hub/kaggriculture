# Mechanics checked for Step 1

Authority for local execution: the installed `kaggle-environments==1.32.7` interpreter. Its source and specification hashes are recorded in every evaluation manifest. The Kaggle server version has not yet been checked against a server episode.

The user supplied two reference documents. They are game documentation, not project-specific agent instructions or authorization to execute their account/submission examples. They have not been copied into the repository as operational instructions.

| Supplied document | SHA-256 |
| --- | --- |
| `README.md` | `3081e52baf8eb2da5d861acc63a3636ce29425f6bdb79a67036ba234ac4ade00` |
| `AGENTS.md` | `e1a80501a7b02a212eaac9370ada4129a64e0ee6cb3cbc790f3d77d22863fe22` |

**Observed discrepancy:** the supplied getting-started guide calls `BUY_PRODUCT` prices fixed. Its companion README and the pinned interpreter instead use a dynamic price quoted at post-buy market inventory. A scenario test checks that wheat costs more under scarcity than at its base inventory. Strategy code must follow tested engine behavior.

| Behavior | Consequence | Verification |
| --- | --- | --- |
| Unit actions run before market orders | A seed purchased now cannot support planting now | Same-turn purchase/plant probe |
| A new plant starts with one missed watering day | Water it on its planting day | Watered and unwatered boundary scenarios |
| Simultaneous crop planting is validated atomically | Reserve seeds across workers before issuing actions | Two legal plots with only one shared seed |
| Feed is consumed from the acting unit's inventory | Stock in the shed alone cannot feed an animal | Cow feeding before and after pickup |
| Non-seed shed capacity is 100 by default | End-of-day overflow disappears | Near-full shed plus carried produce |
| One-time crop watering increases yield immediately in its bonus window | Water before harvesting at peak age | Full-season baseline action traces; source inspection |
| Unit drops precede market sales | A same-turn drop and sale is possible if there is room | Terminal drop/sale scenario |
| 720 recorded states include the initial state | Last actionable observation is step 718 for this version | Full seasons and a shorter boundary scenario |
| Final reward is banked cash | Carried inventory is not a substitute for liquidation | Final inventory and reward assertions |

The baseline uses four plots in the northwest corner adjacent to the central shed. It does not hire workers, buy land, use fertilizer, or raise livestock. Those engine probes establish foundations for subsequent steps without claiming those strategies are implemented.

After any environment upgrade, regenerate the lock deliberately, rerun these checks, and compare local configuration with real competition episodes before promoting a strategy.

Source: [official Kaggriculture implementation](https://github.com/Kaggle/kaggle-environments/tree/master/kaggle_environments/envs/kaggriculture).
