#!/usr/bin/env python3
"""Collect the separately registered failure diagnosis without altering old data."""
import argparse
from collections import Counter, defaultdict
import csv
import datetime
import json
from pathlib import Path
import sys

from check_route import sha256
from collect_results import native_counters
from diagnose_failures import BASE, PLAN, ROOT, capacity_policy_file, set_option, source_key, write_json


def search_signature(history):
    # Wall-clock time depends on other concurrent processes. All other printed
    # counters, costs and QoR must agree along the deterministic common prefix.
    return [{k:v for k,v in row.items() if k!='seconds'} for row in history]


def collect(final=False,native_primary=False):
    protocol=ROOT/'configs/failure_diagnosis_native.json' if native_primary else PLAN
    plan=json.loads(protocol.read_text())
    state=json.loads((BASE/('native_state.json' if native_primary else 'state.json')).read_text())
    auxiliary=[]
    if native_primary:
        old=json.loads((BASE/'state.json').read_text())
        state['jobs']=[j for j in old['jobs'] if j['stage']=='off50']+state['jobs']
        auxiliary=[j for j in old['jobs'] if j['stage']=='off200' and j['state']!='not_run_after_amendment']
    reference_runs={(j['source_key'],j['budget']):j['output'] for j in state['jobs'] if j['width']==100}
    sources={source_key(s):s for s in plan['sources']}
    rows=[]; problems=[]; prefixes=[]; paired=defaultdict(set)
    audit_index={}
    for path in BASE.glob('audits*.json'):
        for row in json.loads(path.read_text()):audit_index[row['output']]=row
    if state['protocol_sha256']!=sha256(protocol):problems.append('Protocol hash mismatch')
    if final and 'finished_epoch' not in state:problems.append('Routing queue is incomplete')
    for job in state['jobs']:
        if job['stage'].startswith('prepare_'):continue
        if job['state'] in ['queued','running','not_run_after_amendment']:continue
        source=sources[job['source_key']]
        output=Path(job['output']);path=output/'manifest.json'
        if not path.exists():
            problems.append('No manifest: '+str(output));continue
        m=json.loads(path.read_text());old=source['manifest']
        expected_command=list(old['command'])
        for flag,value in [('--route_file',output/'routed.route'),('--routing_failure_predictor','off'),
                           ('--max_router_iterations',job['budget']),
                           ('--congested_routing_iteration_threshold',1 if native_primary else min(1,50/job['budget']))]:
            set_option(expected_command,flag,value)
        if job['width']!=100:
            set_option(expected_command,'--read_rr_graph',m['inputs']['rr_graph']['path'])
            set_option(expected_command,'--route_chan_width',job['width'])
        actual_command=list(m['command'])
        # The external native-schedule controls write 1.0; the owner writes 1.
        # Normalize that numeric spelling, leaving every other argument exact.
        for command in [expected_command,actual_command]:
            flag='--congested_routing_iteration_threshold'
            if flag in command:command[command.index(flag)+1]=str(float(command[command.index(flag)+1]))
        if expected_command!=actual_command:problems.append(job['id']+': unexpected command/solver parameter change')
        for key in ['binary','architecture','circuit','packed_netlist','placement']:
            if m['inputs'][key]!=old['inputs'][key]:
                problems.append(job['id']+': changed input '+key)
        if m['experimental_environment']!=old['experimental_environment']:
            problems.append(job['id']+': changed algorithm environment')
        if job['width']==100 and m['inputs']['rr_graph']!=old['inputs']['rr_graph']:
            problems.append(job['id']+': changed fixed graph')
        paired[(job['circuit'],job['width'])].add(tuple(m['inputs'][k]['sha256'] for k in
                                                     ['architecture','circuit','packed_netlist','placement','rr_graph']))
        log=(output/'vpr.log').read_text(errors='replace')
        counters,history=native_counters(log)
        metrics={**m['metrics'],**counters}
        native_ok=m['status']=='completed' and metrics.get('native_full_check_passed') and metrics.get('routing_success_reported')
        audit=audit_index.get(job['output'])
        if audit and (audit['inputs']['rr_graph_sha256']!=m['inputs']['rr_graph']['sha256'] or
                      audit['inputs']['route_sha256']!=m['outputs']['routed.route']['sha256']):
            problems.append(job['id']+': audit hash mismatch')
        if final and native_ok and (not audit or not audit['passed']):
            problems.append(job['id']+': native success lacks passing independent audit')
        if 'native_abort_reason' in metrics:problems.append(job['id']+': predictor unexpectedly aborted')
        if m['status']=='failed' and m['returncode']==2 and metrics.get('last_iteration')!=job['budget']:
            problems.append(job['id']+': failure before budget')
        row={k:job[k] for k in ['id','circuit','variant','stage','budget','width','source_key','output','original_output']}
        row.update(status=m['status'],returncode=m['returncode'],original_valid=source['original_valid'],
                   native_success=bool(native_ok),independent_audit_passed=bool(audit and audit['passed']),
                   valid_solution=bool(native_ok and audit and audit['passed']),
                   metrics=metrics,process_wall_seconds=m['process_wall_seconds'],
                   peak_rss_kib=m['peak_rss_kib'], input_hashes={k:v['sha256'] for k,v in m['inputs'].items()},
                   route_sha256=m.get('outputs',{}).get('routed.route',{}).get('sha256'))
        rows.append(row)
        if job['width']!=100:continue
        reference=Path(source['original_output'])
        if job['budget']>50:
            budget=50 if job['budget']==200 else 200
            reference=Path(reference_runs[(job['source_key'],budget)])
        ref_log=reference/'vpr.log'
        if not ref_log.exists():
            problems.append(job['id']+': absent prefix reference');continue
        ref_history=native_counters(ref_log.read_text(errors='replace'))[1]
        n=min(len(history),len(ref_history))
        a=search_signature(ref_history[:n]);b=search_signature(history[:n])
        mismatch=next((i+1 for i,(x,y) in enumerate(zip(a,b)) if x!=y),None)
        check=dict(id=job['id'],reference=str(reference),iterations_compared=n,passed=n>0 and mismatch is None,
                   first_mismatch_iteration=mismatch)
        if mismatch:check.update(reference_values=a[mismatch-1],actual_values=b[mismatch-1])
        if len(history)==len(ref_history) and m['status'] in ['completed','failed']:
            ref_manifest=json.loads((reference/'manifest.json').read_text())
            ref_hash=ref_manifest.get('outputs',{}).get('routed.route',{}).get('sha256')
            actual_hash=m.get('outputs',{}).get('routed.route',{}).get('sha256')
            check['same_stopping_point_route_byte_identical']=bool(ref_hash and ref_hash==actual_hash)
            if not check['same_stopping_point_route_byte_identical']:
                check['passed']=False
                problems.append(job['id']+': same stopping point has different route bytes')
        prefixes.append(check)
        if not check['passed']:problems.append(job['id']+': search prefix mismatch')
    for key,values in paired.items():
        if len(values)!=1:problems.append(str(key)+': algorithms did not share frozen inputs')
    by_source=defaultdict(dict)
    for r in rows:
        if r['width']==100:by_source[r['source_key']][r['budget']]=r
    classifications=[]
    capacity_policy_path=capacity_policy_file()
    capacity_policy=json.loads(capacity_policy_path.read_text()) if native_primary and capacity_policy_path.exists() else {'cases':{}}
    for case,proof in capacity_policy['cases'].items():
        for role in ['evidence','verification']:
            if sha256(proof[role])!=proof[role+'_sha256']:
                problems.append('Capacity certificate changed: '+case+'/'+role)
        verification=json.loads(Path(proof['verification']).read_text())
        certificate=json.loads(Path(proof['evidence']).read_text())['certificates'][proof['certificate_index']]
        if not verification['passed'] or verification['evidence_sha256']!=proof['evidence_sha256']:
            problems.append('Capacity certificate lacks matching verification: '+case)
        if certificate['circuit']!=case or not certificate['demand']>certificate['capacity']:
            problems.append('Invalid capacity inequality: '+case)
        for source in sources.values():
            if source['circuit']!=case:continue
            for role in ['rr_graph','packed_netlist','placement']:
                if source['manifest']['inputs'][role]['sha256']!=proof[role+'_sha256']:
                    problems.append('Capacity proof input mismatch: '+case+'/'+role)
    checkpoint_path=BASE/'native_500_checkpoint_attempts.json'
    checkpoint=None
    if native_primary and checkpoint_path.exists():
        interrupted=json.loads(checkpoint_path.read_text())
        checkpoint=dict(receipt=str(checkpoint_path),receipt_sha256=sha256(checkpoint_path),
                        statuses=dict(Counter(j['state'] for j in interrupted['jobs'])),
                        scope=interrupted['scope'])
    for key,s in sources.items():
        if s['original_valid']:continue
        trials=by_source[key]
        successful=next((trials[n] for n in [50,200,500] if n in trials and trials[n]['native_success']),None)
        if successful:
            cause={50:'predictor_only',200:'continued_search_51_200',500:'continued_search_201_500'}[successful['budget']]
            if s['circuit'] in capacity_policy['cases']:problems.append('Success contradicts capacity certificate: '+key)
        elif s['circuit'] in capacity_policy['cases']:cause='certified_resource_infeasible'
        elif 500 in trials:
            cause='censored_by_timeout' if trials[500]['status']=='timeout' else 'unresolved_at_500'
        else:cause='pending'
        classifications.append(dict(circuit=s['circuit'],variant=s['variant'],source_key=key,
                                    classification=cause,success_iteration=successful['metrics'].get('iterations') if successful else None,
                                    success_output=successful['output'] if successful else None,
                                    last_observed_iteration=trials[max(trials)]['metrics'].get('last_iteration') if trials else None,
                                    independent_audit_passed=successful['independent_audit_passed'] if successful else False))
    summaries=[]
    for stage in sorted(set(r['stage'] for r in rows)):
        subset=[r for r in rows if r['stage']==stage]
        summaries.append(dict(stage=stage,runs=len(subset),native_success=sum(r['native_success'] for r in subset),
                              audited_success=sum(r['valid_solution'] for r in subset),
                              statuses=dict(Counter(r['status'] for r in subset))))
    supplemental=[]
    for queue_path in sorted(BASE.glob('schedule_controls*.json')):
        comparison=BASE/queue_path.name.replace('schedule_controls','schedule_comparison')
        if comparison.exists():
            extra=json.loads(comparison.read_text())
            if not extra['complete']:problems.append('Incomplete schedule controls: '+str(comparison))
            for row in extra['rows']:
                if row['valid_solution'] and not (row['metrics'].get('native_full_check_passed') and
                                                  row['metrics'].get('routing_success_reported')):
                    problems.append('Supplemental success lacks native FULL check: '+row['output'])
            supplemental.append(extra)
        elif final:problems.append('Pending schedule controls: '+str(queue_path))
    auxiliary_rows=[]
    for job in auxiliary:
        m=json.loads((Path(job['output'])/'manifest.json').read_text())
        checked=audit_index.get(job['output'])
        native_ok=m['status']=='completed' and m['metrics'].get('native_full_check_passed') and m['metrics'].get('routing_success_reported')
        audit_ok=bool(checked and checked['passed'])
        if final and native_ok and not audit_ok:problems.append('Auxiliary successful route lacks audit: '+job['output'])
        auxiliary_rows.append(dict(circuit=job['circuit'],variant=job['variant'],output=job['output'],
                                   status=m['status'],budget=200,congestion_mode_after_iteration=50,
                                   native_success=bool(native_ok),valid_solution=bool(native_ok and audit_ok),metrics=m['metrics']))
    feasible_cases=sorted(set(r['circuit'] for r in rows if r['width']==100 and r['valid_solution']) |
                          set(r['circuit'] for r in auxiliary_rows if r['valid_solution']))
    if set(feasible_cases)&set(capacity_policy['cases']):problems.append('Audited route contradicts capacity certificate')
    for row in classifications:row['graph_has_audited_w100_solution']=row['circuit'] in feasible_cases
    result=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),provisional=not final,
                protocol_sha256=sha256(protocol),stage=state['active_stage'],
                primary_mode='native default congestion scheduling' if native_primary else 'fixed high-effort transition after 50',
                original_failure_classifications=dict(Counter(r['classification'] for r in classifications)),
                paired_inputs_verified=all(len(x)==1 for x in paired.values()),
                command_parameters_verified=not any('command/solver parameter' in p for p in problems),
                prefix_checks=prefixes,prefix_checks_passed=all(x['passed'] for x in prefixes),
                prefix_scope='Compare iteration, pres_fac, bbox_updates, printed heap_pushes, nets_routed, connections_routed, overused_resources, wirelength, printed critical_path_ns. Printed large heap counts are rounded; equal stopping points additionally require byte-identical route hashes.',
                summaries=summaries,classifications=classifications,rows=rows,problems=problems,
                supplemental_schedule_controls=supplemental,
                supplemental_controls_already_in_primary_rows=native_primary,
                width_execution_schedule=state.get('width_execution_schedule','Sequential width stages'),
                auxiliary_high_effort=auxiliary_rows,known_feasible_w100_cases=feasible_cases,
                capacity_certificates=capacity_policy['cases'],skipped_500_certified=state.get('skipped_500_certified',[]),
                capacity_checkpoint=checkpoint,
                inference_limits=plan['inference_limits'],timing_scope=plan['timing_scope'])
    stem='analysis_native' if native_primary else 'analysis'
    write_json(BASE/(stem+'.json'),result)
    fields=['circuit','variant','stage','width','budget','status','native_success','independent_audit_passed',
            'iterations','last_iteration','last_overused_resources','critical_path_ns','wirelength','output']
    with (BASE/(stem+'.csv')).open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader()
        for row in rows:writer.writerow({k:row.get(k,row['metrics'].get(k)) for k in fields})
    print(json.dumps({k:result[k] for k in ['provisional','stage','original_failure_classifications',
                                          'summaries','prefix_checks_passed','problems']},ensure_ascii=False,indent=2))
    if problems:raise RuntimeError('Diagnosis evidence validation failed')


def audit_matrix(native_primary=False):
    state=json.loads((BASE/('native_state.json' if native_primary else 'state.json')).read_text())
    if 'finished_epoch' not in state:raise RuntimeError('Wait for routing queue completion')
    if native_primary:
        old=json.loads((BASE/'state.json').read_text())
        state['jobs']=old['jobs']+state['jobs']
    jobs=[j for j in state['jobs'] if not j['stage'].startswith('prepare_') and j['state']=='completed']
    write_json(BASE/('audit_matrix_native.json' if native_primary else 'audit_matrix.json'),dict(jobs=jobs,finished_epoch=state['finished_epoch']))
    print('Native successful runs to audit:',len(jobs))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--final',action='store_true')
    parser.add_argument('--audit-matrix',action='store_true')
    parser.add_argument('--native-primary',action='store_true')
    args=parser.parse_args()
    if args.audit_matrix:audit_matrix(args.native_primary)
    else:collect(args.final,args.native_primary)
