# TPU P1 owner reachability and complete outcomes

Each row uses the same TPU P1 route, target 13679, local target pin 2 and owner pin 1. Before installing the local witness, the original owner branch is a directed feasible path in the jointly pruned state for every row. After installation, the historical searches exhausted. The counterfactual retains a disconnected target.

| Rank | Owner | Constructor | SOURCE seed (layer) | First OPIN | Witness exit | Free OPIN successors after reservation | Visited |
|---:|---:|---|---|---:|---:|---:|---:|
| 0 | 6335 | cross-layer | 634030 (1) | 634081 | 974548 | 10/16 | 1,589,166 |
| 1 | 6321 | rank sweep | 648136 (1) | 648284 | 974487 | 0/16 | 2 |
| 2 | 6381 | rank sweep | 270726 (0) | 270874 | 974485 | 0/16 | 2 |
| 3 | 6382 | rank sweep | 270727 (0) | 270875 | 974491 | 0/16 | 2 |
| 4 | 6387 | rank sweep | 270732 (0) | 270880 | 974550 | 0/16 | 2 |
| 5 | 6390 | rank sweep | 270735 (0) | 270883 | 974489 | 0/16 | 2 |
| 6 | 6320 | rank sweep | 648135 (1) | 648283 | 974552 | 0/16 | 2 |
| 7 | 6328 | rank sweep | 648143 (1) | 648291 | 974554 | 0/16 | 2 |

The SHA-256 of build_escape_owner_bfs_cross_layer_dev_01.py is 73913a9696a85635ab6b0963c0447805d63edb2e63cca6eb136f4162d5f57745. The SHA-256 of build_escape_owner_rank_sweep_dev_01.py is f47f758fe2c684a004cd05582f76afa1adff5808ae310664ca48df8b8704bf50. Both searches seed every retained owner node, follow directed edges across layers, skip already visited nodes and full nodes, and terminate on exhaustion in these runs. The source can reach its sole OPIN in all eight cases. For ranks 1–7, every outgoing OPIN choice is full. Rank 0 reaches ten free successors from its OPIN. Independent probes identify a sink-side constraint for its original exit and the tested pair of owners.

TPU_OWNER_FRONTIERS.json binds the ranked inputs and both source digests, gives the exact retained target nodes, witness node path, owner seed and pre-reservation path, and lists every immediate frontier holder. The original failure receipts themselves omit argv and the duration. Rank attribution uses the original sweep index, per-rank directories and registration, with the current route used to check each frontier.

## Target branch exchange

Rank 1 is the first two-node frontier where a retained target node also blocks the owner outside the local target witness. The target’s remote branch held 1055704. Reconstructing that branch as well frees 1055704 for owner 6321, while the local target takes 974487. Native reconstruction of the same three pins preserves the original owners. The local witness, owner reconnect and remote target reconnect form a single construction strategy.

| Same-root role | CPD (ns) | Wire | SB | CB | Setup better/worse vs root | Increased hold violations | Original resource decision |
|---|---:|---:|---:|---:|---:|---:|---|
| Unrestricted native | 7.667241952 | 337855 | 78 | 7584 | 0/0 | 0 | Reject, no improvement |
| Target branch exchange | 7.667241952 | 337855 | 79 | 7582 | 0/0 | 0 | Reject, SB cap 78 |

Both routes pass native FULL, fresh STA and physical checks. The comparison includes 34,293 setup and 34,293 hold components. The structural construction receipt records 6.881 s including preparation. Its separate observation command took 41.387 s. The native transaction command took 113.304 s including its source serialization control and validation. These timings cover different work. Historical failed-search process time and complete historical screening time are unknown.

The new owner and target each use one SB and zero CB sources. With the exit transferred, all eight direct cross-layer exits of the target OPIN are occupied by other nets, including the owner using 1055704. A different intervention can select a third net specifically for its ability to free a direct crossing and reconnect without consuming the saved SB. The other seven holders and their RR nodes are listed in TPU_BRANCH_EXCHANGE_PAIR.json.
