"""Compare complete independent native transactions, omitting elapsed time only."""
import hashlib,json
from pathlib import Path

def transaction(path):
    """Preserve failures, physical trees, objective, capacity and heap statistics."""
    rows=[];timings=[]
    for line in Path(path).read_text().splitlines():
        values=line.split();assert values
        if values[0]=='QUERY':
            assert len(values)==8;timings.append(dict(net=int(values[1]),pin=int(values[2]),seconds=float(values[-1])));values=values[:-1]
        elif values[0]=='COMPLETE':
            assert len(values)==6;whole=float(values[4]);values=values[:4]+values[5:]
        rows.append(values)
    assert rows[0][0]=='MODE' and rows[-1][0]=='COMPLETE' and rows[-1][-1]=='occupancy_restored'
    return dict(success=bool(int(rows[-1][1])),finished=int(rows[-1][2]),planned=int(rows[-1][3]),normalized_sha256=hashlib.sha256(json.dumps(rows,separators=(',',':')).encode()).hexdigest(),core_seconds=whole,queries=timings)
