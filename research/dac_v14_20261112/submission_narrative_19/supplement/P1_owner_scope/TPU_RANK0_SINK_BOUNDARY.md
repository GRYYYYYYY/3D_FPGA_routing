# Sink-side boundary for TPU P1 rank 0

Owner 6335 pin 1 terminates at SINK 270606. Its sole directed predecessor is IPIN 270754. That IPIN has fourteen distinct incoming channel nodes. In the historical two-net prune with target 13679's local witness installed, each has capacity one and one occupant. The IPIN itself has spare capacity. This explains how the owner can reach 1,589,166 nodes and still miss the sink.

| Predecessor | Occupant | Predecessor | Occupant |
|---:|---:|---:|---:|
| 974510 | 7360 | 974511 | 7416 |
| 974516 | 6344 | 974517 | 18604 |
| 974522 | 7353 | 974523 | 7412 |
| 974548 | 13679 (installed witness) | 974549 | 7934 |
| 974554 | 6328 | 974555 | 7362 |
| 974560 | 6323 | 974561 | 7988 |
| 974566 | 6325 | 974567 | 7989 |

The enumeration decodes incoming edges in the bound RR graph for the sink and its IPIN. For each predecessor it counts distinct nets in the original route, removes the pruned branches, preserves retained nodes, and installs the recorded witness. The complete original owner path in TPU_OWNER_FRONTIERS.json reaches the sink before the reservation. Removing both owner branches and reserving the other exit instead was already tested for the 6335/6328 pair. This table applies to the single-owner rank-0 residual graph.
