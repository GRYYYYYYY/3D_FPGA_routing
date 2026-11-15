# Standalone selector development entry

The sibling `standalone_selection_dev_01` package contains `select_scopes.py`, exact extracted scientific kernels, all observation dependencies, and the byte-identical full serial `NativeAnalysisPool`. This is a development component, not the complete frozen method.

Use Python 3.10.12 with NumPy 2.2.6 and lxml 6.1.3, the versions exercised by this validation:

```sh
python select_scopes.py --inputs inputs.json --output new-selection-directory
```

`inputs.json` has format `explicit_selection_observation_v1`, `minimum_margin_ns: 0.2`, `near_ns: 0.0`, and `files` containing `route`, `trace`, `constraints`, `vector`, `audit`, and `graph`. Each record supplies a path relative to the descriptor and its SHA-256. `cache` supplies a full graph-cache directory and its completion digest. The route and trace must share a directory and use the names `routed.route` and `native_sta_frontier.jsonl`; its constraints echo has the `.constraints.echo` suffix. The full vector is checked against a fresh complete parse of that trace. Cache payloads and the route resource census are checked. The package manifest must match before execution.

Outputs are `sta.json`, `crossing.json`, `owner.json`, and a bound completion receipt. They are proposals, not accepted transactions or native legality proofs. Native FULL, fresh physical proof, candidate execution, acceptance and complete flow measurement remain separate requirements.

`completion.json` records actual outside-project replay on full existing R1 and tiny inputs. R1's historical eight owner groups and one sharing scope match exactly, including all certificates, screens, ranks and request bytes. Tiny's zero scopes remain explicit. Wrong input hash fails before output creation. Cache payloads were copied exactly; changed metadata paths are marked as relocation, not a new build. The launcher's Python audit hook is a dependency test, not an OS sandbox.

No new native calls or independent scientific samples were added. The copied pool was not executed here. The original registered observation package and running experiment versions remain unchanged.
