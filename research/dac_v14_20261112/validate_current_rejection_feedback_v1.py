"""Check the actual known request and donor-exclusion boundary cases."""
import hashlib
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from current_rejection_feedback_v1 import selected_actions
from current_proposal_portfolio import request_text

out=D/'current_rejection_feedback_validation_01'
generated=read(out/'portfolio.json');assert generated['passed'] and len(generated['proposals'])==1
plan=read(generated['proposals'][0]['plan']);old=D/'vector_feedback_subset_01/plan.json'
assert request_text(plan)==request_text(read(old)), 'Generic controller changed the known actual native request'
assert hashlib.sha256(request_text(plan).encode()).hexdigest()==read(D/'vector_feedback_subset_01/completion.json')['new_request_sha256']
actions=[dict(target=[1,1],donors=[[3,1]]),dict(target=[2,1],donors=[[4,1]])]
changes=[dict(net=1,pin=1,before_s=2.,after_s=1.),dict(net=2,pin=1,before_s=2.,after_s=1.),dict(net=3,pin=1,before_s=1.,after_s=2.)]
assert selected_actions(actions,changes)[0]==[1]
assert selected_actions(actions,changes+[dict(net=4,pin=1,before_s=1.,after_s=2.)])[0]==[]
assert selected_actions(actions,[dict(net=2,pin=1,before_s=1.,after_s=1.)])[0]==[]
shared=[dict(target=[1,1],donors=[[3,1]]),dict(target=[2,1],donors=[[3,1]])]
assert selected_actions(shared,changes)[0]==[]
write(out/'completion.json',dict(passed=True,actual_native_request_exact=True,
    checks=['known_actual_five_connection_request_exact','bad_donor_action_excluded','all_bad_donors_empty',
            'flat_target_excluded','shared_bad_donor_excludes_all_dependent_actions'],native_calls=0,
    source_sha256={str(p):sha(p) for p in [Path(__file__).resolve(),D/'current_rejection_feedback_v1.py',
        D/'run_independent_critical_portfolio_v5.py',out/'portfolio.json',Path(generated['proposals'][0]['plan']),old]},
    qualification='Proposal reproduction and boundary cases only. Controller trajectory and new-state quality require separate live validation; the historical five-connection experiment is not a new independent sample.'))
print('actual request and four donor-exclusion boundary checks passed',flush=True)
