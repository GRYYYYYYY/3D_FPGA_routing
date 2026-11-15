#!/usr/bin/env python3
"""Audit the native domain against original pruned trees and actual candidate edges."""
import argparse,collections
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from resource_opportunity_census import stream_trace
from coordinated_repair_tree import from_trace,prune_sinks
from run_native_scope_policy_v4 import run_dir
p=argparse.ArgumentParser();p.add_argument('--batch',type=Path,required=True);p.add_argument('--role',required=True);a=p.parse_args();b=a.batch.resolve();role=read(b/'registration.json')['roles'][a.role];rd=run_dir(b/a.role);assert read(b/a.role/'completion.json')['passed'];source=Path(role['source']);audit=read(b/(a.role+'_audit/analysis.json'));assert audit['passed'];files=[Path(__file__).resolve(),b/'registration.json',b/a.role/'completion.json',rd/'joint_native.log',b/(a.role+'_audit/analysis.json')]
if not role['crossing_reuse_enabled']:
 assert not (rd/'vertical_domain.log').exists();write(b/(a.role+'_domain_audit.json'),dict(passed=True,enabled=False,source_sha256={str(p):sha(p) for p in files}));raise SystemExit(0)
tracefile=rd/'vertical_domain.log';rows=[l.split() for l in tracefile.read_text().splitlines()];assert rows[-1][0]=='COMPLETE' and rows[-1][-1]=='occupancy_restored';traces={r['net']:r['trace'] for r in stream_trace(source/'routed.route') if str(r['net']) in role['removed_pins']};expected={};original={}
for net,trace in traces.items():
 points={n.inode:n for n in trace};tree=from_trace(trace,collections.defaultdict(float));retained=prune_sinks(tree,role['removed_pins'][str(net)]);expected[net]={up for n,(up,sw,w) in retained['edges'].items() if points[n].low[2]!=points[up].low[2]};original[net]=points
allow=[]
for row in rows[:-1]:
 if row[0]=='ALLOW':
  net,pin,count=map(int,row[1:4]);nodes=set(map(int,row[4:]));assert len(nodes)==count and nodes==expected[net];allow.append([net,pin])
 else:assert row[0]=='CHECK' and row[-1]=='1','Nonconfigurable closure violated requested domain'
assert allow==[[q['net'],q['pin']] for q in role['queries'][:len(allow)]]
actual={}
if audit.get('candidate_route'):
 for r in stream_trace(audit['candidate_route']):
  if r['net'] not in expected:continue
  sources={x.inode for x,y in zip(r['trace'],r['trace'][1:]) if x.switch!=-1 and x.low[2]!=y.low[2]};assert sources<=expected[r['net']];actual[str(r['net'])]=sorted(sources)
files += [tracefile,source/'routed.route',Path(role['crossing_domain'])]
write(b/(a.role+'_domain_audit.json'),dict(passed=True,enabled=True,initial_retained_sources={str(k):sorted(v) for k,v in expected.items()},actual_candidate_sources=actual,all_queries_same_retained_source_domain=True,transaction_completed=bool(int(rows[-1][1])),source_sha256={str(p):sha(p) for p in files},qualification='The selected native search may reuse only crossing sources already present after pruning. Retained edges are separately checked by the physical transaction audit; final FULLSTA remains mandatory.'))
