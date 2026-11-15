"""Audit explicit target-CB restriction with a real retained crossing subtree."""
import argparse, collections
from pathlib import Path
from retained_prefix_workflow import read,write,sha
from run_native_scope_policy_v4 import run_dir
from resource_opportunity_census import stream_trace
from coordinated_repair_tree import from_trace,prune_sinks

p=argparse.ArgumentParser();p.add_argument('--batch',type=Path,required=True);p.add_argument('--role',required=True);a=p.parse_args()
b=a.batch.resolve();role=read(b/'registration.json')['roles'][a.role];target=role['domain_target_net']
worker=b/a.role;rd=run_dir(worker);assert read(worker/'completion.json')['passed']
assert role['crossing_reuse_enabled'] and not role['domain_failure_release']
source=Path(role['source']);audit=read(b/(a.role+'_audit/analysis.json'));assert audit['passed']
tokens=list(map(int,Path(role['explicit_crossings']).read_text().split()));assert tokens[:3]==[1,target,len(tokens)-3]
allowed=set(tokens[3:]);assert len(allowed)==1 and role['allowed_resource_kind']=='CB'
original=next(r for r in stream_trace(source/'routed.route') if r['net']==target)
meta={node.inode:node for node in original['trace']}
tree=from_trace(original['trace'],collections.defaultdict(float))
removed=role['removed_pins'][str(target)];assert removed and set(removed)<set(tree['sinks'])
kept=prune_sinks(tree,removed)
def sources(tree):
 cb,sb=set(),set()
 for v,(u,_,_) in tree['edges'].items():
  if meta[u].low[2]!=meta[v].low[2]:
   if meta[u].kind=='OPIN':cb.add(u)
   else:sb.add(tuple(sorted([u,v])))
 return cb,sb
original_cb,original_sb=sources(tree);retained_cb,retained_sb=sources(kept)
assert original_cb==retained_cb==allowed and not retained_sb and original_sb
manifest=read(rd/'manifest.json')
assert manifest['environment']['VPR_JOINT_NATIVE_EXPLICIT_CROSSINGS']==role['explicit_crossings']
assert manifest['environment']['VPR_JOINT_NATIVE_DOMAIN_FAILURE_RELEASE']=='0'
rows=[line.split() for line in (rd/'vertical_domain.log').read_text().splitlines()]
assert rows[-1][0]=='COMPLETE' and rows[-1][-1]=='occupancy_restored'
observed=[]
for row in rows[:-1]:
 if row[0]=='ALLOW':
  net,pin,count=map(int,row[1:4]);assert net==target and count==len(allowed) and set(map(int,row[4:]))==allowed
  observed.append((net,pin))
 else:assert row[0]=='CHECK' and row[-1]=='1'
expected=[(q['net'],q['pin']) for q in role['queries'] if q['net']==target]
assert observed==expected[:len(observed)]
files=[Path(__file__).resolve(),b/'registration.json',worker/'completion.json',rd/'manifest.json',rd/'vertical_domain.log',
       b/(a.role+'_audit/analysis.json'),source/'routed.route',Path(role['explicit_crossings'])]
actual=[]
if audit.get('candidate_route'):
 rec=next(r for r in stream_trace(audit['candidate_route']) if r['net']==target)
 actual=[(x.inode,y.inode) for x,y in zip(rec['trace'],rec['trace'][1:]) if x.switch!=-1 and x.low[2]!=y.low[2]]
 assert {x for x,y in actual}==allowed
 files.append(Path(audit['candidate_route']))
write(b/(a.role+'_domain_audit.json'),dict(passed=True,enabled=True,explicit_crossing_source_domain=True,
 domain_target_net=target,allowed_sources=sorted(allowed),actual_candidate_crossings=actual,
 retained_crossing_resources_present_after_prune=True,domain_equals_actual_retained_crossing_sources=True,
 retained_CB_sources=sorted(retained_cb),retained_SB_pairs=sorted(retained_sb),
 transaction_completed=bool(int(rows[-1][1])),source_sha256={str(f):sha(f) for f in files},
 qualification='Partial target sink prune retains the actual CB branch to all other sinks and removes the return SB. Explicit source whitelist is exactly that retained CB, and applies only to target queries; owner search unrestricted, failure release disabled. Existing independent native reconstruction checks all untouched branch edges and fixed terminals; source/candidate/restored FULL/STA/capacity remain required. This differs from the earlier full-target prune with no retained crossings.'))
