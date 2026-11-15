"""Circuit-independent same-source feedback proposal; acceptance remains external."""
import argparse
import hashlib
import json
from pathlib import Path
from retained_prefix_workflow import read,write,sha
from critical_action_patterns import patterns,evaluate
from current_proposal_portfolio import request_text
from run_native_scope_policy_v4 import run_dir

def selected_actions(actions,changes):
    bad={(r['net'],r['pin']) for r in changes if r['after_s']>r['before_s']}
    improved={(r['net'],r['pin']) for r in changes if r['after_s']<r['before_s']}
    chosen=[i for i,a in enumerate(actions) if tuple(a['target']) in improved
            and not (set(map(tuple,a['donors'])) & bad)]
    return chosen,bad

def generate(base_path,attempts_path,portfolio_path,output):
    base_path,attempts_path,portfolio_path,output=map(Path,[base_path,attempts_path,portfolio_path,output])
    output.mkdir(exist_ok=False)
    base=read(base_path);menu=read(portfolio_path);state=Path(base['source_state']).resolve()
    assert base['passed'] and Path(menu['source_state']).resolve()==state
    assert all(sha(p)==h for p,h in base['source_sha256'].items())
    snapshot=output/'observed_attempts.json'
    snapshot.write_bytes(attempts_path.read_bytes())
    attempts=read(snapshot)
    files=[Path(__file__).resolve(),base_path,snapshot,portfolio_path]
    proposals=[];reason='no_rejected_same_source_aggregate'
    for row in attempts:
        if row.get('accepted') or row.get('proposal')!='all_positive_combined' or not row.get('evaluation'):continue
        if Path(row['before_state']).resolve()!=state:continue
        evaluation=Path(row['evaluation']);tx=evaluation.parent
        assert read(evaluation/'completion.json')['passed'] and read(evaluation/'input_seal.json')['passed']
        reg=read(tx/'registration.json')['roles']['current_group']
        assert Path(reg['state']).resolve()==state
        audit_path=tx/'current_group_audit/analysis.json';audit=read(audit_path)
        assert audit['passed'] and audit['candidate_route']
        assert all(sha(p)==h for p,h in audit['source_sha256'].items())
        assert sha(audit['candidate_route'])==audit['candidate_sha256']
        files += [evaluation/'completion.json',evaluation/'input_seal.json',tx/'registration.json',audit_path]
        chosen,bad=selected_actions(base['actions'],audit['changed_delays'])
        if not chosen:reason='all_observed_improving_actions_excluded_by_donor_feedback';break
        cones=[Path(p) for p in base['source_sha256'] if Path(p).name=='cone.json']
        assert len(cones)==1
        cone=read(cones[0]);assert cone['passed'] and Path(cone['source_state']).resolve()==state
        profile=evaluate(patterns(cone,base['actions']),base['actions'],chosen)
        if not profile['all_current_paths_covered']:reason='remaining_actions_do_not_cover_current_tied_paths';break
        pins=set(map(tuple,profile['repair_pins']));targets={tuple(base['actions'][i]['target']) for i in chosen}
        sta={};frontier=run_dir(state)/'native_sta_frontier.jsonl'
        for line in frontier.open():
            item=json.loads(line)
            if item.get('type')=='pin' and (item['net'],item['pin']) in pins:
                assert not item['driver'] and not item['ignored'] and not item['global'] and item['route_tree_present']
                sta[item['net'],item['pin']]=item
                if sta.keys()==pins:break
        assert sta.keys()==pins
        files += [cones[0],frontier,state/'endpoint_vector.json']
        ordered=sorted(targets,key=lambda key:(sta[key]['setup_slack_s'],key))+sorted(pins-targets)
        plan=dict(passed=True,source_state=str(state),actions=[base['actions'][i] for i in chosen],
            selection=dict(status='same_state_rejected_candidate_feedback_subset',targets=sorted(targets),
                fraction=base['selection']['fraction'],profile=profile),repair_pins=sorted(pins),
            ordered_queries=[dict(net=n,pin=p,raw_criticality=sta[n,p]['setup_criticality_raw']) for n,p in ordered],
            source_sha256={str(p.resolve()):sha(p) for p in files},native_calls=0,accepted=False,
            qualification='Observed aggregate feedback is a proposal heuristic. Smaller-group occupancy/order can change. Fresh or exactly reused actual candidate FULL/STA and unchanged root policy decide acceptance.')
        digest=hashlib.sha256(request_text(plan).encode()).hexdigest()
        if digest in {p['request_sha256'] for p in menu['proposals']}:reason='exact_request_already_in_current_menu';break
        path=output/'feedback.plan.json';write(path,plan)
        proposals=[dict(name='same_source_rejection_feedback',plan=str(path.resolve()),request_sha256=digest,repair_connections=len(pins))]
        reason='new_same_source_feedback_request';break
    result=dict(passed=True,source_state=str(state),proposals=proposals,reason=reason,
        source_sha256={str(p.resolve()):sha(p) for p in files},native_calls=0,
        qualification='Fixed rule from current rejected aggregate only; no circuit IDs or future outcomes. Full-vector/strict/resource policies and physical delay unchanged.')
    write(output/'portfolio.json',result)
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ['base-plan','attempts','portfolio','output']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();r=generate(a.base_plan,a.attempts,a.portfolio,a.output)
    print(dict(proposals=len(r['proposals']),reason=r['reason']),flush=True)
