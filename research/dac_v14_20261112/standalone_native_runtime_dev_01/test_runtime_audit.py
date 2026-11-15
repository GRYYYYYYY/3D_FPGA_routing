"""Read-only relocation check against an actual archived native route."""
import argparse,json,re,sys
from pathlib import Path

p=argparse.ArgumentParser();p.add_argument('--fixture',type=Path,required=True);p.add_argument('--forbid-prefix',required=True)
a=p.parse_args();forbidden=Path(a.forbid_prefix).resolve()
def reject_historical_reads(event,args):
    if event=='open' and isinstance(args[0],(str,bytes)):
        path=Path(args[0].decode() if isinstance(args[0],bytes) else args[0]).resolve()
        if path.is_relative_to(forbidden):raise RuntimeError('Historical project access forbidden: '+str(path))
sys.addaudithook(reject_historical_reads)
import runtime_audit as audit
from runtime_common import write_json
root=a.fixture.resolve();audit.BASE=root
rd=root/'runs/state';manifest=json.loads((rd/'manifest.json').read_text())
summary=audit.audit_batch({'fixture':{'original_graph':str(root/'rr_graph.xml')}},[manifest],root/'audit.json')
actual=json.loads((rd/'independent_audit.json').read_text())
expected=json.loads((root/'expected.json').read_text())
def scientific(result):
    result=dict(result);result.pop('audit_wall_seconds',None)
    result['inputs']=dict(result['inputs'])
    for key in ['rr_graph','route']:result['inputs'].pop(key,None)
    return result
assert scientific(actual['audit'])==scientific(expected['audit'])
assert actual['physical_metrics']==expected['physical_metrics']
assert summary['legal_count']==1 and summary['failed_count']==0
# Deliberately corrupt an actual switch. Independent audit must reject it.
route=(rd/'routed.route').read_text()
corrupt,n=re.subn(r'Switch:\s*[0-9]+','Switch: 999999999',route,count=1);assert n==1
bad=root/'invalid_switch.route';bad.write_text(corrupt)
evidence=audit.cr.batch_graph_evidence(root/'rr_graph.xml',[bad])
invalid=audit.cr.audit(root/'rr_graph.xml',bad,graph_evidence=evidence)
assert not invalid['passed'] and any('missing directed edge/switch' in x for x in invalid['errors'])
write_json(root/'invalid_audit.json',invalid)
# Failed native observations stay in the denominator and cannot become legal points.
failed=audit.audit_batch({'fixture':{'original_graph':str(root/'rr_graph.xml')}},
    [{'name':'failed_probe','status':'timeout','metrics':{}}],root/'failed_batch.json')
assert failed['registered_route_count']==1 and failed['legal_count']==0 and failed['failed_count']==1
write_json(root/'test.json',dict(passed=True,actual_route_audit_exact=True,physical_metrics=actual['physical_metrics'],
    invalid_switch_rejected=True,failed_observation_retained=True,historical_project_reads_forbidden=True,
    VPR_calls_new=0,qualification='Actual archived tiny route replay through relocated physical audit; no native route rerun or independent scientific sample.'))
print(json.dumps(json.loads((root/'test.json').read_text())))
