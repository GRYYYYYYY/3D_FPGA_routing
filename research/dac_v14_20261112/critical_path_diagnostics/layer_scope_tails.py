#!/usr/bin/env python3
"""Same-layer terminal groups may now have physical cross-layer detours."""
from pathlib import Path
import json
from paired_delay_tails import compare
from inspect_paths import D,sha
B=D/'layer_bbox_dev_01'
pairs=[('scope_R1','eltwise_layer_F','eltwise_layer_F1'),('guide_static','eltwise_layer_A1','eltwise_layer_F1'),('guide_dynamic','eltwise_layer_A1','eltwise_layer_U1')]
result={'scope':'Exploratory saved-route physical connection delay tails after independent audit. Groups use terminal layers, not route planarity: same-layer terminal nets may use inter-layer detours. Not STA critical-path attribution. Batch input seal may still be pending; no formal speedup or blind validation.', 'pairs':{}}
for label,left,right in pairs:
 r=compare(B/'runs'/left,B/'runs'/right)
 if 'entirely_planar_net' in r['groups']:r['groups']['same_layer_terminal_net']=r['groups'].pop('entirely_planar_net')
 result['pairs'][label]=r
result['script_sha256']=sha(Path(__file__))
result['comparison_module_sha256']=sha(Path(__file__).with_name('paired_delay_tails.py'))
(D/'critical_path_diagnostics/layer_scope_tails.json').write_text(json.dumps(result,indent=2)+'\n')
for label,r in result['pairs'].items():
 print(label,'unpaired',r['unpaired_or_identity_mismatch'])
 for group,g in r['groups'].items():print(group,{k:v for k,v in g.items() if k!='worst'})
