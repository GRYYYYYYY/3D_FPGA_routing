# Reproduction and evidence

## Subsequent LaZagna VTR9-port pilot (2026-10-25)

The [separate pilot report](LaZagna后续分支验证_2026-10-25.md) records the exact
`5abd3acaa603e037ec390fa545b04301f13d57e0` source, two retained unmodified build
failures, and a successful VPR-only build with three disclosed portability edits.
The binary is archived under `artifacts/bin/lazagna-vtr9-port-buildfix/` and all
new receipts are under `results/lazagna_vtr9_port/`; neither previous study is
overwritten. All nine pilot routes passed FULL and independent scoped audits.
See that report for the build/graph/fixed-input/PTC-control entry points and
`results/lazagna_vtr9_port/validation.json` for final integrity checks. The small
modern graph and three legacy-graph fixed-input pairs do not constitute a
full-size modern end-to-end PnR comparison.

## Separate LaZagna paper-era controls (2026-10-23)

See [the generated report](../results/lazagna_reproduction/report.html),
[frozen protocol](../results/lazagna_reproduction/protocol.json), and per-run
`manifest.json` files. They do not replace the original A0–A4 evidence below.
LaZagna is pinned to `16fa62c9385843144f9d00c3827e1d87accec4fb`, OpenFPGA to
`729e6187fe9e88b8c24399cfe852bcd3b3fb9291`, and its nested VTR to
`a80511e8f96d560e680d2ebe9c18272a759ce493`. The paper does not identify its exact
experimental commit; the selected public commit is the last on its publication day.
The archived unmodified VPR executable and build settings are in
`artifacts/bin/lazagna-paper/`. OpenFPGA also builds, but full fabric RTL/bitstream
reproduction is not claimed. The historical synthesis template refers to a missing
`yosys.ys`; the existing exact BLIF inputs are used for this PnR comparison.

The protocol uses the paper's 100×100×2 grid, W300, 50% repeated-interval subset
SBs, ratio 0.739, and published example settings cube_bb/seed1/inner_num0.5.
The historical SB generator is run without source edits. Graph dimensions 40×40×2
are used for exhaustive, exact node/edge correspondence; full 100×100×2 graphs
receive physical-Z mapping, BRAM clock connectivity scans, and exhaustive DSP
OPIN endpoint comparisons. The full-array W100/W300 comparisons each cover all
2,548 DSPs and 188,552 OPINs using physical keys rather than version-local IDs. All native-legal
routes must also pass the separate graph/tree/capacity audit before being called
audited successes. Concurrent process timings are not performance comparisons.

An explicit amendment records the published `clock_modeling=route` versus
`spram.clk Fc=0` conflict. Strict primary attempts are preserved; redundant
fixed-layout attempts with active BRAM clocks are cancelled with per-run structural
preflight receipts. Separate `*_ideal_*` diagnostics reuse the exact packed netlist,
placement and graph while changing only the clock treatment. Native compatibility
retries additionally disable the newer VPR's constant-generator merging, matching
the old reader's behavior without editing the packed netlist. These are labeled
diagnostic adaptations, not unchanged original-toolchain results.

The published XML uses L4/L16 frequency weights 280/40, while paper Table III
states 260/40 tracks. Preserve the published XML as the main artifact, and use
`run_lazagna_table_graph.py` for the separate literal-table sensitivity graph.
Its actual channel composition is 260/40 and its BRAM clock pins remain isolated.
Its DSP exits differ from the published-XML graph and are reported separately.

The pinned old VTR branch has inverted valid-coordinate rejection guards in
two placement search-range functions (introduced by `af5b6a4434`).
`build_lazagna_guardfix.py` builds an isolated executable by replacing only the
affected object in a copied library. The original source and binary remain intact.
`run_lazagna_guardfix_pnr.py` registers three full-PnR controls: bnn retains route
clocking, and conv_layer/dla_like.small match the clock-only ideal-PnR controls
from `run_lazagna_repaired_pnr.py`. `validate_lazagna_guard_controls.py` verifies
matching commands and inputs, including canonical packed-netlist equality after
normalizing only its root output filename. All three repaired routes passed both
native FULL and independent auditing. This is a defect in the selected public
branch; the paper does not pin its experimental revision, and native A0 does not
contain these inverted guards.

The historical `vpr_flow` also rewrites `PlaceFile` unconditionally after loading
an existing placement. One redundant clock-route attempt recorded a transient
input hash during a concurrent rewrite and was cancelled before loading placement.
It is preserved and explicitly excluded from numerical comparisons in
`input_registration_race.json`. The reusable runner now gives each attempt
private, byte-identical packed/place copies, so solver rewrites cannot race with
other readers. The original commands and evidence were not retroactively changed.

Four adopted timeout receipts used the empty GNU-time output's creation mtime.
Their original receipts are retained; `timeout_timing_observation.json` records
an explicitly labelled completion-observer upper bound from the result timestamp.
These timing fields are not used for speed comparisons.

Graph-generation clock mode is also an explicit control variable: the historical
graphs use route mode, while the native graphs preserve the original A0's ideal
mode. `check_lazagna_clock_graph_mode.py` changes only that native generation flag
and compares physical edges. It restores all 2,128 CLB clock IPINs in the 40×40×2
fixture and redistributes some ordinary CHAN-to-IPIN edges, without changing DSP
OPIN exits or channel-to-channel edges. Two native bnn route-clock attempts using
the ideal-generated graph are therefore labeled graph/mode incompatibility and
excluded from performance comparisons. The ideal fixed-input arms match the
native graph policy; BRAM's zero-Fc clock limitation persists in either mode.

Entry points (each owner refuses an existing state; do not launch duplicates):

```sh
.venv-lazagna/bin/python scripts/prepare_lazagna_study.py
.venv-lazagna/bin/python scripts/run_lazagna_graphs.py --family paper --wait-build
.venv-lazagna/bin/python scripts/run_lazagna_graphs.py --family native
.venv-lazagna/bin/python scripts/run_lazagna_routes.py --workers 6
.venv-lazagna/bin/python scripts/run_lazagna_planar_controls.py
.venv-lazagna/bin/python scripts/run_lazagna_clock_diagnostics.py
.venv-lazagna/bin/python scripts/run_lazagna_native_compat.py
.venv-lazagna/bin/python scripts/collect_lazagna_study.py
```

The complete graph, clock-scan and route-audit commands are recorded with their
outputs under `results/lazagna_reproduction/`; the collector refuses unfinished
evidence unless explicitly called with `--allow-incomplete` for a progress report.
`audit_lazagna_dsp_correspondence.py` performs the full-array DSP comparisons.
`audit_lazagna_routes.py` is invoked separately for the original, ideal-clock,
native-compatibility, clock-only-PnR and guard-repair state files. The one-time
native scheduler transfer is recorded separately and retained the original live
solver processes and deadlines; fresh studies use the ordinary native scheduler.
`finalize_lazagna_study.py` waits for all registered states and audits, reconciles
timeout timing annotations, collects results, and runs `validate_lazagna_study.py`.
The final validator rehashes unique inputs and outputs, verifies every successful
route's placement digest, checks protected original-study files, and checks report
links. Existing evidence directories are never a target for rerunning the study.

## Original native-3D study

Read [the Chinese research report](研究结论.md) and [generated results](实验结果.md)
for the interpretation. All planned matrices, independent audits and sequential timing runs are complete.
The collector rejects incomplete evidence unless explicitly run with
`--allow-incomplete` for an intermediate inspection.

## Build

The pinned VTR commit is in `configs/sources.lock.json`. A clean baseline binary
and build manifest are archived under `artifacts/bin/baseline/`. Source patches
are exported without making commits to the upstream repository.

The container required these packages (Ubuntu 22.04):

```sh
DEBIAN_FRONTEND=noninteractive apt-get install -y cmake ninja-build flex bison \
  pkg-config zlib1g-dev libtbb-dev libreadline-dev libffi-dev python3-venv \
  python3-pip clang-format time swig tcl-dev
```

Initialize the pinned `eigen`, `libcatch2`, `libsdcparse`, `yaml-cpp` and `yosys`
submodules. Use `python3 scripts/build_vpr.py --name baseline` before applying the
patch, and a different name after modifications. The script invokes upstream's
Makefile. This revision requires interchange enabled when Cap'n Proto is on:
disabling interchange alone leaves unconditional schema includes in
`read_fpga_interchange_arch.cpp`. Enabling it resolves the build without an
upstream code change. Its Java schema is fetched by the upstream build recipe.

The system clang-format 14 does not recognize `InsertNewlineAtEOF`; format the
changed files with `--Wno-error=unknown` and preserve a terminal newline manually.

## Paired experiments

```sh
python3 scripts/run_vpr.py \
  --circuit vendor/vtr/vtr_flow/benchmarks/blif/ex5p.blif \
  --width 100 --output results/runs/prepare_ex5p
python3 scripts/run_vpr.py --reuse results/runs/prepare_ex5p \
  --binary artifacts/bin/a1/vpr --output results/runs/ex5p_a1 \
  --env VPR_H3D_VERTICAL_WEIGHT=1 --env VPR_H3D_STATS=1
python3 scripts/check_route.py \
  --rr-graph results/runs/prepare_ex5p/rr_graph.xml \
  --route results/runs/ex5p_a1/routed.route --output results/ex5p_a1.audit.json
```

Keep each run directory: manifests hash the binary, architecture, circuit and,
for route-only comparisons, packed netlist, placement and RRG. The wrapper rejects
changed prepared input bytes. It invokes VPR's FULL checker. The separate audit
checks tree attachment, directed graph edges including switch identity, reported
node metadata, routed resource capacities, and vertical channel sharing. It does
not independently check terminal-to-netlist identity, reserved local OPINs,
nonconfigurable closure, or bus-mux configuration: these remain covered by VPR.
Do not describe this audit as independent complete bitstream certification.

`VPR_H3D_VERTICAL_WEIGHT=w` multiplies the configurable CHANZ congestion charge
by `1+w`; zero follows the original arithmetic. Existing criticality weighting,
present/history cost, capacitance and timing refresh are preserved.
`VPR_H3D_STATS=1` enables per-iteration resource/search counters. Compare instrumented
variants with the same instrumentation setting when measuring runtime.

## Initial observations (2026-10-22)

- The unmodified headless baseline built with GCC 11.4 and CMake 3.22.1.
- The bundled `adder.blif` uses an architecture-specific `adder` model absent
  from the chosen Hecate architecture; this is an input compatibility failure,
  not a routing result.
- `alu4` failed to converge at channel width 66 within VPR's iteration budget.
  At width 100, `alu4`, `ex5p` and `diffeq` completed with the FULL native checker
  and independent scoped audit passing.
- The width-100 `alu4` placement uses **zero** CHANZ resources. It is a planar
  negative control, not evidence for a cross-layer optimization. `ex5p` and
  `diffeq` use 323 and 490 vertical channels respectively.
- Subsequent endpoint inspection found **zero driver-to-sink layer changes in
  all three initial placements**. CHANZ occupancy is not synonymous with an
  inter-layer terminal connection: it can be used for detours or same-layer
  access through a bidirectional vertical resource. These initial runs test A1
  and disabled-mode equivalence, but do not exercise the remote-terminal DP.
  `make_layer_fixture.py` creates explicitly labeled balanced-CLB stress fixtures
  with matched tile type/offsets and unchanged XY/subtile positions. The ex5p
  fixture moves 39 of 78 CLB clusters; VPR accepts the resulting placement.
- Preparation logs contain warnings/errors about disconnected resources while
  constructing placement-estimation graphs. Preserve and investigate these;
  successful final routes do not establish that every architecture resource is
  reachable. Candidate reachability must be checked in the exact final graph.
- These preparation runs overlapped and included graph generation/placement.
  Their elapsed times are functional smoke evidence only; controlled runtime
  comparisons must use repeated, sequential route-only runs.

The native model's vertical segment has zero wire R/C, while the inter-die switch
uses fan-in dependent delay entries (e.g. 142 ps at fan-in 32 in the selected
switch). This is a particular model assumption, not a universal measured FPGA
delay. Architecture sensitivity experiments must retain/report its full tables.

## Checks

```sh
python3 -m unittest discover -s tests -v
python3 scripts/export_patch.py
```

The core C++ checks can be rebuilt independently of VPR:

```sh
mkdir -p build
g++ -std=c++20 -O2 -Ivendor/vtr/vpr/src/route tests/test_partition_dp.cpp -o build/test_partition_dp
g++ -std=c++20 -O2 -Ivendor/vtr/vpr/src/route tests/test_reachability.cpp -o build/test_reachability
g++ -std=c++20 -O2 -Ivendor/vtr/vpr/src/route tests/test_flute_adapter.cpp \
  vendor/vtr/vpr/src/route/h3d_flute.cpp -o build/test_flute_adapter
build/test_partition_dp
build/test_reachability
build/test_flute_adapter artifacts/sources/flute3
python3 scripts/exact_small_graphs.py
```

The FLUTE code/LUT pair and copyright are pinned in
`configs/flute_sources.lock.json` and `LICENSES/FLUTE-BSD3.txt`. PathSteiner's full
3,101,706,050-byte archive was checked against the published MD5; SHA256 and URL
are in `artifacts/sources/pathSteiner.tar.verified.json`. The adapted controls are
not full reproductions of either paper. Their explicit definitions and source
limitations are in `literature_controls.md`.

## Full experiment matrix

The prepared input lists and variant JSON files are the canonical experiment
definitions. Every queue uses one owner and a file lock; keep existing terminal
runs and never run competing owners for the same label. An output directory must
be empty for a new route. Existing failed runs are retained, not silently rerun.

| Data | Preparation list | Variants / queue labels |
|---|---|---|
| 20 public circuits, seed 1 | `results/koios_prepare_seed1.json` | `variants_a0_a4.json` / `koios_a0a4_seed1`; `variants_controls.json` / `koios_controls_seed1`; `variants_prune_controls.json` / `koios_prune_controls` |
| 2 fixed placements × 8 architectures | `results/sweep_prepare_v4.json` | `variants_all.json` / `sweep_all_v4` |
| 5 MCNC circuits × 3 seeds | `results/paired_seed_prepare.json` | `variants_all.json` / `paired_seeds_all` |
| Natural elliptic follow-up | `results/natural_seed_prepare.json` | `variants_all.json` / `natural_seeds_all` |
| Identical incremental-pruning controls | `results/small_all_prepare.json` | `variants_prune_controls.json` / `small_prune_controls` |
| Exploratory training | `results/tuning_prepare.json` | `variants_tuning.json` / `tuning` |
| Held-out placements | `results/heldout_prepare.json` | `variants_tuned.json` / `tuned_heldout` |
| Same elliptic placements, W=160 | `results/elliptic_w160_prepare.json` | `variants_extended.json` / `elliptic_w160_all` |

For example, on prepared inputs:

```sh
python3 scripts/run_matrix.py --prepared-list results/koios_prepare_seed1.json \
  --variants configs/variants_a0_a4.json --label koios_a0a4_seed1 --workers 2
```

The preparation entry points are `fetch_benchmarks.py`, `make_native_arch.py`,
`prepare_koios.py`, `prepare_paired_seeds.py` and `prepare_sweeps.py`; inspect their
`--help` and the immutable preparation manifests for exact parameters. The
20-circuit architecture is
`configs/architectures/koios_native3d_n6_f16_d1_v3.xml`; its adjacent provenance
file documents the preserved Koios primitives and imported native Hecate Z model.
It is a hybrid model, not a process-calibrated reproduction of Beyond-Flatland.
Clock modeling retains this pinned VTR's default `ideal`; these signal-routing
experiments do not evaluate physical cross-layer clock-network routing delay.

Balanced MCNC fixtures use `make_layer_fixture.py`, which preserves XY/subtile
positions and checks compatible empty sites on the other layer. Natural elliptic
placements already span layers. The initial seed queue captured placeholder paths
before those natural outputs were selected; its 24 `unavailable_inputs` slots
are explicitly superseded by the 24 real runs in `natural_seeds_all`, not counted
twice. Their W=100 failures remain results. W=160 is a separate capacity study.

Architecture changes use `regraph.py`. It checks exact equality of all non-Z
architecture structure and reuses packed/place bytes, then records a specific
architecture-digest exception before disabling VPR's embedded digest check.
`run_vpr.py` revalidates this compatibility proof and all prepared hashes on reuse.
Do not generalize this exception to arbitrary architecture changes. The failed
earlier `sweep_prepare`, `v2`, `v3` attempts are retained; only `v4` enters results.

The wrapper defaults to 900 seconds per route-only process, with the native
convergence predictor unchanged. Preparation of the large circuits uses 1,800
seconds. A predictor abort or timeout is not a proof of unroutability. Failed
preparations may still supply complete frozen packed/place/RRG inputs, allowing
all router variants to be tested on the same problem.

Paths in the archived manifests are absolute. To reproduce in a different
workspace, regenerate preparation manifests and update `VPR_H3D_FLUTE_LUT` in
variant configurations to the new absolute LUT directory; preserve the pinned
content hashes. Do not edit historical manifests to pretend they came from the
new location. Each run's binary SHA identifies the algorithm actually measured.

## Audits, timing and final collection

`audit_matrix.py` requires terminal matrices, streams each shared XML RRG once
per batch, and audits all routes against the actual directed edges/switches. A
native successful route failing the independent audit stops final validation.
Failed routes can legitimately contain overflow and remain marked failed.
An existing detailed audit is reused only after matching both auditor source
hashes and freshly computed graph/route hashes. Completed subsets can therefore
be audited while the remaining screening matrix runs. Sequential timing also
waits for the exact recorded pre-audit process IDs and start times to terminate.

```sh
python3 scripts/audit_matrix.py --matrix results/sweep_all_v4.json \
  --matrix results/paired_seeds_all.json --matrix results/tuning.json \
  --output results/audits_small_connection_delays.json --workers 2
python3 scripts/final_validation_queue.py
```

The final supervisor waits for the remaining matrix owners, audits their routes,
runs `run_timing_repeats.py` sequentially, and audits those timing routes. Timing
uses ex5p balanced seed1 and natural `conv_layer_hls`, 15 settings, 3 repetitions,
and deterministic shuffled variant order. All include the same native net timing
CSV option. Native A0 and instrumented-but-disabled A0 are both measured.
The already selected A1/A3/A4 tuning settings are included. Selected A1 has the
same weight as the early weight-2 setting, but uses a newer archived binary with
dormant planner/control branches, so both are timed. The final timing list was
fixed before any timing repeats started; no parameters are selected from timing data.
All algorithm planning and control setup are included in the native routing
measurement. Process wall time additionally includes graph reading and analysis.
This removes contention from our own experiment queues, but not shared-host load.

Only after that supervisor reports `ready_for_final_analysis`:

```sh
python3 scripts/collect_results.py
python3 scripts/verify_timing_repeats.py
.venv/bin/python scripts/render_results.py
python3 scripts/package_results.py
```

Without `--allow-incomplete`, these steps refuse provisional evidence. They join
native counters, input hashes and route audits; failed runs are kept in CSV/JSON.
Ratios require jointly successful audited pairs. Repeated timing measurements
are reduced within a case before comparing variants. The figures report min/max
measurement ranges, not confidence intervals. The Python package versions used
for VTR's task runner and plotting are in `artifacts/python-environment.txt`.
`python3 scripts/verify_tuning_selection.py` independently recomputes the archived
training-only choice and checks it matches `results/tuning_selection.json`; it
does not reselect parameters from held-out or timing results.
The ZIP contains reviewable code, exact run/preparation manifests, historical
build source snapshots, compact evidence and plots. Large binaries, RRGs, route
files and per-net audit bodies remain in the workspace, identified by hashes;
the ZIP is not a standalone copy of those large external dependencies.

The zero-RC delay audit adds actual switch Tdel on each source-to-sink route-tree
path, including repeated branch starts and distinct sink pin indices. It refuses
that shortcut when the path's R/C is nonzero. These are inter-cluster routing
delays, not logic-inclusive CPD; native STA remains authoritative for CPD.

## Follow-up failure diagnosis (2026-10-23)

The primary frozen protocol is `configs/failure_diagnosis_native.json`, amended
from the initial `configs/failure_diagnosis.json`. It selects all
132 previously failed routing runs and three successful controls (A0 for both
variant-specific regressions, and A0 with the same pruning threshold for
`clstm_like.small`). Original executables, environment variables, architecture,
packed netlist, placement, and W=100 RRG are retained by SHA256. The historical
769-run analysis and package are not replaced by this diagnostic dataset.

`scripts/diagnose_failures.py --native-primary` reuses all 135 completed
predictor-off/50 runs, runs predictor-off/200 on every selected source, and
extends unresolved runs to 500 together with their A0 controls. The primary
intervention retains the native default congestion-mode threshold fraction 1.0;
the stronger congestion mode never participates before the iteration limit.
One process owns the finite queue and lock; it uses up to 24 single-threaded VPR
processes with a 180 GiB estimated memory admission limit and a 7200-second
per-run timeout. It reuses the 16 previously registered normal-mode controls,
waiting on their original owners when necessary rather than resubmitting them.
Concurrent timings describe
diagnostic execution, not a controlled performance comparison.

The native `--congested_routing_iteration_threshold` is a fraction of the maximum
iteration count. The initial protocol attempted to preserve an absolute
transition after iteration 50 by using fraction 0.25 at budget 200. This allows
new iterations that expand bounding boxes and focus on remaining conflicts,
which is an additional intervention beyond a pure iteration-budget extension.
Observed iteration times grew to tens of seconds on some large cases. The
protocol was therefore explicitly amended: the 26 completed high-effort trials
(13 successful, 13 failed) are auxiliary evidence; 16 in-progress trials were
terminated and marked `cancelled_protocol_amendment`, and 93 unstarted trials
were marked `not_run_after_amendment`. All logs and actual return codes remain
available. Cancelled runs are not counted as algorithmic routing failures.
See `results/failure_diagnosis/protocol_amendment.json` and the original
`state.json`; the main queue is now `native_state.json`.

We compare the recorded iteration counters, costs,
wirelength and CPD over shared prefixes, excluding elapsed time. Printed large
heap counts are rounded; equal stopping points additionally require byte-identical
route files. These checks support continuation of the same initial search
trajectory. In the revised main comparison the extra iterations retain normal
congestion mode, while auxiliary high-effort results remain a separate arm.

The separate width arm scans W=120/140/160 at predictor off, 200 iterations and
the same native normal-mode scheduling used by its W=100 reference,
keeping the same architecture, packing and placement. A0/A3/A4 subtree are
compared on the 11 common-failure placements; the two specific regression cases
use A0/A0-prune/A4 subtree or A0/FLUTE soft respectively. Each width gets a newly
generated RRG shared by its compared methods. Width preparation uses one routing
iteration solely to export the graph; its expected failed routing is not a
diagnostic solver trial. Wider RRGs can change connectivity and switch fan-in as
well as capacity, so this is a resource-configuration sensitivity experiment,
not a proof of graph infeasibility or an exact minimum-width search.

The actual queue and results are in `results/failure_diagnosis/`. To reproduce
with the archived frozen inputs and completed off50 receipts available, run the
revised owner and its independent validation follower:

```bash
python3 scripts/diagnose_failures.py --native-primary --parallel-widths
# In another process; it waits for the original owner's terminal receipt:
python3 scripts/finalize_failure_diagnosis.py --native-primary
# After validation completes:
.venv/bin/python scripts/render_failure_diagnosis.py --native-primary
```

Initialization and final validation verify the source hashes. Existing terminal
runs can be reused; any existing `running` receipt requires live-process
inspection before recovery. The finalizer uses the existing independent route
auditor on every newly successful run, verifies directed edges and capacities,
and requires a passing native FULL check. `collect_failure_diagnosis.py` writes
`analysis_native.json`/CSV and checks paired inputs and common search prefixes.
All unsuccessful runs remain in the diagnostic records.

After all 135 normal-mode 200-iteration trials completed, independently checked
capacity cuts established infeasibility of the fixed W=100 terminal demands for
`conv_layer`, `dla_like.small`, `dla_like.medium`, and `attention_layer`. The
first three have block-output demand greater than the sum of available boundary
capacities; attention requires the finer SOURCE-class cut, because the whole
block's output total alone does not expose its restricted pin access. The
certificate generator (`scripts/check_terminal_cuts.py --source-classes`) and
independent edge-enumeration verifier (`scripts/verify_terminal_cuts.py
--source-classes`) are separate programs. The Hall relaxation implementation was
also compared with exhaustive subsets on 300 random cases. A negative search
result is not a routability proof, and overlapping deficits must not be summed.

`certified_infeasibility_policy_source_classes.json` in the diagnostic directory
binds the four selected certificates, independent verification receipts, graph,
packing and placement by SHA256. All 44 affected variants retain their measured
200-iteration failures and remain in the original 132-failure denominator. Only
their redundant 500-iteration extensions are omitted. The remaining 72 original
failures plus one paired A0 control produce 73 500-iteration trials. Every case
still participates in the independent width scan. The controller was stopped at
the completed-200 checkpoint, with 17 just-started 500-iteration attempts retained
as `cancelled_at_capacity_checkpoint` and 100 unstarted attempts retained as
`not_run_at_capacity_checkpoint`; neither category is an algorithmic failure.
See `native_500_checkpoint_attempts.json`, `native_state_before_capacity_policy.json`
and `capacity_policy_transition.json`. The resumed stage uses fresh output names
beginning `normal500_after_capacity_check` and verifies all proof bindings before
admission. Keep the proof and verification files immutable after registration.

These cut proofs apply to the recorded fixed terminal mapping on the capacitated
directed RRG, not to other layouts, packing, architectures, widths or silicon.
Process timeouts, if any, are reported as censored trials with the last observed
iteration; they are never described as completed 500-iteration failures.

The `--parallel-widths` execution schedule prepares the 39 graphs, then admits
all 114 independent width trials under the same 24-worker/180-GiB limits. It
avoids waiting for the slowest case at each individual width before starting
the next width. It changes scheduling only; every trial retains its originally
registered inputs, 200-iteration budget, native congestion scheduling and
timeout. `parallel_width_schedule_registration.json` binds this decision to the
frozen diagnostic protocol. The initial proposal to stop at the post-500 stage
boundary (`transition_width_schedule.py`) was superseded before it acted, so it
did not cancel any graph preparation or routing trial.

For this execution, `scripts/overlap_failure_widths.py` waits until all 73 extended
trials have been admitted, then signals only the Python admission owner with
SIGINT. Its executor drains all admitted work; each VPR process has its own
process group and keeps its original supervisor, timeout and output manifest.
No VPR process is signaled by this scheduling change. A separate width coordinator
uses idle slots while counting the draining jobs against the same **total**
24-worker/180-GiB limits. After both arms finish, it acquires the original owner
lock, reconciles terminal manifests and starts the independent finalizer. See
`overlapped_width_schedule_registration.json`, `native_state_before_width_overlap.json`
and `width_parallel_state.json`. Fresh graph-preparation paths end in
`_native_parallel`. Only execution order changes; the trial population and solver
parameters stay frozen. Concurrent diagnostic wall times remain unsuitable for
algorithm speed comparisons.

`audit_failure_widths_incrementally.py` invokes the unchanged independent auditor
when every registered trial sharing a graph is terminal. Identical graph hashes
share a scan; the ordinary final audit still checks each route/graph hash and
reuses only matching auditor-version caches. An advisory lock prevents concurrent
cache writes by the incremental and final audit owners.

The stalled `dla_like.medium/W=120` case also received an exploratory terminal-cut
check (`check_width_terminal_cuts.py`). Its terminal demands came from that width's
own preparation route, not reused W=100 node IDs. No certificate was found by
this search, so its 200-iteration failures cannot be upgraded to a mathematical
infeasibility claim. See `width_terminal_cut_check.json`; this check did not omit
or change any registered solver trial.

After the two specific regressions first recovered at iterations 52/69, a
separate schedule control was registered to disentangle additional iterations
from the high-effort transition. `scripts/check_failure_schedule.py` retains
normal congestion mode through iteration 200 (threshold fraction 1.0) on those
two variants and their three controls. Its `--common-baselines` arm applies the
same counterfactual to the other 11 A0 circuit/placement cases. Both arms retain
the exact binaries, graph, packing, placement and algorithm settings of their
paired off200 runs, verify common prefixes through iteration 50, and perform
independent audits. They use separate owner locks and non-overlapping output
names; they never resubmit the main queue. Their 16 runs and comparisons are
recorded in `schedule_controls*.json` and `schedule_comparison*.json` within the
diagnostic results directory. Final collection requires both registered arms
to finish and validates every successful route's native and independent checks.

## Native timing-report repair and final source validation

The detailed timing resolver in this pinned VTR omitted CHANZ when expanding
interconnect delay, causing a Tatum delay-breakdown assertion. The patch includes
CHANZ in the same reporting branch as CHANX/CHANY. A paired unmodified/native-CSV
run and repaired/detailed run have byte-identical routes and atom delay/slack CSV.
`validate_timing_breakdown.py` independently checks 507 displayed resource
increments, including 60 CHANZ, against actual zero-RC switch Tdel within the
0.001 ns display precision. See `results/timing_breakdown_validation.json`.

The native VTR strong task is
`regression_tests/vtr_reg_strong/strong_h3d_vertical`; its final configuration
includes detailed timing, FULL route checks, and the real CHANZ architecture.
With the root virtual environment active, run from `vendor/vtr/vtr_flow`:

```sh
VPR_H3D_MODE=static VPR_H3D_REACHABILITY=scc \
  scripts/run_vtr_task.py regression_tests/vtr_reg_strong/strong_h3d_vertical
python3 scripts/python_libs/vtr/parse_vtr_task.py \
  regression_tests/vtr_reg_strong/strong_h3d_vertical -check_golden
```

`results/release_equivalence.json` records that final release source cleanup and
the report repair preserve the archived disabled, subtree and field-control
routes. `artifacts/bin/release/manifest.json` includes the binary, tracked patch
and every new source hash. `git -C vendor/vtr apply --reverse --check
../../patches/vtr-h3d.patch` verifies the exported patch matches the current source
without changing it. No upstream commits or pull requests were created.

## Three-baseline comparison on 2026-10-27

The completed comparison is documented in [三基线对比](三基线对比_2026-10-27.md).
`results/three_baselines_20261027/protocol.json` distinguishes published VTR-8.1
results, the pinned LaZagna VTR-9 port, and pristine native VTR A0. A3 uses the
original `a4scc` binary and the exact environment in `variants_a0_a4.json`.
Do not substitute an older A3 binary or the modified `vendor/vtr` working tree.

The original execution sequence was:

```sh
.venv-lazagna/bin/python scripts/run_three_baselines.py register
.venv-lazagna/bin/python scripts/run_three_baselines.py graphs
.venv-lazagna/bin/python scripts/audit_three_baseline_graphs.py native
.venv-lazagna/bin/python scripts/audit_three_baseline_graphs.py modern
.venv-lazagna/bin/python scripts/run_three_baselines.py routes --workers 6
.venv-lazagna/bin/python scripts/finish_three_baselines.py
```

The finisher may also start while the route supervisor is active: its sole
owner waits for the recorded terminal state, invokes the independent validator,
and collects statistics. It never resubmits solver jobs. Existing receipts and
outputs are protected against overwrite; a new study needs a separate `BASE`
and protocol. These commands are not an instruction to rerun the sealed study.

Both full-size graphs were generated with routed-clock connectivity. All three
measured arms use ideal clocks because every BRAM clock IPIN has zero fanin.
This is a disclosed diagnostic, separate from strict historical failures.
Each native run receives private copies of modern LaZagna's packed netlist and
placement. Validation checks source hashes, unchanged block coordinates, equal
native options, exact graph/binary hashes, FULL checks, and every successful
route against streamed graph evidence. Native CHANZ capacities are inferred
directly; legacy paired halves require the verified physical-resource map.

`summary.json` and `per_case.csv` exclude failures from paired CPD means while
retaining all eleven registered circuits. Resource means in
`native_resource_metrics.json` use the same audited A0/A3 pairs and
`exp(mean(log(A3/A0)))`; the finalizer independently checks their inputs and
calculations. No cross-family wirelength or concurrent-runtime speedup is
reported. After reviewing the report and QA record, `finalize_three_baselines.py`
seals the evidence and source bindings. The original twelve protected files
remain unchanged.
