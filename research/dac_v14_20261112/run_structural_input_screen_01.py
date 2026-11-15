"""Inspect the five already inventoried candidates and retain the failed reference."""
import subprocess,sys,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
b=D/'structural_input_screen_01';b.mkdir(exist_ok=False)
inventory=D/'confirmation_input_inventory_01/inputs.json';rows=read(inventory)
files=[inventory,D/'screen_structural_mechanisms_v1.py',Path(__file__).resolve()]
write(b/'registration.json',dict(source_sha256={str(f):sha(f) for f in files},input_order=[r['name'] for r in rows],native_calls_planned=0,qualification='Existing independently identified physical roots; no new route quality or confirmation claim. All inventoried rows retained, including initial failure.'))
results=[]
for row in rows:
    cache=D/('full_route_graph_cache_bnn_01' if 'n125_' in row['name'] else 'complete_serial_additional_circuits_01/robot_rl_native/flow/full_graph_cache')
    output=b/row['name'];cmd=[sys.executable,str(D/'screen_structural_mechanisms_v1.py'),'--run',str(Path(row['source_manifest']).parent),'--full-graph-cache',str(cache),'--output',str(output)]
    with (b/(row['name']+'.log')).open('x') as log:
        r=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,timeout=1800)
    assert r.returncode==0,(row['name'],r.returncode)
    result=read(output/'completion.json');assert result['passed']
    results.append(dict(name=row['name'],circuit=row['circuit'],packing_sha256=row['packing_sha256'],placement_coordinates_sha256=row['placement_coordinates_sha256'],netlist_sha256=row['netlist_sha256'],completion=str(output/'completion.json'),**{k:result[k] for k in ['status','counts','mechanism_decision','physical_metrics','route_body_sha256'] if k in result}))
    write(b/'rows.json',results);print(results[-1],flush=True)
write(b/'completion.json',dict(passed=True,input_records=len(results),legal_root_screens=sum(r['status']=='legal_historical_root_structural_screen' for r in results),failed_initial_roots=sum(r['status']=='initial_route_failed_no_legal_repair_root' for r in results),native_calls_new=0,new_full_method_outcomes=0,source_sha256={str(f):sha(f) for f in [b/'registration.json',inventory,*[Path(r['completion']) for r in results]]},artifact_sha256={'rows.json':sha(b/'rows.json')},qualification='Read-only input/mechanism applicability screen. Historical names do not imply unseen holdout status. Structural opportunities require fresh native STA and actual matched native/domain executions; zero supported cuts do not prove no other routing opportunity.'))
