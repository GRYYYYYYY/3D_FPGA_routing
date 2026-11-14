"""Selection changes with current STA; numeric tie windows are not accept tolerances."""
import json
import tempfile
from pathlib import Path
from current_sta_selector import select

def row(net,slack,criticality=.9):
    return dict(type='pin',net=net,pin=1,driver=0,ignored=0,global_=0,route_tree_present=True,
                setup_slack_s=slack,tree_rr=net+100,setup_criticality_raw=criticality,native_net_delay_s=1e-9,**{'global':0})
with tempfile.TemporaryDirectory() as td:
    p=Path(td)/'trace.jsonl'
    def run(rows,near=0):
        p.write_text('\n'.join(json.dumps(r) for r in rows));return select(p,near)
    a=run([row(1,-6e-9,.9999),row(2,-5.9e-9,1)])
    assert [r['net'] for r in a['targets']]==[1]
    b=run([row(1,-5.7e-9),row(2,-5.9e-9)])
    assert [r['net'] for r in b['targets']]==[2]
    assert len(run([row(1,-6e-9),row(2,-5.9e-9)],.2)['targets'])==2
    bad=row(3,-7e-9);bad['ignored']=1
    assert [r['net'] for r in run([bad,row(1,-6e-9)])['targets']]==[1]
print('PASS: fresh-state migration, raw-criticality rank mismatch, optional near window, ignored pins')
