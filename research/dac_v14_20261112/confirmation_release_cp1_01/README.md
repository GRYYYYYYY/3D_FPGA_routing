# Current-STA confirmation source CP1

This is a fixed prospective confirmation version, not a completed confirmation cohort. The116-file runtime is byte-identical to the outside-project whole-method execution. Existing development jobs retain their original package and rules. The inherited runtime string `development_v1` is a compatibility tag; `release_manifest.json` and the measured `confirmation_input.json` identify CP1.

Dependencies are CPython3.10 on Linux x86_64, the bundled NumPy2.2.6/lxml6.1.3/shared-library files, Linux process supervision, the exact phase binaries/query executables declared in `binary_inputs.json`, and explicitly provided architecture/RRG/BLIF/packing/placement files. Binaries and large input data are explicit external inputs, not bundled or fetched automatically. Source compilation and packing/placement generation are upstream. No historical project Python imports or hidden state aliases are required.

Use an input directory outside the historical project. Make native/domain configs with exactly the fields in `contract.json`: fixed configuration plus route command, phase-runtime configuration, input SHA256 map and the two arm switches. Native is unrestricted/false, domain is paired/true. Both arms use identical current selectors, owner opportunities and fixed route controls. The route command explicitly disables the failure predictor and fixes8convergences/1.01threshold; device, channel width, seed and physical paths belong to the preregistered input, not per-arm tuning.

Copy the actual provenance manifest whose `outputs.packed.net.sha256` identifies the input packing. Preserve its `--merge_constant_generators off` when present; an omitted flag means the bound native default on. The checker rejects an off-to-default mismatch before native work. Add SHA256 bindings for the release manifest, contract and provenance manifest to both configs' input maps. Physical/binary bytes are fully checked by the original runtime inside the measured command; cheap admission alone is not a byte-integrity or legality proof.

Before preregistering a cohort:

```
python3 confirmation.py check --native INPUT/native.json --domain INPUT/domain.json --packing-manifest INPUT/source_manifest.json --forbid-prefix HISTORICAL_PROJECT
```

Run each arm serially, using a new CASE directory and an external queue's shared execution lock. Do not run both arms concurrently. The exact measured command is:

```
python3 runtime/measure_process_tree_v1.py --output CASE/measurement -- python3 runtime/supervise_method_phase.py --receipt CASE/supervision.json -- python3 confirmation.py run-arm --native INPUT/native.json --domain INPUT/domain.json --packing-manifest INPUT/source_manifest.json --forbid-prefix HISTORICAL_PROJECT --arm native --case CASE
python3 runtime/guarded_entry.py --forbid-prefix HISTORICAL_PROJECT --script runtime/verify_complete_unified_method_v1.py --root CASE
```

Use `--arm domain` and a different CASE for the other arm. Verification is a separate research audit. Preserve every failed command and its complete measured cost. Only complete verified outputs may carry legal quality. Match initial route bodies, full vectors, physical identities and constraints before reporting paired differences. A native/domain pair jointly changes restriction/release and cannot isolate them; separate fixed-scope ablations remain necessary.

Freeze the cohort's input/config/release digests before any outcome. No old development run becomes confirmation merely because its runtime bytes match. Changes after this source freeze require a new release/cohort. Keep no-cut/no-gain/worse/initial-routing outcomes and distinguish input loading errors. Positive owner reentry, positive timing feedback and independent complete benefits remain unconfirmed; consult `contract.json` for exact rules and gaps.
