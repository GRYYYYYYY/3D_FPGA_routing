"""Correct an overbroad table seed caption using existing command metadata only."""
import re, shutil
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha

parent_path = D/'mechanism_trigger_paper_binding_16.json'
parent = read(parent_path)
previous = Path(parent['snapshot'])
p = D/'paper'
e = D/'input_seed_paper_evidence_17'
assert not e.exists()
assert sha(p/'current_repair_main.tex') == sha(previous/'current_repair_main.tex')
e.mkdir()
bound = [parent_path, Path(__file__).resolve()]
cases = []
for group, prefix in [('BNN', 'complete_resource_timing_full_flow_01/bnn'),
                      ('Robot_SDC_upstream_s23', 'unified_input_integration_01/robot_s23_SDC')]:
    for arm in ['native', 'domain']:
        completion = D/(prefix+'_'+arm)/'completion.json'
        c = read(completion)
        assert c['passed'] and c['complete_configuration_verified']
        state = Path(c['initial_state'])/'completion.json'
        manifest = Path(read(state)['run'])/'manifest.json'
        cases.append((group, arm, manifest, completion, 11))
        bound.append(state)
plan = D/'cp1r2_cross_circuit_cohort_01/plan.json'
bound.append(plan)
for item in read(plan)['inputs']:
    for arm in ['native', 'domain']:
        config = Path(item['configs'][arm])
        bound.append(config)
        manifest = Path(item['workspace'])/arm/'flow/resource_flow/initial/runs/state/manifest.json'
        cases.append(('CP1r2_'+item['id'], arm, manifest, config, 21))

rows = []
for group, arm, manifest, receipt, expected in cases:
    m = read(manifest)
    cmd = m['command']
    assert isinstance(cmd, list) and cmd.count('--seed') == 1
    seed = int(cmd[cmd.index('--seed')+1])
    assert seed == expected
    def value(flag):
        assert cmd.count(flag) == 1
        return cmd[cmd.index(flag)+1]
    # These are recorded input identities, not a new physical-byte validation.
    inputs = {**{k: v['sha256'] for k,v in m['shared_inputs'].items()},
              **m['private_input_sha256']}
    placement = value('--place_file')
    packed = value('--net_file')
    graph = value('--read_rr_graph')
    assert all(path in inputs for path in [placement, packed, graph, cmd[1], cmd[2]])
    rows.append(dict(input=group, arm=arm, actual_router_seed=seed,
        manifest=str(manifest), manifest_sha256=sha(manifest), command=cmd,
        status=m['status'], returncode=m.get('returncode'),
        recorded_input_sha256={k:inputs[k] for k in [cmd[1],cmd[2],graph,packed,placement]},
        metadata_receipt=str(receipt), metadata_receipt_sha256=sha(receipt)))
    bound.extend([manifest, receipt])
for group in {r['input'] for r in rows}:
    pair = [r for r in rows if r['input'] == group]
    assert len(pair) == 2 and pair[0]['actual_router_seed'] == pair[1]['actual_router_seed']
    assert list(pair[0]['recorded_input_sha256'].values()) == list(pair[1]['recorded_input_sha256'].values())
assert {r['status'] for r in rows if r['input']=='CP1r2_tpu_ws'} == {'timeout'}
write(e/'seed_provenance.json', dict(passed=True, scope='Eight existing initial-route command manifests; metadata-only correction.',
    rows=rows, new_native_calls=0, new_STA_calls=0, new_independent_inputs=0,
    fresh_physical_byte_audit=False, candidate_admission=False,
    qualification='Directory seed labels describe upstream provenance and are not substituted for the actual VPR --seed. Different seeds alone do not establish distinct physical roots. CP1r2 TPU timeout is retained; this correction supplies no legal route or new quality evidence.',
    source_sha256={str(f):sha(f) for f in sorted(set(bound))}))
(e/'README.md').write_text('''# Actual router seeds and input provenance

This metadata correction changes no experiment, quantitative row or benefit claim.
The ledger binds eight original command manifests and the recorded physical input
identities; it does not rehash large physical files or re-execute native/STA work.

| Existing input | Native/domain actual router seed | Outcome scope |
|---|---:|---|
| Complete BNN engineering reference | 11 / 11 | Existing complete pair |
| Robot SDC, upstream placement label s23 | 11 / 11 | Existing complete no-gain pair |
| CP1r2 conv_hls | 21 / 21 | Existing complete no-op pair |
| CP1r2 tpu_ws | 21 / 21 | Existing initial-route timeouts, no legal QoR |

The upstream Robot s23 directory label is not its actual routing seed. The paper's
former blanket “router seed 11” caption was false for CP1r2. The corrected caption
says seeds vary by input. All other table evidence remains bound by the parent
snapshot. No new independent circuit, placement, architecture or complete result
is created by this editorial correction. Previously verified physical identities
and failed attempts retain their original qualifications.
''')
old = (previous/'current_repair_main.tex').read_text()
before = 'Hybrid-O except eltwise alternate-topology rows; router seed 11.'
after = 'Hybrid-O except eltwise topology rows; seeds vary by input.'
assert old.count(before) == 1
text = old.replace(before, after)
source = p/'current_repair_input_seeds_17.tex'
source.write_text(text)
write(e/'edit_registration.json', dict(parent=str(parent_path), source=str(source), changes=[[before,after]],
    main_table_rows=43, new_independent_inputs=0, new_native_calls=0, new_full_method_results=0,
    source_sha256={str(f):sha(f) for f in [Path(__file__).resolve(),parent_path,source,e/'seed_provenance.json',e/'README.md']}))
print(dict(source=str(source), command_manifests=len(rows), rows_unchanged=43, new_native_calls=0))
