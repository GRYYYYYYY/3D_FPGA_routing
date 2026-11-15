"""Explicit independent/native resource views for algorithm-private states.

Native counts never acquire an independent-audit label merely by being used for
acceptance. Publication of deferred states needs their separate final proof.
"""
from pathlib import Path
from retained_prefix_workflow import read,sha
from native_resources_from_receipt import bound_native_resources


def resource_assurance(state):
    state=Path(state).resolve();complete=read(state/'completion.json');assert complete['passed']
    run=Path(complete['run'])
    if complete.get('resource_assurance_policy')=='native_per_candidate_final_independent':
        path=run/'native_resource_assurance.json'
        assert sha(path)==complete['native_resource_assurance_sha256']
        data=read(path)
        assert data['passed'] and data['assurance_kind']=='native_actual_route_tree_census'
        assert data['independent_physical_audit'] is False
        assert sha(run/'routed.route')==data['actual_route_sha256']
        assert sha(run/'packed.net')==data['packed_sha256'] and sha(run/'placed.place')==data['placed_sha256']
        view=data['bound_native_view']
        assert sha(view['origin_receipt'])==view['origin_receipt_sha256']
        worker=read(view['origin_receipt'])
        bound=bound_native_resources(worker,view['state_kind'])
        assert bound==view,'Native state resource provenance differs from originating actual worker'
        return dict(passed=True,assurance_kind='native_actual_route_tree_census',
            independent_physical_audit=False,physical_metrics=bound['physical_metrics'],
            resource_axes=bound['resource_axes'],evidence=str(path),evidence_sha256=sha(path),
            publication_requires=str(state/'final_independent_validation.json'))
    path=run/'independent_audit.json';audit=read(path);assert audit['audit']['passed']
    m=read(run/'manifest.json')
    assert sha(run/'routed.route')==m['outputs']['routed.route']['sha256']
    metrics=audit['physical_metrics']
    return dict(passed=True,assurance_kind='independent_physical_audit',independent_physical_audit=True,
        physical_metrics=metrics,resource_axes=dict(wirelength=metrics['planar_wirelength_excluding_sb_half_nodes'],
            SB_pairs=metrics['sb_pairs_used'],CB_sources=metrics['cb_crossing_output_sources_used']),
        evidence=str(path),evidence_sha256=sha(path))


def require_publication_proof(state):
    """Fail closed on a deferred state without its own successful final audit."""
    state=Path(state).resolve();view=resource_assurance(state)
    if view['independent_physical_audit']:return view
    proof=read(state/'final_independent_validation.json')
    assert proof['passed'] and proof['state']==str(state)
    run=Path(read(state/'completion.json')['run'])
    assert proof['route_sha256']==sha(run/'routed.route')
    path=run/'independent_audit.json';assert sha(path)==proof['independent_audit_sha256']
    audit=read(path);assert audit['audit']['passed']
    assert all(audit['physical_metrics'][key]==value for key,value in view['physical_metrics'].items())
    seal=read(proof['context_input_seal'])
    assert seal['passed'] and seal['final_independently_validated_state']==str(state)
    return dict(view,publication_independently_validated=True,final_proof=str(state/'final_independent_validation.json'))
