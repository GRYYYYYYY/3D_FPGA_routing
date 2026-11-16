# H3D-inspired native 3D FPGA routing

## Current research snapshot — 2026-11-16

Research remains active, with public evidence base `9734eee`. Use the [current status and evidence index](research/dac_v14_20261112/CURRENT_STATUS.md) for captured process identities and receipts. Completed batches are reused; local updates and original experiment rules are preserved.

The unified method selects groups using current STA, applies retained-crossing sharing domains, releases a failed network's domain, and expands stalled scopes using capacity-certified owners and current timing margins. It accepts complete legal transactions under fixed root envelopes, then performs independent terminal selection and current-STA timing repair. Intermediate states need not each improve CPD. The [dev03 package](research/dac_v14_20261112/standalone_unified_method_component_03.json) is fixed for its registered development runs; whole-entry execution has passed on an existing tiny input; [CP1 source and rules are now frozen](research/dac_v14_20261112/confirmation_release_cp1_01/completion.json), with23 admission checks and actual full-bundle relocation validation. Positive integrated paths and independent confirmation outcomes remain pending. Existing development runs are not retroactively confirmation.

[Current six-page paper](research/dac_v14_20261112/paper_snapshots/current_owner_contract_20261116/build/current_repair_main.pdf) · [Source and evidence binding](research/dac_v14_20261112/owner_contract_paper_binding_09.json) · [New complete results and continuation](docs/GitHub_CP1_progress_20261116.md). The main table separates31complete attempts (4initial routing failures and4input-loading failures) from2scoped component rows. CP1 and the robot owner scope tradeoff are integrated. BNN whole costs, robot-SDC no gain and attention failures are integrated; local trajectories and recovery audits stay in the supplement.

| Original complete BNN configuration | CPD (ns) | Wire | SB | CB | Complete time (s) |
|---|---:|---:|---:|---:|---:|
| Native | 13.228145690 | 2059631 | 82 | 5062 | 7933.25 |
| Domain-first | 13.228145690 | 2061417 | 43 | 5060 | 9754.31 |

These matched configurations trade 1786 wire and approximately 22.95% more complete time for 39 SB and two CB. SB alone falls 47.56%; total SB+CB falls approximately 0.797%. Domain-first improves 534 setup components and regresses 803, with no increased hold violation. These are occupancy reductions on a fixed architecture, not measured silicon-area or power savings. [Full paired evidence](research/dac_v14_20261112/complete_resource_timing_full_flow_01/comparison.json).

Mechanism evidence remains scoped: a fixed three-net BNN composition saves 24 wire with unchanged CPD and two improved setup components; disabling only failure release in robot fails and restores the source exactly. R1 owner repair produces the same result in native and domain arms, supporting expanded coordination scope rather than an additional domain benefit. Recorded transfer outcomes retain conv-layer initial routing failures, SPMV/CB-only no-cut cases, softmax equal quality, SB-only strict-mode no gain, and robot's wire/CB tradeoff.

The [complete terminal-wire BNN comparison](docs/GitHub_complete_inputs_progress_20261116.md) is verified: 13.228145690 ns,2059607 wire,82 SB,5062 CB and7351.26 s. The exact shared resource prefix is preserved; final wire falls24 with2setup improvements and no regression versus the closed-stream native baseline. GNU-time7351/7247 s is104 s higher; old observer/PSS loss and overlap remain. This is a same-input quality/cost tradeoff, not acceleration. Sampled PSS is11.063 GiB with24missing observations.

The new robot-SDC pair starts at identical routes/vectors on a known, actually different placement. Both retain12.727250365 ns,250411 wire,2 SB,526 CB and unchanged full endpoints at498.00/504.09 s. Neither finds a sharing or owner cut; a faster timing candidate exceeds fixed resource caps. Attention fails initial routing in both arms (200iterations,231overused nodes), costing794.67/792.69 s. Failures remain in the denominator; a pair is one physical input, not two independent samples.

Portable observation, a known R1 nonempty owner transaction, and the existing tiny whole-flow execution have now passed outside the project. These checks add no independent input or frozen-controller confirmation. The clstm pair ended before routing: its template omitted the historical constant-net interpretation option and native loading reported a `$undef` mismatch. These are input-compatibility failures, not algorithmic routing failures. Original receipts are preserved. Robot owner-scope has now completed:31setup improvements for12extra wire and1extra CB versus target-only at equal CPD; fixed resource acceptance rejects both, with no actor commit. The shared imported pair costs155.10 s, not a complete cold flow. Robot p1 also failed before routing on the same missing input option. The domain engineering arm now runs, followed by reduction_layer and separately corrected input pairs. A separate [corrected clstm input pair](research/dac_v14_20261112/clstm_input_contract_pair_02/plan.json) is appended after them, with unchanged dev03 and matched input flags; actual execution remains pending. See [current actual processes](research/dac_v14_20261112/CURRENT_STATUS.md) and the [reduction plan](research/dac_v14_20261112/portable_reduction_pair_01/plan.json); existing registered rules and owners are unchanged.

The [domain engineering arm](docs/GitHub_domain_engineering_registration_20261116.md) applies the completed native single-pass/cache/stream implementation with the original domain rules. The earlier native observation has qualified GNU-time only, with observer loss, a full PSS gap and brief overlap. The [terminal-wire completion comparator](docs/GitHub_terminal_comparison_progress_20261116.md) preserves these limitations and compares matching GNU-time scopes after actual completion. The qualified terminal comparison and pending domain arm do not revise the original22.95% overhead; stable same-environment interleaved timing remains pending.

[First prospective CP1 cross-circuit cohort](research/dac_v14_20261112/cp1_cross_circuit_cohort_01/plan.json): conv_layer_hls and tpu_like.small.ws, two different known circuits and four matched arms, registered before CP1 outcomes. Both historical success and failure inputs are retained. Actual frozen admission checks pass; large physical provisioning and native runs wait behind corrected robot p1 under the shared serial lock. Registration adds no completed independent result and changes no existing batch. [Registration and live-owner evidence](docs/GitHub_CP1_cohort_progress_20261116.md).

[Robot composition screen](docs/GitHub_robot_composition_screen_20261116.md): same-root sharing and owner candidates overlap two requested connections; sharing's32 regressed setup components do not overlap owner's31 improved components. Existing scalar gains cannot be added into a claimed combined route. A union request needs fresh capacity/FULL/STA validation; no new native result or CP1 rule change.

[Executable robot union experiment](docs/GitHub_robot_union_registration_20261116.md): three matched treatments on the25-connection union isolate domain and failure-release effects inside a fixed coordination scope. Eight development checks pass; the single owner waits after the CP1 cross-circuit cohort. No new native outcome or change to frozen CP1.

<details>
<summary>Historical progress snapshots and earlier paper versions</summary>

The following entries retain their original publication-time wording. Their running/pending labels are historical; use the current status link above for continuation.

## Current snapshot — 2026-11-15 (research active)

[Current six-page manuscript and native ablations](docs/GitHub_native_ablation_progress_20261116.md): the fixed BNN three-net composition passes native FULL/STA and independent physical checks; robot no-release fails with exact rollback. The unified table retains 22 complete-flow rows and adds two explicitly scoped component rows, without attaching old whole-flow costs. [Current PDF](research/dac_v14_20261112/paper_snapshots/current_native_ablation_20261116/build/current_repair_main.pdf) · [Evidence binding](research/dac_v14_20261112/native_ablation_paper_binding_06.json). Complete terminal-wire BNN is running; full frozen-controller confirmation remains pending. Its [qualified completion comparison](docs/GitHub_terminal_comparison_progress_20261116.md) is registered to preserve the old observer loss and compare GNU-time on matching scopes.

[Prospective fixed-dev03 robot p1 pair](docs/GitHub_robot_p1_registration_20261116.md): verified different actual packing and block-coordinate mapping from modern robot p0, with the same circuit and architecture. Two full-method arms share dev03 and owner opportunities, start fresh routing and are queued after existing work. No native execution or new independent outcome yet; known historical input, not an unseen holdout.

[Missing domain engineering arm registered](docs/GitHub_domain_engineering_registration_20261116.md): apply the completed native single-pass/cache/stream implementation to the original full domain configuration after existing cross-input work. No repeated native batch or changed algorithm rule; no new result or revised overhead claim yet.

Earlier [routing contribution comparison](docs/GitHub_routing_position_progress_20261116.md) added five primary references (nine total), credited prior incremental/current-timing routing and separated imported price resets from unvalidated CHANZ scope.

[Robot owner-scope continuation](docs/GitHub_robot_owner_scope_progress_20261116.md): 18 actual residual-capacity queries separate two target-only no-path cases from 16 owner-release local-path cases. A fixed same-root 3-connection/4-connection unrestricted native contrast is queued after existing work; owner reconnection, complete legality and timing remain unverified. [Current concise status](research/dac_v14_20261112/CURRENT_STATUS.md).

[Earlier mechanism/input continuation](docs/GitHub_mechanism_inputs_progress_20261115.md): robot's exact retained-domain/capacity proof separates per-net release from outside-owner coordination. Six historical input records were screened, including one initial routing failure; no new full-method outcome is claimed. A fixed dev03 clstm native/domain pair is queued after the portable whole-method check. [Earlier six-page paper](research/dac_v14_20261112/paper_snapshots/current_mechanism_inputs_20261115/build/current_repair_main.pdf) incorporates the mechanism evidence, retaining the 22 measured rows and explicit pending-ablation limits; [evidence binding](research/dac_v14_20261112/mechanism_inputs_paper_binding_04.json).

Earlier snapshot: [completed results, conclusions and running experiments](docs/GitHub_progress_20261115.md), the [publication-time verified process state](docs/github_progress_status_20261115.json), and the [C221 six-page manuscript](research/dac_v14_20261112/paper_snapshots/current_R1_native_closure_20261115/build/current_repair_main.pdf). All eight original native/domain control menus are closed. New evidence includes 32-SB owner coordination, mixed circuit transfer outcomes, complete BNN costs and the verified single-pass-index full-flow comparison. Later results are explicitly separated from the manuscript's frozen archive and from trials still in progress. This remains a research snapshot, not a complete offsite raw-data backup.

Continuation from public evidence base `9734eee`: [unified-method progress and publication scope](docs/GitHub_unified_progress_20261115.md), [captured process state](research/dac_v14_20261112/CURRENT_STATUS.md), [reorganized six-page manuscript](research/dac_v14_20261112/paper_snapshots/current_unified_archive_20261115/build/current_repair_main.pdf), and [source/evidence binding](research/dac_v14_20261112/unified_archive_paper_binding_03.json). The 22-row main table binds complete costs and full endpoint changes, including two initial-route failures. The integrated development entry and four new paired roles are registered; full outcomes and frozen-controller confirmation remain pending. The completed same-flow cache/stream native control preserves actual quality and work at approximately 7247 GNU-time seconds; observer loss and missing complete PSS remain explicit. The separately packaged native runtime component has passed relocation tests and is not the whole algorithm. Recovery scheduling preserves surviving processes and never-executed tasks.

Latest continuation: [portable selectors, completed grouping controls and live queue](docs/GitHub_portable_selection_progress_20261115.md). Actual outside-project R1 replay preserves all eight owner groups, one sharing scope and STA selection; a no-cut tiny input remains empty. Three completed grouping roles preserve requests, endpoint vectors and route bodies, with no query-count reduction. BNN domain and registered follow-up roles continue. The complete independently executable confirmation method remains pending.

[Archive integration and measurement coverage](docs/GitHub_archive_scope_progress_20261115.md): [671 actual observations](research/dac_v14_20261112/multiobjective_closed_stream_quality_01/verification.json) now include the completed stream flow. There are 34 quality-complete configurations: 33 with complete observer measurements and one with qualified original GNU-time only. No missing PSS/observer wall/CPU is reconstructed; the six-page main distinguishes these coverage counts. These are not independent samples.

[Portable transaction development entry](docs/GitHub_transaction_entry_progress_20261115.md): actual outside-project two-arm owner protocol reconstruction, installed-candidate vectors/physical audit, five-connection request preparation and runtime/command preflight pass. Altered actual gates and wrong complete trees are rejected. No new VPR execution or independent sample is claimed; full method freeze remains pending.

The 2026-11-09 section below is historical.

</details>

## Historical snapshot — 2026-11-09

This repository preserves the current research code, source patches, experiment
protocols, selected evidence and handoff documents. The registered experiment
queue is still running on the original shared-storage environment; this is **not
a final experimental release or a complete raw-data backup**.

Read the [GitHub snapshot guide](docs/GitHub快照说明_2026-11-09.md) and
[current account handoff](docs/账号切换交接_2026-11-07.md) first. Current source
changes, including previously ignored vendor modifications, are preserved in
[verified source patches](patches/snapshot_20261109/manifest.json). The strict
study's [preliminary report](results/architecture_flow_20261027/serial_strict_reexecution_20261103/report.html)
predates the remaining fixed-placement width diagnosis and final acceptance audit.
Results are conditional: they do not establish general routing acceleration or
an architecture ranking reversal. Historical results below describe earlier
experiment matrices, not completion of the current strict study.

## Earlier experiments and project background

Research implementation of timing-driven vertical-channel selection and routing-tree reoptimization on a fixed FPGA routing resource graph (RRG).

For continuing this work in a new conversation, read the [2026-10-25 handoff](docs/交接说明_2026-10-25.md), including the distinction between paper-era LaZagna, its later VTR-9 code migration, and the native A0 baseline.

The [VTR-9-port build and controlled pilot](docs/LaZagna后续分支验证_2026-10-25.md) completed an explicitly patched VPR build, small-graph checks, and nine audited routes. The subsequent [three-baseline comparison](docs/三基线对比_2026-10-27.md) now adds full-size modern VPR PnR and paired native A0/A3 routing: 31 attempts, 30 routes passing FULL and independent audits, and one capacity failure causing two dependent skips. Under the disclosed ideal-clock diagnostic, all ten A3/A0 pairs have identical reported CPD. Both native arms have 0.277% lower geometric-mean CPD than modern LaZagna; that cross-tool difference is not an A3 benefit. Paper-reported results remain a separate reference without a comparable A3 ratio.

Start with [the Chinese research report](docs/研究结论.md) and the
[generated experiment results](docs/实验结果.md). The completed matrix contains 769 route runs: 637 native successful, independently
audited solutions and 132 retained failures. All 90 sequential timing runs pass.
A3 has conditional timing benefits; A4 has no stable overall advantage in this study.

A separate [LaZagna reproduction and graph correspondence report](results/lazagna_reproduction/report.html)
pins the paper-era LaZagna/OpenFPGA/VTR sources, retains strict published-configuration
attempts, and checks DSP exits, planar edges and physical vertical resources.
Its status is recorded separately from the original 769-run matrix.

The baseline is a pinned upstream VTR version with native CHANZ support. Algorithms must retain directed connectivity, per-net resource occupancy, the original timing model, and the same placement/architecture during router comparisons. This is software CAD research; VPR timing results are model-based, not silicon measurements.

See [the implementation and validation plan](docs/implementation_plan.md) for the full task, evidence requirements, and progress. Source modifications will be kept as reviewable patches against the pinned VTR checkout. Downloaded dependencies, builds, and raw runs are kept outside the tracked source files.

The finite model and its limits are described in [planner_model.md](docs/planner_model.md).
Two literature-inspired controls, their explicit formulas, and differences from
the original papers are documented in [literature_controls.md](docs/literature_controls.md).
The imported FLUTE code retains its [BSD-3 license](LICENSES/FLUTE-BSD3.txt).
Build, paired-run and audit commands are in [reproduction.md](docs/reproduction.md).

## Tool choice

AMD Ross Skills and Vivado MCP are considered according to the user's FPGA tool policy. The current implementation phase uses C++/Python and VPR; it does not require a Vivado project or HLS synthesis. If fabric RTL/bitstream validation becomes necessary, inspect the applicable Ross skill and use existing Vivado MCP sessions preferentially. Local Vivado is 2022.2; newer commands require compatibility checks.


最新接续：[失败释放迁移与实际事务执行检查](docs/GitHub_release_execution_progress_20261115.md)。

最新组件：[完整方法迁移、实际反馈验证与整流程执行登记](docs/GitHub_unified_method_progress_20261115.md)。
