# Portable serial resource controller component

The current component is `../standalone_resource_controller_dev_03`.
It ports the **registered serial lazy** unified resource controller. It does not
replace the separately running persistent-pool query-reduction experiment or
claim the costs of the source-snapshot engineering variant.

The original resource/owner `while` loop and both transaction arm loops are AST
identical. Current crossing/owner selectors, scheduling, fixed-root decisions,
terminal selection and handoff are unchanged. Worker code from native execution
through source/physical/STA checks and input sealing is AST identical; source
physical-audit reuse is retained. The fresh-route entry preserves its native
quality/physical/STA gate block, binds explicit phase binaries, and connects to
the portable resource controller. Runtime-library resolution, package hashing
and explicit input admission are engineering changes whose full costs have not
been measured here.

`controller_runtime.py` accepts `explicit_unified_phase_runtime_v1` JSON:

- `physical_files`: architecture, circuit, graph, packed, placement, and optional
  sdc; each row contains `path` and `sha256`.
- `phase_binaries`: resource and owner; each row contains `path` and `sha256`.
- `full_graph_cache_completion_sha256`: required for an imported-state resource
  run; the fresh-route entry derives it from the actual same-flow cache.

Paths in this descriptor can be relative to its own directory. The returned
configuration uses absolute paths before being written inside a new flow.
Route commands and `input_sha256` in a fresh-route config use absolute paths.
The fresh route pathname is an output placeholder, never an imported input.

An imported-state invocation is:

```text
python run_unified_resource_repair_v1.py --runtime-config RUNTIME.json \
  --initial-state STATE --batch NEW_OUTPUT --full-graph-cache CACHE \
  --bundle-size 8 --seed-order delay_rr_id --domain-mode paired --domain-feedback
```

The independent fresh-route/resource entry is
`run_complete_unified_resource_flow_v1.py --config FLOW.json --output NEW_OUTPUT`.
Its config retains the original route command, input hashes, cache mode, domain
mode/feedback, seed order, and owner settings, and adds `phase_runtime_config`.
The native baseline uses the same implementation with unrestricted mode and no
feedback flag. No completed output directory may be reused as a new run.

Actual validation uses the original tiny no-cut state and known R1 source,
outside the historical project with locally copied NumPy/lxml. The no-cut
controller and terminal menu/handoff really execute. The R1 owner selector returns
exactly the original eight groups; owner request and controller's first crossing
request match existing native requests. Three workers and the fresh-route entry
reach actual command construction, then an explicitly marked capture stops
before `io.run`. These are not new native calls or independent circuit samples.
The fresh-route preflight imports a graph-only cache; it does not execute the
cold joint-index build. The diagnostic Python launcher forbids reads from the
historical project in the checked interpreter; it is not an OS sandbox.

Version 1's missing historical cache-validation receipt and manifest byte-order
mismatch are retained. Version 2 removes that obsolete lookup while retaining
actual package/XML/cache-payload admission and canonicalizes manifest ordering.
Version 3 normalizes relative paths for derived same-flow configs. All 73 files
of version 3 rebuild byte-exactly; original versions and registered experiments
are unchanged.

The full current-STA timing portfolio and outer whole-method wrapper still need
porting. Positive owner commit/reentry, native backend execution equivalence,
and complete costs remain unverified. This component is not the frozen complete
confirmation method. The existing native observation and owner transaction
interface checks keep their originally registered packages and queue order.
