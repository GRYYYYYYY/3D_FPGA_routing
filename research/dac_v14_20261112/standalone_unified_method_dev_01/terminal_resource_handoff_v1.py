"""Choose an actual same-flow terminal wire alternative without altering the resource actor."""
from pathlib import Path
from retained_prefix_workflow import read,sha
from state_resource_assurance import require_publication_proof
from endpoint_timing_policy_streaming_v2 import compare

def choose(resource_flow,selection):
    resource_flow=Path(resource_flow).resolve();selection=Path(selection).resolve()
    closed=read(resource_flow/'completion.json');assert closed['passed']
    original=Path(closed['final_state']).resolve();record=read(selection/'completion.json')
    assert record['passed'] and record['mode']=='endpoint'
    assert Path(record['actor']).resolve()==resource_flow/'repair' and Path(record['state']).resolve()==original
    assert all(sha(f)==h for f,h in record['source_sha256'].items())
    if record['selected'] is None:target=original
    else:
        target=Path(record['selected']['state']).resolve();assert target.is_relative_to(resource_flow)
        a,b=[require_publication_proof(s)['resource_axes'] for s in [original,target]]
        assert all(a[k]==b[k] for k in ['SB_pairs','CB_sources']) and b['wirelength']<a['wirelength']
        cp=compare(read(original/'endpoint_vector.json'),read(target/'endpoint_vector.json'))
        assert cp['compatible'] and cp['cpd_nonworse'] and cp['setup_regressed']==cp['hold_violation_regressions']==0
    return dict(passed=True,resource_policy_final_state=str(original),selected_resource_state=str(target),changed=target!=original,terminal_wire_commits=int(target!=original),selection=str(selection/'completion.json'),selection_sha256=sha(selection/'completion.json'),original_actor_unchanged=True,qualification='Only actual candidates evaluated inside this measured resource flow are eligible. The original vertical-policy terminal and its decisions remain unchanged; the outer algorithm selects an optional endpoint-nonregressing wire improvement before its own timing phase. No external route/candidate/query history or historical cost imported.')
