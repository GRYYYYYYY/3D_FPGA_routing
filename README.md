# H3D-inspired native 3D FPGA routing

## Current snapshot — 2026-11-09 (experiments in progress)

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

