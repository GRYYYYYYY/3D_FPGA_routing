# Implementation and evidence plan

## Scope

Execute the analysis in this conversation, preserving all algorithm and evaluation stages. Do not treat a working toy router or a baseline smoke test as completion. A positive performance result is not assumed: measured negative results must also be retained.

## Required stages

1. **Pinned reproducible baseline (complete: pinned baseline and 25-circuit workload prepared).** Build upstream VTR, verify native 3D SB routing, archive versions, commands, architecture, packed netlist, placement, RRG and timing constraints. Start with two homogeneous layers and clustered, serial timing-driven routing.
2. **Resource semantics and instrumentation (complete: unit/oracle/real-graph checks and final matrix audits pass).** Index physical vertical channels, entry/exit RR resources and direction. Account for native CHANZ, legacy paired-node encodings, shared resources, and unique occupancy per net. Record vertical usage, overuse per iteration, connection delays, search work, reroutes and timing.
3. **A1 simple-cost control (implemented; pilot and screening matrices complete).** Add an independently switchable vertical resource cost, retaining baseline RC and PathFinder present/history costs. Verify disabled-mode equivalence.
4. **A2 reachable candidate guidance (BFS/SCC pilots and real-graph cross-checks pass; screening complete).** Generate diverse reachable candidates, include current channels, allow occupied channels with negotiated cost, and fall back to unrestricted baseline search.
5. **A3 tree-level planning (integrated; exact hierarchical oracle and cross-layer pilots pass).** Compare shared and split crossings with finite graph-valid candidates. Use a documented surrogate DP; report precomputation costs and do not claim exact global timing/Steiner optimality.
6. **A4 dynamic reoptimization (whole-net/subtree variants implemented; screening complete).** Replan on congestion/timing events; transactional replacement restores sharing, occupancy, timing and reroute requests after failure. Injected rollback passes native/scoped checks. This does not yet claim globally optimal subtree selection.
7. **Literature controls (two explicit adaptations implemented; pilot routes pass).** Static FLUTE XY guidance and an explicitly defined potential-field/sink-order control are described in `literature_controls.md`. Neither is labeled an original-paper reproduction; PathSteiner's full code was retrieved, while the other paper's detailed formula/code remains unavailable.
8. **Validation and experiments (complete).** Independent resource/connectivity checks; known-solution congestion cases and small exact-oracle cases; no-guide equivalence; fixed placement/RRG paired experiments across density, spatial distribution, access fan-in/out and delay; 3–5 pilot circuits followed by the available 20-circuit set and representative different workload types; multiple paired placements/seeds; retain failed/time-limited runs and all overhead.
9. **Analysis and reproducibility (complete; final tables, plots, manifests and reviewable patch delivered).** Summarize legality, success within budget, CPD, wirelength, unique vertical occupancy, runtime, memory, convergence and search effort. Attribute improvements using ablations. Separate algorithm effects from architecture/version changes and timing assumptions. Package build/run instructions, manifests, patches, checks and results.

## Scientific gates

- Every reported successful final route uses real directed RRG transitions and satisfies capacity/configuration constraints.
- Same-net branches sharing one channel count as one net occupancy; a path crossing, a graph node and a physical channel are different quantities.
- Candidate search failure is not a proof that the full graph is unroutable. Preserve fallback and failed runs.
- Shared trunks may change upstream load and critical delay. Use VPR's timing recalculation, not Manhattan distance or a fixed Z penalty as final evidence.
- Keep the graph and placement identical for the primary A0–A4 comparisons. Compare old tool branches separately unless equivalence has been verified.
- Any algorithm-specific preprocessing, planning, fallback and reoptimization time belongs in the reported runtime.
- Fixed-fabric resource usage reductions are not fabricated-area reductions.
- If A4 does not outperform tuned A1/static tree controls, report it; do not claim an unmeasured benefit.

## Sources

- H3D (ICCAD 2025): https://www.cse.cuhk.edu.hk/~byu/papers/C297-ICCAD2025-3DRoute.pdf
- LaZagna: https://github.com/sharc-lab/LaZagna ; https://arxiv.org/abs/2505.05579
- Multi-die VTR modeling (FPL 2026): https://arxiv.org/abs/2606.06421
- PathSteiner (FCCM 2026): https://www.shashwatshrivastava.com/documents/FCCM26_PathSteiner.pdf ; https://zenodo.org/records/19204522
- Steiner potential fields (FCCM 2026): https://doi.org/10.1109/FCCM68464.2026.00031
- Escaping Flatland: https://arxiv.org/abs/2604.01078 ; https://github.com/IY2002/Beyond-Flatland
- 3DPRO: https://doi.org/10.1155/2008/764942
- PathFinder convergence study: https://www.shashwatshrivastava.com/documents/FCCM25_Guaranteed_Yet_Hard_to_Find.pdf

## Activity

- 2026-10-22: Final evidence is complete: 769 formal route runs, 637 native successful and independently audited solutions, 132 retained failed runs, no timeouts. All 90 sequential timing runs pass; each of the 30 case/setting groups has three byte-identical routes. Paired input hashes and audit/run hashes match. A3 has conditional model-based CPD gains on the 12 jointly legal large-circuit cases; dynamic A4 has no stable overall advantage and one additional failed circuit. The tuned implementations are slower than tuned A1 in both controlled timing cases. See the Chinese report and generated result tables for scope and limits.

- 2026-10-22: All screening matrices are terminal. The native 20-circuit A0–A4 matrix has 71 completed and 49 failed runs, with no timeouts; static literature adaptations and pruning controls are also terminal. Independent audit batches cover terminal subsets without adding routing runs. Final timing uses 15 already-defined settings on two cases with three repetitions, fixed before timing begins. A CHANZ omission in native detailed timing reporting was repaired and validated without changing route/STA CSV results. Final release disabled/subtree/field routes match archived references.

- 2026-10-22: A4 whole/subtree modes pass the balanced ex5p fixture, including a forced rollback. The SCC reachability index passes 300 randomized all-pairs directed-graph oracle comparisons. Static SCC planning takes 0.300 s versus 2.948 s for BFS on this fixture, but geometric cost/sampling differs and total routing still exceeds baseline. The latest off mode reproduces the unmodified route exactly. Began the complete 20-circuit × 6-variant fixed-input screening matrix, including failed preparations when their packed/place/RRG files exist. Eight native-Z parameter settings on two fixed placements are being prepared. All concurrent runtimes remain screening evidence.
- 2026-10-22: Endpoint inspection found no remote sink connections in the three initial natural placements, despite CHANZ occupancy in two of them. Added a labeled balanced-layer fixture (39/78 ex5p CLBs moved at identical compatible sites). A0 and static DP both pass VPR FULL routing checks on this fixture; A3 performs 460 plans, visits 53.6 million BFS nodes, and spends 2.95 s in preprocessing/planning versus A0's 0.53 s total routing. The static result is therefore not a runtime improvement. Downloaded all 20 published Beyond-Flatland BLIFs at commit `84ba44acf1bad597bc5a9d1f615415870e178a86`; original hard-block models require an architecture compatibility adaptation, which must be documented rather than silently remapping primitives.
- 2026-10-22: Built and archived an unmodified baseline, then validated native CHANZ routing on ex5p/diffeq and a zero-crossing alu4 control. Added a streamed independent directed-edge/tree/capacity audit (9 failure-injection cases). Completed 18 sequential paired A0/A1 route-only runs: all off/zero modes match the unmodified routes exactly; 17 routes pass native/scoped checks, while ex5p at weight 0.5 retains one overused node. A1 weight 2 uses 283/362 channels on ex5p/diffeq versus 323/490 baseline; broader tuning/generalization remains pending. Added a finite hierarchical sharing/splitting DP with 250 exact enumeration comparisons. The integrated candidate planner is being compiled and has not yet been validated on real routes.
- 2026-10-22: Inspected empty work directory and current execution environment. Upstream VTR master resolves to the previously reviewed commit `0b912334fdd83bb754b302146ac0d1ec9edc9a0e`. Started isolated source acquisition. Current container lacks CMake and VPR build dependencies; restoring build prerequisites rather than relying on a different project's historical environment record.

