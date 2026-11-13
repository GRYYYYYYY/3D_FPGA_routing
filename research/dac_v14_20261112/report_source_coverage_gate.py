#!/usr/bin/env python3
"""Matched old/new-score gate effects; separate information loss from final QoR."""
import collections,csv,math
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body
from analyze_native_reconvergence_v2 import observe
from analyze_candidate_path_score import parse
from verify_path_witnesses_v2 import fields

def main():
    b=D/'source_coverage_gate_eltwise_dev_01';audit=b/'source_coverage_analysis.json';assert read(audit)['passed'];assert read(b/'input_seal.json')['passed']
    dirs={a:b/'runs'/('eltwise_layer_'+a) for a in ['F','G','E','N']};logs={a:(p/'stdout.log').read_text().splitlines() for a,p in dirs.items()};data={a:parse(ls)[0] for a,ls in logs.items()}
    out=D/'source_coverage_gate_summary_01.json';assert not out.exists();obs=[dict(observe(Path(p)),arm=a,reused=True) for a,p in read(b/'registration.json')['references'].items()]
    obs += [dict(observe(p),arm=a,reused=False) for a,p in dirs.items()]
    e=D/'source_empty_reverse_eltwise_dev_01';assert read(e/'source_empty_analysis.json')['passed'];obs += [dict(observe(e/'runs'/('eltwise_layer_'+a)),arm='empty_'+a,reused=False) for a in ['C','R']]
    pairs={}
    for c,t in [('G','E'),('F','N')]:
        before=next(r for r in obs if r['arm']==c);after=next(r for r in obs if r['arm']==t);comparable=before['status']==after['status']=='legal';changes=[];decision_changes=0
        for key,v in data[t].items():
            old=data[c].get(key)
            if not old or not v['decision'] or not old['decision']:continue
            proposal=lambda x:{(pin,entry) for pin,ps in x['pairs'].items() for entry,r in ps.items() if r['proposed']=='1'}
            if proposal(v)!=proposal(old):changes.append(dict(plan=key[0],net=key[1],accepted=v['decision']['accepted']=='1',control_accepted=old['decision']['accepted']=='1'))
            decision_changes+=v['decision']['accepted']!=old['decision']['accepted']
        counters={}
        for a in [c,t]:
            def final(tag):return fields(next(l for l in reversed(logs[a]) if l.startswith(tag+' ')))
            counters[a]=dict(delay=final('H3D_DELAY'),fresh=final('H3D_CANDIDATE_PATH_SUMMARY'),capture=final('H3D_CANDIDATE_PATH_CAPTURE'),score=final('H3D_PATH_PRICE_SCORE_SUMMARY') if any(l.startswith('H3D_PATH_PRICE_SCORE_SUMMARY ') for l in logs[a]) else None,physical=final('H3D_PATH_DELAY_SUMMARY') if any(l.startswith('H3D_PATH_DELAY_SUMMARY ') for l in logs[a]) else None,gate=final('H3D_SOURCE_COVERAGE_SKIP_SUMMARY') if a in ['E','N'] else None)
        pairs[c+'->'+t]=dict(both_legal=comparable,cpd_improvement_pct=(1-after['legal_cpd_ns']/before['legal_cpd_ns'])*100 if comparable else None,
            same_complete_route=route_body(dirs[c]/'routed.route')==route_body(dirs[t]/'routed.route') if comparable else None,same_final_guides=sha(dirs[c]/'h3d_final_guides.csv')==sha(dirs[t]/'h3d_final_guides.csv') if comparable else None,
            same_all_base_table_fingerprints=[l for l in logs[c] if l.startswith('H3D_TABLE ')]==[l for l in logs[t] if l.startswith('H3D_TABLE ')],same_all_prefix_tables_and_decisions=[l for l in logs[c] if l.startswith('H3D_PREFIX_')]==[l for l in logs[t] if l.startswith('H3D_PREFIX_')],proposal_changed_plans=len(changes),accepted_changed_proposals=sum(x['accepted'] for x in changes),acceptance_changes=decision_changes,changed_proposals=changes,counters=counters)
    inputs=[Path(__file__),audit,b/'input_seal.json',b/'completion.json',b/'registration.json',e/'source_empty_analysis.json',D/'source_empty_exercise_classification_01.json']+[p/n for p in dirs.values() for n in ['manifest.json','stdout.log','h3d_final_guides.csv','independent_audit.json','final_guide_audit.json']]
    result=dict(status='sealed_source_coverage_gate_development_report',observations=obs,status_counts=dict(collections.Counter(r['status'] for r in obs)),pairs=pairs,source_empty_requests=read(D/'source_empty_exercise_classification_01.json')['requests'],availability_oracle=read(audit)['source_coverage_gate'],source_sha256={str(p):sha(p) for p in inputs},qualification='One seen circuit/seed. Four strictly matched native references and six new roles, including the zero-exercise source-empty diagnostic. Changed query-only records are expected even under old-score objective equivalence. Score/table/guide differences and final physical CPD analyzed separately. Ordered costs are not formal timing; broader failures retained.')
    write(out,result)
    p=D/'paper/data/source_coverage_gate_v14.csv';assert not p.exists()
    with p.open('w') as stream:
        w=csv.writer(stream);w.writerow(['arm','reused','status','cpd_ns','iterations','SB','CB','planning_seconds','router_seconds','process_seconds'])
        for r in obs:
            ph=r['physical_metrics'] or {};w.writerow([r['arm'],r['reused'],r['status'],r['legal_cpd_ns'],r['iterations'],ph.get('sb_pair_net_occupancy'),ph.get('cb_crossing_output_source_net_occupancy'),r['planning_seconds'],r['router_seconds'],r['process_seconds']])
    write(D/'source_coverage_gate_report_binding_01.json',dict(status='sealed_report',report_sha256=sha(out),exporter_sha256=sha(Path(__file__)),artifacts_sha256={str(p.relative_to(D)):sha(p)}))
    print({k:{n:r[n] for n in ['cpd_improvement_pct','same_complete_route','same_final_guides','same_all_base_table_fingerprints','same_all_prefix_tables_and_decisions','proposal_changed_plans','accepted_changed_proposals','acceptance_changes']} for k,r in pairs.items()})

if __name__=='__main__':main()
