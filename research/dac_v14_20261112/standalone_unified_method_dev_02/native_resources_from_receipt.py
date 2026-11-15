"""Consume explicitly native resource assurance; never relabel it an independent audit."""
from pathlib import Path
from retained_prefix_workflow import read,sha

def bound_native_resources(worker, kind='input'):
    """Return actual counts only from an immutable, matching native FULL/STA job."""
    assert kind in ['input','candidate','restored_source']
    job=Path(worker['job'])
    origin=read(job/'completion.json')
    keys=['static_identity','fingerprint','passed','route_sha256','native_directory','native_options',
          'artifact_sha256','native_resource_census_requested','native_seed_order','candidate_full_STA_passed',
          'native_transaction_succeeded']
    assert all(worker[key]==origin[key] for key in keys),'Native resource view differs from actual job receipt'
    registry=read(job.parent/'registration.json')
    assert origin['passed'] and origin['static_identity']==registry['identity']
    assert origin['native_resource_census_requested'] is True and registry['native_resource_census'] is True
    assert origin['native_seed_order']==registry['native_seed_order']
    assert origin['native_options']['native_resource_census'] is True
    assert sha(job/'routed.route')==origin['route_sha256'],'Frozen worker source changed'
    native=Path(origin['native_directory'])
    if kind!='input':
        assert origin['native_options']['operation'] in ['repair_fused','repair_feedback_fused']
        native=native/('candidate' if kind=='candidate' else 'candidate_restored')
        gate=native/'native_state_gate.txt'
        assert str(gate) in origin['artifact_sha256'] and sha(gate)==origin['artifact_sha256'][str(gate)]
        assert gate.read_text()==kind+' FULL fresh_STA actual_installed_trees\n'
        route=native/'routed.route'
        assert str(route) in origin['artifact_sha256'] and sha(route)==origin['artifact_sha256'][str(route)]
        if kind=='candidate':assert origin['candidate_full_STA_passed'] and origin['native_transaction_succeeded']
    path=native/'native_sta_frontier.jsonl.resources.json'
    assert str(path) in origin['artifact_sha256'] and sha(path)==origin['artifact_sha256'][str(path)]
    data=read(path)
    assert data['schema_version']==1 and data['assurance_kind']=='native_actual_route_tree_census' and data['state_kind']==kind
    metrics=data['physical_metrics']
    for key in ['planar_wirelength_excluding_sb_half_nodes','sb_pairs_used','sb_pair_net_occupancy',
                'cb_crossing_output_sources_used','cb_crossing_output_source_net_occupancy']:
        assert type(metrics[key]) is int and metrics[key]>=0
    assert all(isinstance(key,str) and type(value) is int and value>=0 for key,value in metrics['actual_crossing_edge_traversals'].items())
    return dict(assurance_kind='native_actual_route_tree_census',independent_physical_audit=False,
        state_kind=kind,physical_metrics=metrics,resource_axes=dict(wirelength=metrics['planar_wirelength_excluding_sb_half_nodes'],
            SB_pairs=metrics['sb_pairs_used'],CB_sources=metrics['cb_crossing_output_sources_used']),
        census_path=str(path),census_sha256=sha(path),origin_receipt=str(job/'completion.json'),origin_receipt_sha256=sha(job/'completion.json'),
        qualification='Counts bound to a real native FULL/freshSTA state and frozen controls. Endpoint-vector acceptance and final independent physical verification remain separate requirements; this is not a fabricated independent_audit.json.')
