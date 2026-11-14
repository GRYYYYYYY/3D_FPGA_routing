#!/usr/bin/env python3
"""Validate archive semantics, separate timing scopes, and export joint plots."""
import collections,json,math,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha

start=time.monotonic();b=D/'multiobjective_archive_01';proof=read(b/'completion.json')
assert proof['passed'] and all(sha(b/n)==h for n,h in proof['artifact_sha256'].items())
rows=read(b/'points.json');lookup={p['id']:p for p in rows};assert len(lookup)==len(rows)
receipts=[];files=[Path(__file__).resolve(),b/'completion.json',b/'points.json']
for p in rows:
 assert p['status']=='legal'
 if p['opportunity']!='initial_route':assert p['complete_single_configuration_seconds'] is None and p['timing_cohort'] is None
 for name in p['quality_dominated_by']:
  a=lookup[name];assert a['quality_cohort']==p['quality_cohort']
  assert all(a[k]<=p[k] for k in ['wirelength','SB_pairs','CB_sources'])
  assert a['CPD_interval_ns'][1]<=p['CPD_interval_ns'][0] or (a['route_body_sha256']==p['route_body_sha256'] and a['binary_sha256']==p['binary_sha256'])
 for name in p['matched_time_dominated_by']:
  a=lookup[name];assert a['timing_cohort']==p['timing_cohort']=='formal_timing_01' and a['convergence']==p['convergence']
  assert a['complete_single_configuration_seconds']<=p['complete_single_configuration_seconds']
 if not p['state']:continue
 state=Path(p['state']);attempt=state.parent;log=attempt/'candidate/runs/state/joint_native.log'
 if log.exists():
  terminal=[line.split() for line in log.read_text().splitlines() if line.startswith('COMPLETE ')]
  assert len(terminal)==1 and len(terminal[0])==6
  complete=read(attempt/'candidate/completion.json');files.extend([log,attempt/'candidate/completion.json'])
  receipts.append(dict(point=p['id'],repair_core_seconds=float(terminal[0][4]),transaction_terminal=terminal[0],
   native_repair_observation_wrapper_timing=complete['timing'],candidate_FULL_STA_wrapper_timing=p['observation_workflow'],
   shared_research_workflow=p['shared_research_workflow'],complete_standalone_configuration_seconds=None,
   qualification='Nested measured scopes. Core lies within repair observation wrapper; candidate FULL/STA is separate. Shared multi-policy workflow is not a standalone configuration runtime.'))
write(b/'timing_scope_receipts.json',receipts)
# Formal summaries use all registered repeats, only when all QoR dimensions and
# input/config identities agree. The resulting statistics are not archive points.
groups=collections.defaultdict(list)
for p in rows:
 if p['timing_cohort']=='formal_timing_01':groups[(p['circuit'],p['arm'])].append(p)
statistics=[]
for (circuit,arm),ps in sorted(groups.items()):
 assert len(ps)==3
 for k in ['quality_cohort','binary_sha256','convergence','CPD_ns','wirelength','SB_pairs','CB_sources']:assert len({p[k] for p in ps})==1,(circuit,arm,k)
 times=sorted(p['complete_single_configuration_seconds'] for p in ps)
 statistics.append(dict(circuit=circuit,arm=arm,complete_process_seconds=times,median_seconds=times[1],
  CPD_ns=ps[0]['CPD_ns'],wirelength=ps[0]['wirelength'],SB_pairs=ps[0]['SB_pairs'],CB_sources=ps[0]['CB_sources'],
  actual_runs=[p['id'] for p in ps],qualification='Three-repeat summary of same frozen configuration and identical reported QoR; no cross-configuration synthetic point.'))
write(b/'formal_repeat_statistics.json',statistics)
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig,axes=plt.subplots(1,3,figsize=(12.5,3.7))
styles={'A0':('black','s'),'R1':('#2374ab','^'),'U':('#e18727','D'),'Tf':('#7a43a8','v'),'repair_or_observed_state':('#25944b','o')}
for ax,circuit in zip(axes,['eltwise_layer','spmv','bnn']):
 for arm,(color,marker) in styles.items():
  ps=[p for p in rows if p['circuit']==circuit and p['arm']==arm]
  ax.scatter([p['CPD_ns'] for p in ps],[p['wirelength'] for p in ps],c=color,marker=marker,s=30,alpha=.65,label=arm.replace('repair_or_observed_state','repair/STA state'))
 ax.set_title(circuit);ax.set_xlabel('CPD (ns)');ax.set_ylabel('Planar routed wirelength');ax.grid(alpha=.2)
axes[0].legend(fontsize=7);fig.suptitle('Observed quality states: strong baselines included; opportunities differ',fontsize=11)
fig.tight_layout();fig.savefig(b/'quality_projection.svg');fig.savefig(b/'quality_projection.pdf');plt.close(fig)
write(b/'validation.json',dict(passed=True,points=len(rows),joint_quality_frontier=True,strong_baselines_included=True,
 timing_scopes_separated=True,formal_repeat_groups=len(statistics),repair_core_receipts=len(receipts),
 graph_and_input_revalidation='Actual bound graph, binary, netlist, packing, placement and route hashes checked during extraction; not rerun here.',
 CPD_precision='Rounded-report overlap remains unknown; no fake tolerance for native acceptance.',
 source_sha256={str(p):sha(p) for p in files},artifact_sha256={n:sha(b/n) for n in ['timing_scope_receipts.json','formal_repeat_statistics.json','quality_projection.svg','quality_projection.pdf']},complete_process_seconds=time.monotonic()-start,
 qualification='Figures project four-dimensional quality data onto CPD/wire only; no two-dimensional dominance or fair runtime advantage implied. Development archive includes unequal repair/convergence opportunities.'))
print(dict(passed=True,points=len(rows),timing_receipts=len(receipts),formal_groups=len(statistics)),flush=True)
