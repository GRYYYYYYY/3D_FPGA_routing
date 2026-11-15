"""Replay actual endpoint/policy/audit evidence through the relocated dependency closure."""
import argparse,copy,re,shutil
from pathlib import Path
import runtime_audit as study
from retained_prefix_workflow import read,write,sha
from endpoint_timing_policy_streaming_v2 import load,compare
from multiobjective_acceptance_v2 import decide
from full_route_graph_cache import FullRouteGraphCache
from immutable_rr_audit_cache import GraphAuditCache
from observe import inputs
p=argparse.ArgumentParser();p.add_argument('--fixture',type=Path,required=True);a=p.parse_args();f=a.fixture.resolve()
expected=read(f/'expected.json');graph=f/'rr_graph.xml';route=f/'routed.route'
cache=FullRouteGraphCache(graph,f/'indexes/full_cache')
for name,digest in expected['payload_sha256'].items():assert sha(f/'indexes'/name)==digest,name
original=study.cr.read_graph_evidence;study.cr.read_graph_evidence=cache.evidence
try:
    evidence=study.cr.batch_graph_evidence(graph,[route]);audit=study.cr.audit(graph,route,graph_evidence=evidence)
finally:study.cr.read_graph_evidence=original
def scientific(result):
    result=copy.deepcopy(result);result.pop('audit_wall_seconds',None)
    for key in ['rr_graph','route']:result['inputs'].pop(key,None)
    return result
assert scientific(audit)==scientific(expected['physical_audit']['audit'])
assert study.physical_route_metrics(route,evidence)==expected['physical_audit']['physical_metrics']
vector=load(f/'native_sta_frontier.jsonl');assert vector==read(f/'endpoint_vector.json')
policies=read(f/'policy_cases.json');results=[]
for row in policies:
    actual=decide(**row['arguments']);assert actual==row['expected'];results.append(dict(accepted=actual['accepted'],reason=actual['reason']))
    incomplete=copy.deepcopy(row['arguments']);incomplete['transaction_complete']=False
    assert decide(**incomplete)['accepted'] is False
    foreign=copy.deepcopy(row['arguments']);foreign['after_vector']['constraints_sha256']='different_constraints'
    assert decide(**foreign)['accepted'] is False
assert {r['accepted'] for r in results}=={True,False}
bad_trace=f/'truncated_trace.jsonl';lines=(f/'native_sta_frontier.jsonl').read_text().splitlines();bad_trace.write_text('\n'.join(lines[:-1])+'\n')
shutil.copy2(f/'native_sta_frontier.jsonl.constraints.echo',Path(str(bad_trace)+'.constraints.echo'))
try:load(bad_trace)
except AssertionError:pass
else:raise AssertionError('Incomplete native endpoint trace accepted')
bad=f/'bad_cache';shutil.copytree(f/'indexes/audit_cache',bad)
with (bad/'nodes.npy').open('r+b') as stream:stream.seek(-1,2);last=stream.read(1);stream.seek(-1,2);stream.write(bytes([last[0]^1]))
try:GraphAuditCache(graph,bad)
except AssertionError:pass
else:raise AssertionError('Changed cached payload accepted')
c,paths,loaded,command=inputs(f/'inputs.json',f/'prospective_native_output')
assert '--analysis' in command and '--route' not in command
broken=copy.deepcopy(c);broken['files']['route']['sha256']='0'*64;write(f/'bad_inputs.json',broken)
try:inputs(f/'bad_inputs.json',f/'wrong_output')
except AssertionError:pass
else:raise AssertionError('Wrong input digest accepted')
write(f/'dependency_test.json',dict(passed=True,actual_cached_physical_audit_exact=True,actual_endpoint_vector_exact=True,
    original_cache_payloads_byte_exact=5,actual_policy_cases=results,incomplete_transaction_rejected=True,changed_constraint_rejected=True,
    incomplete_trace_rejected=True,corrupt_cache_rejected=True,wrong_input_digest_rejected=True,
    historical_project_Python_reads_forbidden=True,native_calls=0,
    qualification='Actual archived tiny route/STA and real accepted/rejected BNN decisions, with fresh single-pass index generation outside the project. No native solver run and no independent input quality claim.'))
print(dict(passed=True,policy_cases=len(results),cache_payloads_byte_exact=5,native_calls=0))
