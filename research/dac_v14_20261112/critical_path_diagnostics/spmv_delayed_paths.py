#!/usr/bin/env python3
"""Inspect a saved spmv regression while retaining unsealed status explicitly."""
from pathlib import Path
import json
from inspect_paths import inspect,D,sha
paths=[D/'layer_bbox_expansion_dev_01/runs'/('spmv_'+a) for a in ['F','A1','F1']]+[D/'delayed_scope_expansion_dev_01/runs'/('spmv_'+a) for a in ['A3','F3','U3']]
rows=[]
for rd in paths:
 m=json.loads((rd/'manifest.json').read_text());audit=json.loads((rd/'independent_audit.json').read_text())
 assert m['status']=='completed' and m['metrics']['native_full_check_passed'] and audit['audit']['passed']
 seal=rd.parent.parent/'input_seal.json'
 row=inspect(rd);row['batch_sealed']=seal.exists() and json.loads(seal.read_text())['passed']
 row['status']='legal_saved_route_diagnostic' if row['batch_sealed'] else 'pending_batch_seal_diagnostic_only'
 rows.append(row)
(D/'critical_path_diagnostics/spmv_delayed_paths.json').write_text(json.dumps(rows,indent=2)+'\n')
for r in rows:print(Path(r['path']).name,r['cpd_ns'],r['status'],r['startpoint'],r['endpoint'])
