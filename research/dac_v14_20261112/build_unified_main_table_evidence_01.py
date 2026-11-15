"""Bind the main table to complete case receipts, including all endpoint changes."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from endpoint_timing_policy_streaming_v2 import compare
p=D/'paper';source=p/'current_repair_unified_structure_01.tex';text=source.read_text()
inventory=read(D/'multiobjective_engineering_inventory_01/complete_configuration_inventory.json')['configurations']
rows=[];output=[];files={}
for line in text.splitlines():
 if '&' not in line or not line.endswith(('\\\\','\\\\\\hline')) or line.startswith('Circuit/role'):
  output.append(line);continue
 cells=line.split('&')
 if len(cells)!=5:output.append(line);continue
 label,cpd,resources,seconds,pss=cells
 if '(initial fail)' in label:
  name='conv_layer_native' if ' N ' in label else 'conv_layer_domain'
  report=D/'complete_serial_additional_circuits_01/comparison.json';v=read(report)['results'][name]
  assert v['quality'] is None and f"{v['actual_failed_seconds']:.2f}"==seconds
  row=dict(label=label,outcome='initial_route_failed',CPD_ns=None,resources=None,complete_seconds=v['actual_failed_seconds'],endpoint_comparison=None,source=str(report))
  files[str(report)]=sha(report);endpoint='--'
 else:
  found=[r for r in inventory if f"{r['complete_seconds']:.2f}"==seconds and f"{r['quality']['CPD_ns']:.6f}"==cpd and '/'.join(str(r['quality'][k]) for k in ['wirelength','SB_pairs','CB_sources'])==resources]
  assert len(found)==1,(label,seconds,len(found))
  r=found[0];proof=read(r['proof']);assert proof['passed'];initial=Path(proof['initial_state']);final=Path(proof['final_state'])
  # Own initial/final FULL/STA vectors, not final-vs-native or historical CPD text.
  before=initial/'endpoint_vector.json';after=final/'endpoint_vector.json';delta=compare(read(before),read(after));assert delta['compatible']
  row=dict(label=label,case=r['case'],quality=r['quality'],complete_seconds=r['complete_seconds'],memory=r['memory'],endpoint_reference='same configuration initial legal route',endpoint_comparison=delta,source=r['proof'])
  for f in [Path(r['proof']),Path(r['measurement']),before,after]:files[str(f)]=sha(f)
  endpoint=f"{delta['setup_improved']}/{delta['setup_regressed']}/{delta['hold_violation_regressions']}"
 rows.append(row)
 line=line.replace('\\\\', '&'+endpoint+'\\\\',1);output.append(line)
assert len(rows)==21,len(rows)
text='\n'.join(output)+'\n';text=text.replace('{lrrrr}\\hline','{lrrrrr}\\hline',1).replace('Time(s) & PSS\\\\','Time(s) & PSS & Setup $+/-$/Hold$^-$\\\\')
text=text.replace('PSS: sampled tree sum in GiB.','PSS: sampled tree sum in GiB. Last column: improved/regressed setup components and increased hold violations against that same configuration\'s initial legal root, not between final arms.')
source.write_text(text)
root=D/'unified_main_table_evidence_01';root.mkdir(exist_ok=False)
write(root/'rows.json',rows)
write(root/'completion.json',dict(passed=True,rows=len(rows),legal_rows=sum(r.get('quality') is not None for r in rows),failed_initial_rows=sum(r['endpoint_comparison'] is None for r in rows),full_endpoint_vectors_recomputed=True,native_calls_new=0,source_sha256=files,artifact_sha256={'rows.json':sha(root/'rows.json')},qualification='Actual same-case initial/final endpoint vectors, CPD, wire/SB/CB, whole command time and memory. Failures have no final vector or legal quality. No new independent input or native execution.'))
print(dict(passed=True,rows=len(rows),changes=[(r['label'],None if r['endpoint_comparison'] is None else {k:r['endpoint_comparison'][k] for k in ['setup_improved','setup_regressed','hold_violation_regressions']}) for r in rows]))
