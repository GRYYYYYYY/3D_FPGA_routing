"""Apply both fixed terminal modes to the same thirteen already closed real menus."""
import os,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from seed_census_analysis_pool_v2 import process_identity
from select_terminal_resource_alternative_v2 import select

out=D/'terminal_timing_envelope_policy_01';out.mkdir(exist_ok=False)
refs=[D/'BNN_terminal_wire_alternative_01/completion.json']+[D/'terminal_wire_selector_merge_validation_01'/n/'completion.json' for n in ['eltwise_native','spmv_domain','softmax_domain','SB102_domain']]
menus={};legacy={}
for index,ref in enumerate(refs):
 r=read(ref);assert r['passed'];name='legacy_'+str(index);menus[name]=Path(r['actor']);legacy[name]=ref
proof=D/'closed_seed_transfer_eight_roles_01.json';rootproof=read(proof);assert rootproof['passed']
for label,pair in rootproof['matched_own_current_pairs'].items():
 for role in ['native','paired']:menus[label+'_'+role]=Path(pair[role]['actor'])
files=[Path(__file__).resolve(),D/'select_terminal_resource_alternative_v2.py',D/'select_terminal_resource_alternative_v1.py',proof,*refs]
bindings={str(f):sha(f) for f in files};write(out/'registration.json',dict(pid=os.getpid(),start_ticks=process_identity(os.getpid())['start_ticks'],menus={k:str(p) for k,p in menus.items()},modes=['endpoint','fixed_timing'],native_calls=0,source_sha256=bindings,question='Do two uniform terminal wire policies preserve the previous endpoint rule and expose legal CPD/hold-constrained wire alternatives in actual completed own-current menus?',qualification='Retrospective rule development on existing observations; both modes applied to every declared menu, no per-circuit mode tuning or new native samples. No original actor changes.'))
results=[]
for label,actor in menus.items():
 for mode in ['endpoint','fixed_timing']:
  r=select(actor,out/(label+'_'+mode),mode)
  if mode=='endpoint' and label in legacy:
   old=read(legacy[label]);assert r['actual_same_source_candidates']==old['actual_same_source_candidates'] and r['eligible_candidates']==old['eligible_candidates']
   assert (r['selected'] or {}).get('state')==(old['selected'] or {}).get('state')
  results.append(dict(menu=label,actor=str(actor),mode=mode,candidates=r['actual_same_source_candidates'],eligible=r['eligible_candidates'],selected=r['selected'],current_resources=r['current_resources'],fixed_CPD_limit_s=r['fixed_CPD_limit_s']))
  write(out/'results.json',results)
  print(dict(menu=label,mode=mode,candidates=r['actual_same_source_candidates'],eligible=r['eligible_candidates'],selected=None if r['selected'] is None else r['selected']['resources']),flush=True)
assert all(sha(f)==h for f,h in bindings.items())
write(out/'completion.json',dict(passed=True,real_closed_menus=len(menus),mode_evaluations=len(results),legacy_endpoint_menus_reproduced=5,native_calls_new=0,committed_to_original_actors=False,source_sha256=bindings,artifact_sha256={'results.json':sha(out/'results.json')},qualification='Same retrospective endpoints and exact previous selector outcomes in5legacy menus, plus8closed original seed-control menus with both predeclared global modes. Selected states are already executed legal candidates, not new routing experiments or archive observations. Fixed timing allows actual setup tradeoffs within original CPD/resource/hold envelope; endpoint mode remains unchanged. Per-mode selection cost is not full workflow runtime or a prediction of speedup.'))
