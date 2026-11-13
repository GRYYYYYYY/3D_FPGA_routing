import tempfile,json,subprocess,sys
from pathlib import Path
D=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory() as temp:
 p=Path(temp);(p/'registration.json').write_text(json.dumps(dict(circuits=['a','b','c','d'],arms=['F','N'])))
 rows=[dict(circuit='a',arm=arm,status='legal',metrics=dict(critical_path_ns=cpd,iterations=1),path='synthetic',physical_metrics={},h3d=[]) for arm,cpd in [('F',10),('N',11)]]
 (p/'observations.json').write_text(json.dumps(rows))
 subprocess.run([sys.executable,str(D/'analyze_development.py'),str(p)],check=True,stdout=subprocess.DEVNULL)
 a=json.loads((p/'analysis.json').read_text())
 assert a['paired']['F->N']['declared_circuits']==4
 assert a['paired']['F->N']['both_legal']==1
 assert a['status_counts']['F']=={'legal':1,'missing':3}
 assert a['paired']['A0->N']['both_legal']==0
 assert a['paired']['A0->N']['circuit_geomean_improvement_pct'] is None
print('partial population and missing-denominator tests passed')
