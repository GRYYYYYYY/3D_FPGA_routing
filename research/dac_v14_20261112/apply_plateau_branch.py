#!/usr/bin/env python3
"""Apply a new policy to existing completed native evidence without rerunning it."""
import argparse
from pathlib import Path
import re
from retained_prefix_workflow import D,read,write,sha
from postroute_plateau_policy import decide

parser=argparse.ArgumentParser();parser.add_argument('--native',type=Path,required=True);parser.add_argument('--branch',type=Path,required=True)
parser.add_argument('--parent',type=Path);args=parser.parse_args()
b=args.native.resolve();out=args.branch.resolve();assert not out.exists()
registration=read(D/'postroute_plateau_policy_experiment_01.json')
assert all(sha(p)==h for p,h in registration['source_sha256'].items())
completion=read(b/'completion.json');assert completion['passed']
audit=read(b/'independent_native_analysis_audit.json');assert audit['passed']
source=Path(completion['input_run']);candidate=Path(completion['candidate_run'])
m=read(candidate/'manifest.json');original=read(source/'manifest.json')
assert m['status']=='completed' and m['metrics']['native_full_check_passed']
for path,digest in m['private_input_sha256'].items():assert sha(path)==digest
for name,record in m['outputs'].items():assert sha(candidate/name)==record['sha256']
if args.parent:
    parent=read(args.parent);assert Path(parent['accepted_run'])==source
    assert sha(source/'routed.route')==parent['accepted_route_sha256']
    seen=parent['seen_route_sha256'];origin=parent['origin_run']
else:
    assert source==Path(registration['start_state']) and candidate==Path(registration['reusable_first_candidate'])
    parent=None;origin=str(source);seen=[sha(source/'routed.route')]
def sta(run):
    text=(run/'stdout.log').read_text();result={}
    for name in ['sWNS','sTNS','hWNS','hTNS']:
        match=re.search(r'\('+name+r'\):\s*([-+0-9.eE]+) ns',text)
        result[name]=float(match[1]) if match else None
    return result
graph=Path(m['command'][m['command'].index('--read_rr_graph')+1])
reference=read(D/'critical_capacity_potential_01/analysis.json')
assert reference['passed']
zero_rc=sha(graph)==reference['source_sha256'].get(str(graph))
# The bound preparation source checks every node R/C and switch R/C fields.
prior=read(D/'critical_capacity_potential_01/execution.json')
assert sha(D/'run_critical_capacity.py')==prior['source_sha256'][str(D/'run_critical_capacity.py')]
assert sha(graph)==prior['source_sha256'][str(graph)]
physical=read(b/'physical_change_audit.json');assert physical==completion['physical_change']
cpd_before=original['metrics']['critical_path_ns'];cpd_after=m['metrics']['critical_path_ns']
assert cpd_before==completion['before_cpd_ns'] and cpd_after==completion['after_cpd_ns']
route_hash=sha(candidate/'routed.route')
decision=decide(True,zero_rc,cpd_before,cpd_after,sta(source),sta(candidate),physical,route_hash,seen)
accepted=candidate if decision['accepted'] else source
out.mkdir(parents=True)
files=[Path(__file__),D/'postroute_plateau_policy.py',D/'postroute_plateau_policy_experiment_01.json',
    b/'completion.json',b/'physical_change_audit.json',b/'input_seal.json',b/'independent_native_analysis_audit.json',
    source/'manifest.json',source/'routed.route',candidate/'manifest.json',candidate/'routed.route',D/'critical_capacity_potential_01/analysis.json',D/'critical_capacity_potential_01/execution.json']
if args.parent:files.append(args.parent.resolve())
result=dict(status='plateau_policy_evaluated',passed=True,decision=decision,origin_run=origin,
    accepted_run=str(accepted),accepted_route_sha256=sha(accepted/'routed.route'),
    seen_route_sha256=seen+([route_hash] if decision['accepted'] else []),
    strict_policy_accepted=completion['accepted'],native_evidence_reused=str(b),new_native_calls=0,
    before_CPD_ns=cpd_before,after_CPD_ns=cpd_after,STA=dict(before=sta(source),after=sta(candidate)),
    physical=physical,source_sha256={str(p):sha(p) for p in files},
    original_rejection_preserved=True,quality_promoted=False)
write(out/'decision.json',result)
print(dict(accepted=decision['accepted'],kind=decision['kind'],CPD=cpd_after,strict_policy_accepted=completion['accepted']),flush=True)
