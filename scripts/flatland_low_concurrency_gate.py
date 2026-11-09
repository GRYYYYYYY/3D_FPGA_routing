"""Prove the frozen training queue can use at most three further VPR slots."""
from flatland_benchmark import BASE,read
from lazagna_common import ROOT,sha256


def ready():
    protocol=read(BASE/'training_continuation_protocol.json')
    assert protocol['source_sha256']==sha256(ROOT/'scripts/continue_flatland_training.py')
    batches=protocol['batches']
    assert batches[0]==dict(circuits=['attention_layer','softmax'],workers=6)
    assert all(batch['workers']<=3 for batch in batches[1:])
    state=read(BASE/'training_continuation_state.json')
    if state['status']=='error':raise RuntimeError('Training supervisor requires diagnosis')
    for family in ['sb','cb_o','hybrid_o']:
        directory=BASE/'training_cases'/('softmax_'+family)
        path=directory/'result.json'
        if not path.exists():return False
        assert read(path)['status']=='completed',path
        audit=read(directory/'audit_summary.json')
        assert audit['passed'] and audit['registered_route_count']==33
    # The six-case attention/softmax batch has no other queued cases. Its
    # three softmax cases are terminal after audit, leaving at most three
    # attention VPRs. Every later frozen batch has a <=3-worker budget.
    if state['status']=='running_training' and state['workers']>3:
        assert state['circuits']==['attention_layer','softmax'] and state['workers']==6
    return True
