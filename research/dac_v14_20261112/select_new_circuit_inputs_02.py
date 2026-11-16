"""Bind two different historical circuit/layout candidates without using QoR.

Only provenance metadata and existence are checked while the experiment slot is
busy. Full physical byte checks/provisioning, interpretation admission and fixed
paired runtime registration remain required before any native execution.
"""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
repo=D.parents[1];runs=repo/'results/architecture_flow_20261027/runs';out=D/'independent_input_candidates_02'
assert not out.exists();out.mkdir()
selected=[('lstm','heldout_lstm_s21_hybrid_o_n125_w100_p0'),('dla_like.small','heldout_dla_like.small_s21_hybrid_o_n100_w100_p0')]
reference=D/'mechanism_selection_evidence_01/pairs.json';known={r['native']['declared_physical_identity']['circuit'] for r in read(reference)}
records=[];files=[Path(__file__).resolve(),reference]
for circuit,stem in selected:
    route=runs/(stem+'_a0');packing=runs/(stem+'_place');manifest=route/'manifest.json';provenance=packing/'manifest.json'
    m=read(manifest);p=read(provenance);command=m['command'];pack_command=p['command']
    netlist=Path(command[2]);architecture=Path(command[1]);graph=Path(command[command.index('--read_rr_graph')+1])
    assert command[command.index('--merge_constant_generators')+1]=='off'
    assert pack_command[pack_command.index('--merge_constant_generators')+1]=='off'
    assert m['outputs']['packed.net']['sha256']==p['outputs']['packed.net']['sha256']
    assert m['outputs']['placed.place']['sha256']==p['outputs']['placed.place']['sha256']
    assert all((route/name).is_file() for name in ['packed.net','placed.place'])
    assert all(f.is_file() for f in [netlist,architecture,graph])
    circuit_sha=m['shared_inputs'][str(netlist)]['sha256'];assert circuit_sha not in known
    records.append(dict(circuit=circuit,source_run=str(route),packing_provenance=str(provenance),
        physical_files=dict(circuit=str(netlist),architecture=str(architecture),graph=str(graph),packed=str(route/'packed.net'),placement=str(route/'placed.place')),
        declared_sha256=dict(circuit=circuit_sha,architecture=m['shared_inputs'][str(architecture)]['sha256'],graph=m['shared_inputs'][str(graph)]['sha256'],
            packed=m['outputs']['packed.net']['sha256'],placement=m['outputs']['placed.place']['sha256']),
        merge_constant_generators='off',source_packing_metadata_matches=True,known_historical_input=True,
        historical_QoR_not_used_for_selection=True,previous_route_will_not_be_imported=True,explicit_SDC=False,
        family='two_layer_edge_encoded_Hybrid_O',different_device_size_is_not_new_architecture_family=True,
        physical_bytes_rechecked=False,placement_coordinate_normalization_pending=True,prospective_runtime_or_config_registered=False))
    files += [manifest,provenance]
assert len({r['declared_sha256']['circuit'] for r in records})==2
write(out/'inputs.json',records)
write(out/'completion.json',dict(passed=True,status='candidate_provenance_metadata_only',candidate_circuits=2,
    declared_netlists_differ_from_all_ten_context_matrix=True,packing_and_route_metadata_agree=True,
    new_native_calls=0,new_independent_results=0,registered_execution_roles=0,physical_byte_admission_pending=True,
    source_sha256={str(f):sha(f) for f in files},artifact_sha256={'inputs.json':sha(out/'inputs.json')},
    selection='LSTM and DLA-like.small seed21/p0 actual historical packed/placed inputs, chosen by different circuit identities and available provenance, not routing quality. Keep failures if full provisioning/admission fails; no replacement chosen from new outcomes.',
    qualification='Provenance declarations/existence only, no original QoR consulted or raw graph/route/STA loaded. Both are known historical circuits and Hybrid-O, not unseen data or new architecture families. Future fixed CP1r3 pairing needs actual physical hashes/placement identity, new release/config admission, normal fixed routing opportunities, fresh roots and complete outcome/cost accounting. No current queue or frozen rule changes.'))
print(dict(passed=True,candidates=[r['circuit'] for r in records],new_results=0,physical_admission_pending=True))
