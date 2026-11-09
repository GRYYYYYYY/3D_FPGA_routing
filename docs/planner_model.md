# Finite, graph-checked migration of the H3D idea

The implemented planning core deliberately limits its claim. It reuses the idea
of deciding whether multiple branches should share a vertical transition, but
does not transfer ASIC Manhattan-region convexity or global optimality to FPGA
routing. At present candidate modes support serial clustered routing on exactly
two stacked layers, without 2.5D cuts or shared bus-mux controls. A1's separate
CHANZ cost does not require this candidate planner.

## Feasibility before geometry

For a driver on die A and a terminal on die B, a native CHANZ candidate is included
only if a directed same-die forward search reaches it from the driver and a
reverse search reaches it from the terminal. Searches stop at CHANZ, so these
two halves certify a single-crossing walk in the original graph. Reverse edges
are only an index for analysis and never become available to the detailed router.
Candidates are not discarded because another net currently occupies them;
PathFinder negotiates congestion. Existing channels are included if feasible.

Reachability is computed in the whole RRG. It does not assert that a path stays
inside VPR's current net bounding box or is simultaneously conflict-free with
other nets. The detailed router still enforces the graph and its configuration
rules. A connection with no candidate uses the ordinary router, including paths
that cross more than once. Legacy paired CHANX encodings are not silently treated
as native CHANZ and need a separate verified import adapter.

## Finite planning objective

The core uses a deterministic spatial binary hierarchy over remote terminals,
formed by median splits along the larger x/y extent. This is a hierarchical
facility-selection surrogate, **not an exact FPGA Steiner-tree solver**.

For a subtree `v`, the recurrence compares:

```
D(v) = min(
    min over common reachable c: opening(c) + sum(branch_cost(i,c), i in v),
    D(left(v)) + D(right(v))
)
```

The opening cost includes source-to-channel hop distance and the channel's
normalized present/history congestion cost. Branch cost includes channel-to-sink
hop distance and a criticality-weighted source/sink term. The DP counts one
opening for a shared group. It sums downstream branch proxies and therefore
does not model their detailed shared wires, switch loading or RC delay exactly.
Its optimality applies only to the supplied candidate table, hierarchy and
surrogate. Tiny tests enumerate all hierarchical partitions and candidate
assignments independently to check this limited claim.
Opening is charged per hierarchical group, not once globally for every channel
identity across unrelated groups. Actual same-net physical occupancy is instead
deduplicated in VPR's route tree and in the independent resource audit.

The router applies a nonnegative extra congestion preference to unselected
CHANZ resources. It retains all resources, VPR's negotiated congestion costs,
actual switch/segment timing, and normal route-tree timing refresh. A failed
guided sink search retries without the guide before ordinary bounding-box
recovery. Guided planning is allowed to produce a worse measured result.

## Ablations

- `VPR_H3D_MODE=off`: original search, with optional independent A1 vertical cost.
- `candidates`: cost-ranked, spatially diverse reachable candidates per terminal.
- `static`: compute the finite shared/split DP once per net; keep its preference.
- `dynamic`: replan when VPR has already selected a net for congestion/timing
  rerouting; reuse VPR's normal whole-net/incremental policy.
- `dynamic_whole`: explicitly rip up the selected net's complete previous tree.
- `dynamic_subtree`: apply VPR's congestion/timing subtree pruning even below
  its normal incremental-fanout threshold. Retained legal branches remain owned
  by this net. This is selective rerouting, not a globally optimal cut search.

The last two modes snapshot a complete prior signal-net tree and consumed
reroute requests. Failure after the ordinary unrestricted retry restores the old
tree, subtracts/adds the appropriate occupancy, recalculates timing, restores
CBRR/hold/skew requests and invalidates affected pin timing. A restored tree may
still be congested; the global VPR checker decides feasibility. The explicit
`VPR_H3D_TEST_ROLLBACK_ONCE=1` injection rejects one completed replacement and has
passed the native FULL checker and independent scoped audit.

## SCC acceleration ablation

`VPR_H3D_REACHABILITY=scc` replaces repeated whole-die BFS with a condensation
DAG of exact same-layer directed non-Z edges. A candidate is feasible when its
real predecessor component is reachable from the source and its real successor
component can reach the sink. No reverse edge is added to the router. A generic
300-graph randomized test compares all reachability pairs against independent
Floyd–Warshall closure, in both directions.

This variant changes more than data structures: it samples candidates near
endpoints, their interpolated points and the net centroid, and uses Manhattan
distance divided by mean planar segment span plus a fixed hop offset as its
cost proxy. It scans the full channel table when the spatial sample contains no
feasible candidate. It includes feasible prior channels and allows occupied
channels. Retained own-net occupancy adds zero prospective demand. More than
128 remote sinks uses independent candidate guidance, with a reported fallback
counter. Thus SCC results are not claimed to equal BFS-distance optimization.

The reference BFS opening cost uses the native prospective congestion function;
the SCC variant explicitly avoids charging retained own-net demand twice. The
planning counter in the archived SCC binary includes zero-remote nets, whereas
the BFS counter counts only remote-net plans; use measured time and endpoint
counts for comparisons, rather than equating these two counters.

`VPR_H3D_CANDIDATES` defaults to 8, `VPR_H3D_MISS_WEIGHT` to 2,
`VPR_H3D_OPENING_WEIGHT` to 8. These are experimental settings needing tuning,
not derived technology constants. Reachability caches, reverse indexing and DP
time are included in process runtime and separately counted by `H3D_PLAN`.
