import tempfile,csv
from pathlib import Path
from audit_final_guides import audit
with tempfile.TemporaryDirectory() as temp:
 d=Path(temp)
 (d/'routed.route').write_text('''Net 0 (a)
Node: 0 SOURCE (0, 0, 0) Switch: 0
Node: 1 OPIN (0, 0, 0) Switch: 0
Node: 2 CHANX (0, 0, 1) Switch: 0
Node: 3 IPIN (1, 0, 1) Switch: 0
Node: 4 SINK (1, 0, 1) Switch: -1 Net_pin_index: 1
Node: 1 OPIN (0, 0, 0) Switch: 0
Node: 5 CHANX (0, 0, 1) Switch: 0
Node: 6 IPIN (2, 0, 1) Switch: 0
Node: 7 SINK (2, 0, 1) Switch: -1 Net_pin_index: 2
''')
 (d/'h3d_final_guides.csv').write_text('net,pin,source,sink,planned_criticality,preferred,actual_crossings,routed,adopted,timing_penalty_seconds\n0,1,0,4,0.9,1;,1;,1,1,0\n0,2,0,7,0.8,99;,1;,1,0,0\n')
 (d/'stdout.log').write_text('H3D_FINAL success=1 guided=2 routed=2 adopted=1\n')
 assert audit(d)['passed']
 p=d/'h3d_final_guides.csv';p.write_text(p.read_text().replace('0,1,0,4','0,1,0,7'))
 try:audit(d)
 except AssertionError:pass
 else:raise AssertionError('auditor accepted wrong terminal')
print('final trace branched-path reconstruction and wrong-terminal rejection passed')
