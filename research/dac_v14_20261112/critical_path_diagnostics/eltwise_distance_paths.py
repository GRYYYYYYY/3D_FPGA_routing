#!/usr/bin/env python3
"""Inspect a sealed eltwise distance/DP regressions while retaining unsealed status explicitly."""
from pathlib import Path
import json
from inspect_paths import inspect,D,sha
paths=[D/'source_floor_dev_01/runs/eltwise_layer_P',D/'complete_distance_dev_02/runs/eltwise_layer_Ed',D/'distance_dp_dev_01/runs/eltwise_layer_Pn',D/'distance_dp_dev_01/runs/eltwise_layer_En']
rows=[]
for rd in paths:
 m=json.loads((rd/'manifest.json').read_text());audit=json.loads((rd/'independent_audit.json').read_text())
 assert m['status']=='completed' and m['metrics']['native_full_check_passed'] and audit['audit']['passed']
 seal=rd.parent.parent/'input_seal.json'
 row=inspect(rd);row['batch_sealed']=seal.exists() and json.loads(seal.read_text())['passed']
 row['status']='legal_saved_route_diagnostic' if row['batch_sealed'] else 'pending_batch_seal_diagnostic_only'
 rows.append(row)
(D/'critical_path_diagnostics/eltwise_distance_paths.json').write_text(json.dumps(rows,indent=2)+'\n')
for r in rows:print(Path(r['path']).name,r['cpd_ns'],r['status'],r['startpoint'],r['endpoint'])
