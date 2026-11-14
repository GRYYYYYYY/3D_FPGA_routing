#!/usr/bin/env python3
"""New independent controller: native query workers, bundles and native-only selector ablation."""
from retained_prefix_workflow import D
s=(D/'run_pooled_resource_repair.py').read_text();s=s.replace('from native_analysis_pool_v2 import NativeAnalysisPool','from native_repair_analysis_pool import NativeAnalysisPool').replace('from pool_state_evaluator import PoolStateEvaluator','from pool_state_evaluator_v2 import PoolStateEvaluator');s=s.replace("p.add_argument('--batch',type=Path,required=True);a=p.parse_args()", "p.add_argument('--batch',type=Path,required=True);p.add_argument('--bundle-size',type=int,default=1);p.add_argument('--domain-mode',choices=['paired','unrestricted'],default='paired');a=p.parse_args();assert a.bundle_size>0")
s=s.replace("assert read(D/'pool_state_evaluator_bnn_01/completion.json')['passed']", "assert read(D/'native_repair_queue_equivalence_bnn_01/completion.json')['passed']")
s=s.replace('analysis_queue_stage_01/bin/vpr','native_repair_queue_stage_01/bin/vpr');s=s.replace("D/'native_analysis_pool_v2.py'","D/'native_repair_analysis_pool.py'").replace("D/'pool_state_evaluator.py'","D/'pool_state_evaluator_v2.py'").replace("D/'pool_state_evaluator_bnn_01/completion.json'","D/'native_repair_queue_equivalence_bnn_01/completion.json'").replace("D/'resource_domain_stage_01/native_validation_binding_01.json'","D/'native_repair_queue_stage_01/binding.json'")
s=s.replace("initial_state=str(initial),anchor=anchor,resource_objectives", "initial_state=str(initial),bundle_size=a.bundle_size,domain_mode=a.domain_mode,anchor=anchor,resource_objectives")
s=s.replace("selection='Uniform current-state crossing rank; fresh own STA after every accepted state; at most first three scopes examined per current-state integration probe.'", "selection='Uniform current-state rank; at most first three rank windows, distinct-net cuts within each bundle; fresh own STA after every final accepted transaction.'")
s=s.replace("question='Does resource sharing remain useful after fast timing repair and stronger native reconvergence, can two independently selected resource moves compose, and does dynamic native FULLSTA integrate without changing physical/acceptance semantics?'", "question='Can a distinct-net release bundle amortize full validation while preserving fixed timing/resource conditions, and does the same own-current native-only selector attain the same or another joint frontier?' ")
old="""  for ci,candidate in enumerate(candidates[:3]):
   tx=round_dir/f'candidate_{ci:02d}';tx.mkdir();net=candidate['net'];pins=candidate['pins'];request=tx/'request.txt';request.write_text('1\\n'+' '.join(map(str,[net,len(pins),*pins]))+'\\n0\\n'+str(len(pins))+'\\n'+''.join(f"{q['net']} {q['pin']} {q['raw_criticality']:.17g}\\n" for q in candidate['ordered_queries']));domain=tx/'domain.txt';domain.write_text('1\\n'+str(net)+'\\n');roles={}
   for enabled in [False,True]:
    name='reuse_'+('on' if enabled else 'off');roles[name]=dict(state=str(current),source=str(run_dir(current)),request=str(request),objective='weighted_soft',fixed_target_paths=False,queries=candidate['ordered_queries'],removed_pins={str(net):pins},crossing_reuse_enabled=enabled,crossing_domain=str(domain),source_sha256={str(p):sha(p) for p in [current/'completion.json',current/'endpoint_vector.json',run_dir(current)/'routed.route',request,domain]})"""
new="""  for ci in range(min(3,len(candidates))):
   selected=[];selected_nets=set()
   for candidate in candidates[ci:]:
    if candidate['net'] in selected_nets:continue
    selected_nets.add(candidate['net']);selected.append(candidate)
    if len(selected)==a.bundle_size:break
   if not selected:continue
   tx=round_dir/f'candidate_{ci:02d}';tx.mkdir();net=selected[0]['net'];pins=selected[0]['pins'];queries=sorted([q for cut in selected for q in cut['ordered_queries']],key=lambda q:(-q['raw_criticality'],q['net'],q['pin']));removed={str(cut['net']):cut['pins'] for cut in selected};request=tx/'request.txt';request.write_text(str(len(selected))+'\\n'+''.join(' '.join(map(str,[cut['net'],len(cut['pins']),*cut['pins']]))+'\\n' for cut in selected)+'0\\n'+str(len(queries))+'\\n'+''.join(f"{q['net']} {q['pin']} {q['raw_criticality']:.17g}\\n" for q in queries));domain=tx/'domain.txt';domain.write_text(str(len(selected))+'\\n'+''.join(str(cut['net'])+'\\n' for cut in selected));roles={}
   for enabled in ([False,True] if a.domain_mode=='paired' else [False]):
    name='reuse_'+('on' if enabled else 'off');roles[name]=dict(state=str(current),source=str(run_dir(current)),request=str(request),objective='weighted_soft',fixed_target_paths=False,queries=queries,removed_pins=removed,crossing_reuse_enabled=enabled,crossing_domain=str(domain),source_sha256={str(p):sha(p) for p in [current/'completion.json',current/'endpoint_vector.json',run_dir(current)/'routed.route',request,domain]})"""
assert old in s;s=s.replace(old,new)
old="""    seen_requests.add(key);extra=['--crossing-domain',domain] if role['crossing_reuse_enabled'] else [];ok=invoke('run_resource_domain_state_analysis.py',['--source',run_dir(current),'--batch',tx/name,'--native-cases',request,'--objective','weighted_soft',*extra],f'{len(steps):03d}_{ci:02d}_{name}_native')
    if ok:
     unchanged=read(tx/name/'endpoint_vector.json');assert all(unchanged[k]==before[k] for k in ['cpd_s','setup','hold','endpoint_ids','constraints_sha256']);ok=invoke('audit_native_objective_cached.py',['--batch',tx,'--role',name,'--cache',D/'rr_audit_cache_bnn_01','--output',tx/(name+'_audit')],f'{len(steps):03d}_{ci:02d}_{name}_transaction_audit')"""
new="""    seen_requests.add(key);native_started=time.monotonic();worker=pool.analyze(run_dir(current)/'routed.route',native_request=request,objective='weighted_soft',crossing_domain=domain if role['crossing_reuse_enabled'] else None);write(tx/(name+'_worker_receipt.json'),worker);costs.append(dict(tag=f'{len(steps):03d}_{ci:02d}_{name}_native_worker_request',status='completed' if worker['passed'] else 'failed',complete_process_seconds=time.monotonic()-native_started));persist();ok=worker['passed']
    if ok:
     material=evaluator.evaluate(run_dir(current)/'routed.route',tx/name,physical_reference=current,native_observation=worker);ok=material['passed']
    if ok:
     unchanged=read(tx/name/'endpoint_vector.json');assert all(unchanged[k]==before[k] for k in ['cpd_s','setup','hold','endpoint_ids','constraints_sha256']);ok=invoke('audit_native_objective_cached.py',['--batch',tx,'--role',name,'--cache',D/'rr_audit_cache_bnn_01','--output',tx/(name+'_audit')],f'{len(steps):03d}_{ci:02d}_{name}_transaction_audit')"""
assert old in s;s=s.replace(old,new)
s=s.replace("sha(D/'resource_domain_stage_01/bin/vpr')","sha(D/'native_repair_queue_stage_01/bin/vpr')")
s=s.replace("net=net,pins=pins,pair=pair", "net=net,pins=pins,bundle_removed_pins=removed,bundle_actual_nets=len(selected),pair=pair")
s=s.replace("Independent automatic selector→native paired transaction", "Independent automatic current selector→native request pool→whole multi-net transaction")
(D/'run_pooled_native_bundle_repair.py').write_text(s)
