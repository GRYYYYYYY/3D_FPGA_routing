# Standalone native runtime component 01

This component removes historical experiment directories from process execution,
metric parsing and physical route auditing. It is **not** the complete frozen
resource/owner/current-STA algorithm. Existing live and registered experiments
continue using their original code.

Supported and tested environment: Linux x86-64, Python 3.10.12, `/proc`,
`/usr/bin/time`, `/usr/bin/prlimit`, `/usr/bin/ldd`; physical auditing additionally
uses lxml 6.1.3. The included seccomp binary was validated on this host, not on
other architectures or operating systems. `seccomp_thread_guard.c` is included.
No VPR binary, benchmark input, or third-party Python package is bundled.

After extracting the archive, verify and execute the process/guard self-tests:

```sh
python3 selftest.py --output /tmp/new-runtime-check
```

The output directory must be new. The test creates actual normal, timeout,
thread-rejection, modified-input and wrong-executable receipts. These processes
are not VPR calls and do not generate scientific quality evidence.

With lxml installed in the chosen Python environment, audit explicit physical
inputs (the JSON output path must be new):

```sh
python3 audit_route.py --graph /data/rr_graph.xml --route /data/routed.route --output /tmp/new-audit.json
```

This checks directed edges, route trees, routed resource capacity and physical
wire/SB/CB counts. Native FULL checks, endpoint identity, local OPIN reservations,
nonconfigurable closure, mux selection and STA remain separately required; see
the output's exact audit scope. Failure returns a nonzero exit status and retains
the actual errors. It does not replace a native legality or timing observation.

Python callers use `runtime_io.configure(new_output_directory, executable)` once
per process, then `runtime_io.run(name, command, frozen=..., private_inputs=...)`
and `runtime_io.seal_inputs(...)`. Configuration binds the actual executable and
its current dynamic libraries. The runner preserves the existing 64 GiB address
space limit, serial guard, timeout, sanitized environment and input seals. The
executable must match that binding. A caller is responsible for the input/config
manifest, process scheduling, native command, candidate acceptance and full-flow
measurement. A per-call native time is not a whole-method time.

`artifact_manifest.json` seals package contents. `provenance.json` records original
source identities and transformations; historical paths there are provenance
only and are not read at runtime. The runtime API additionally enforces current
binary identity, an intentional strengthening over the historical wrapper.
The parser and scientific audit functions preserve their original ASTs; the
route auditor and serial guard are byte-identical to their originals.

Repository receipts `standalone_native_runtime_validation_01/completion.json`
and `standalone_physical_audit_validation_01/completion.json` record actual
relocated checks with historical project reads forbidden. Physical validation
replayed an existing tiny route (146 wire, 0 SB, 13 CB), rejected a corrupt switch,
and retained an unsuccessful native-observation denominator. It does not establish
SB-positive coverage or a new independent circuit result. Full selection,
transaction, graph-cache and endpoint-STA dependency closure, automatic positive
owner reentry and fixed full-method confirmation remain outstanding.
