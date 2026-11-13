#!/usr/bin/env python3
"""Reuse failed-artifact counts only for an identical route body and physical input graph."""
from pathlib import Path
import hashlib,json
D=Path(__file__).resolve().parent;B=D/'failed_attention_diagnostic_01';assert json.loads((B/'input_seal.json').read_text())['passed'];reg=json.loads((B/'registration.json').read_text());original=Path(reg['source']);report=json.loads((B/'analysis.json').read_text());base=json.loads((original/'manifest.json').read_text())
def body(p):
 t=p.read_text();assert 'Net ' in t;return hashlib.sha256(t[t.index('Net '):].encode()).hexdigest()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
graph=base['command'][base['command'].index('--read_rr_graph')+1];entries={}
for rd in [original,D/'target_feedback_scale_dev_01/runs/attention_layer_V',D/'target_feedback_scale_dev_01/runs/attention_layer_Tf']:
 mp=rd/'manifest.json'
 if not mp.exists():continue
 m=json.loads(mp.read_text())
 if m['status']!='failed':continue
 assert m['command'][m['command'].index('--read_rr_graph')+1]==graph
 assert m['shared_inputs'][graph]['sha256']==base['shared_inputs'][graph]['sha256']
 assert body(rd/'routed.route')==body(original/'routed.route')
 assert sha(rd/'routed.route')==m['outputs']['routed.route']['sha256']
 entries[str(rd)]=dict(qualification='Saved failed route artifact counts; native failure retained, no legal CPD. Exact body/physical graph reuse, not another independent observation.',source=str(B/'analysis.json'),source_sha256=sha(B/'analysis.json'),manifest_sha256=sha(mp),route_sha256=sha(rd/'routed.route'),route_body_sha256=body(rd/'routed.route'),physical_metrics=report['physical_metrics_of_saved_failed_artifact'],overused_rr_nodes=report['saved_route_summary']['overused_rr_nodes'])
(D/'failed_occupancy_index.json').write_text(json.dumps(dict(entries=entries,scope='Explicit failed-route artifact metrics separate from legal-route physical results'),indent=2)+'\n');print('indexed',len(entries))
