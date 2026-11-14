"""Build uniform resource-release bundles, excluding overlapping net scopes.

Each selected net contributes only one ranked cut. The native transaction removes
all cuts, updates real occupancy on each restoration, and only a complete final
candidate can be accepted. Rank screening never claims timing feasibility.
"""
import hashlib,json
from pathlib import Path
from retained_prefix_workflow import read,write,sha

def make(selection,output,size):
 selection=Path(selection).resolve();out=Path(output).resolve();assert isinstance(size,int) and size>0;out.mkdir(exist_ok=False);c=read(selection/'completion.json');assert c['passed'];assert all(sha(p)==h for p,h in c['source_sha256'].items());candidates=read(selection/'candidates.json');picked=[];nets=set()
 for row in candidates:
  if row['net'] in nets:continue
  assert row['pins'] and row['retained_crossing_sources'] and row['removed_crossing_resources']>0;nets.add(row['net']);picked.append(row)
  if len(picked)==size:break
 requests=sorted([q for r in picked for q in r['ordered_queries']],key=lambda q:(-q['raw_criticality'],q['net'],q['pin']));assert len({(q['net'],q['pin']) for q in requests})==len(requests)
 request=out/'request.txt';request.write_text(str(len(picked))+'\n'+''.join(' '.join(map(str,[r['net'],len(r['pins']),*r['pins']]))+'\n' for r in picked)+'0\n'+str(len(requests))+'\n'+''.join(f"{q['net']} {q['pin']} {q['raw_criticality']:.17g}\n" for q in requests));domain=out/'domain.txt';domain.write_text(str(len(picked))+'\n'+''.join(str(r['net'])+'\n' for r in picked));plan=dict(passed=bool(picked),source_state=c['source_state'],requested_bundle_size=size,actual_bundle_size=len(picked),ranked_selection='First rank-ordered distinct-net cuts from the current source only; no per-circuit historical best.',queries=requests,removed_pins={str(r['net']):r['pins'] for r in picked},fixed_target_paths=False,objective='weighted_soft',request=str(request),request_sha256=sha(request),crossing_domain=str(domain),domain_sha256=sha(domain),selected_scopes=picked,independent_removed_crossings=sum(r['removed_crossing_resources'] for r in picked),source_sha256={str(p):sha(p) for p in [Path(__file__).resolve(),selection/'completion.json',selection/'candidates.json']},qualification='Private multi-net transaction request; native occupancy updated at every restoration. Counts describe removal before reconnection, not final savings. Whole native/physical/FULLSTA and fixed root budgets decide one final commit; after an accepted bundle, rerank using its new STA. A failing bundle is rolled back as a whole.');write(out/'plan.json',plan);return plan
