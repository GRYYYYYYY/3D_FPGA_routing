# Complete serial method: development portability validation

The current package is `../standalone_unified_method_dev_03`. This is a complete
dependency port of the registered serial method, **not a frozen confirmation
result**. The persistent pool, source snapshot and query grouping experiments
retain their own implementations and costs.

The resource phase derives sharing cuts from the current route and STA. It
tries the registered rank windows with domain-first lazy scheduling and optional
per-net failure release. When resource proposals do not advance, capacity
certificates and timing margin select owner coordination, unrestricted in both
arms. Each accepted whole transaction triggers current-state reselection. The
root CPD and resource envelopes never roll forward. Intermediate route branches
are private construction states; they need not individually improve CPD.

The endpoint-safe terminal wire choice is made among actual candidates of the
same resource flow. A fresh complete STA handoff then starts the original
current critical-path portfolio: action-derived proposals, lazy critical-owner
exchange, then same-source rejection feedback covering tied paths. First
admissible whole-candidate acceptance advances the state; the final output is
the registered strict timing terminal, not the best historical observation.
Exact native success/failure and query reuse remains confined to this actor.

`run_complete_unified_method_v1.py --config FLOW.json --output NEW_OUTPUT` is the
complete entry. `verify_complete_unified_method_v1.py --root CASE` and
`measure_process_tree_v1.py` are copied byte-exactly from the original whole-flow
implementation. The phase hash fields retain the original schema:
`route_and_resource`, `owner_coordination`, `timing_native_repair`,
`timing_candidate_STA`.

The added `phase_runtime_config` points to `explicit_unified_phase_runtime_v1`:

- `physical_files`: architecture, circuit, graph, packed, placement, optional sdc.
- `phase_binaries`: resource, owner, timing_repair, timing_observer.
- `query_engines`: capacity and relaxed.
- `query_validations`: capacity unit-validation receipt.

Each entry has a path and SHA-256. Relative paths resolve against the descriptor,
then normalize before any derived descriptor is written. Imported-state checks
also bind `full_graph_cache_completion_sha256`; a complete fresh flow obtains
this value from its own joint graph build. Route output is never an input.
Package files, real graph/cache payloads, source FULL/physical/STA gates and all
actual consumed receipts remain checked. Historical proof aliases are replaced
by explicit package/runtime admission, not by fabricated successful receipts.

Actual validation outside the repository used the existing eltwise observation:
all original timing feedback stages and portfolio preparation ran until the
first uncached native proposal, intentionally held by `--native-mode reuse_only`.
Five capacity and five relaxed queries were then reused with zero new queries;
their full query logs were identical. Both timing workers reached actual
command/runtime binding and stopped at an explicit `io.run` capture. No VPR was
called, and no independent circuit was added. This does not exercise rejection
feedback after a newly executed native rejection or a positive owner commit.

Five scientific controller/transaction loops and two timing workers' complete
native execution/audit/STA/seal tails are AST identical. All 116 package files
rebuild byte-exactly. Revision 3 changes only the outer phase-field mapping and
adds the unchanged original verifier/observer; revision 2 validation therefore
remains applicable to its unchanged scientific components. Revision 3 outer
admission was also executed before registration.

Each invoked phase has a private Linux subreaper. Real fork/setsid tests cover
normal completion, child timeout, live orphan after root exit, and interruption;
all leave no descendants. The original per-native/per-child guards remain.
Complete multi-step phases have no total time or call cap. Hashing, library
binding and supervision overhead must be measured in both arms.

`../standalone_whole_method_check_01/plan_v2.json` registers the first actual full
execution on existing tiny packing/placement, with fresh routing and one joint
graph build inside the measured command. It follows all pre-existing queues.
The original pre-execution plan is retained: its amendment keeps orchestrator
hash checks outside the project-read-denying verifier. No native call ran under
that first plan. Positive owner commit/reentry, full native equivalence, distinct
inputs and complete paired costs remain required before confirmation freeze.
