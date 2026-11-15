"""Register fixed development integration on a different circuit and a distinct placement+SDC."""
import ast,copy,re
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
r=D/'unified_input_integration_01';r.mkdir(exist_ok=False);(r/'configs').mkdir()
base=D.parents[1];template_path=Path(read(D/'complete_BNN_terminal_wire_flow_01/plan.json')['config']);template=read(template_path)
assert read(D/'current_owner_transaction_validation_01/completion.json')['passed']
noop=read(D/'unified_resource_noop_preflight_01/completion.json');assert noop['passed'] and noop['attempted_scopes']==noop['owner_commits']==0
# Declared synthetic benchmark requirement, chosen before this new paired execution.
sdc=r/'robot_50MHz.sdc';sdc.write_text('# Integration timing instance: 50 MHz, 1 ns maximum external I/O delay.\n# This is a declared benchmark target, not an externally supplied application requirement.\ncreate_clock -period 20 clk\nset_input_delay -clock clk -max 1 [get_ports {*} ]\nset_input_delay -clock clk -min 0 [get_ports {*} ]\nset_output_delay -clock clk -max 1 [get_ports {*} ]\nset_output_delay -clock clk -min 0 [get_ports {*} ]\n')
clocks=set()
for line in (base/'benchmarks/downloads/beyond_flatland/robot_rl.blif').open():
 if line.startswith('.latch '):clocks.add(line.split()[4])
assert clocks=={'clk'},clocks
entries={'attention':base/'results/architecture_flow_20261027/runs/training_attention_layer_s11_hybrid_o_n60_w100_p0_a0','robot_s23_SDC':base/'results/architecture_flow_20261027/runs/heldout_robot_rl_s23_hybrid_o_n60_w100_p0_a0'}
def inputs(command):return [command[1],command[2],*[command[command.index(k)+1] for k in ['--read_rr_graph','--net_file','--place_file']]]
oldinputs=set(inputs(template['route_command']));common={f:h for f,h in template['input_sha256'].items() if f not in oldinputs}
# Also bind statically reachable local helpers and subprocess script literals.
seeds=['run_complete_unified_method_v1.py','run_complete_unified_resource_flow_v1.py','run_unified_resource_repair_v1.py','current_owner_transaction_v1.py','verify_complete_unified_method_v1.py','queue_unified_input_integration_01.py']
seen=set();pending=[D/f for f in seeds]
while pending:
 f=pending.pop()
 if f in seen:continue
 seen.add(f);text=f.read_text();tree=ast.parse(text)
 names={x.module+'.py' for x in ast.walk(tree) if isinstance(x,ast.ImportFrom) and x.module}
 names.update(name+'.py' for x in ast.walk(tree) if isinstance(x,ast.Import) for name in [a.name for a in x.names])
 names.update(re.findall(r"['\"]([A-Za-z_][A-Za-z_0-9]*\.py)['\"]",text))
 pending += [D/n for n in names if (D/n).is_file() and D/n not in seen]
for f in seen:common[str(f)]=sha(f)
for f in [Path(__file__).resolve(),D/'crossing_source_stage_01/bin/vpr',D/'crossing_source_stage_01/binding.json',D/'current_owner_transaction_validation_01/completion.json',D/'unified_resource_noop_preflight_01/completion.json']:
 common[str(f)]=sha(f)
assert all(sha(f)==h for f,h in common.items())
cache={};cases={};provenance={}
def digest(f):
 f=str(Path(f).resolve())
 if f not in cache:cache[f]=sha(f)
 return cache[f]
for label,source in entries.items():
 m=read(source/'manifest.json');old=m['command'];cmd=list(template['route_command']);cmd[1:3]=old[1:3]
 for option in ['--read_rr_graph','--net_file','--place_file','--device','--route_chan_width']:cmd[cmd.index(option)+1]=old[old.index(option)+1]
 for option,name in [('--net_file','packed.net'),('--place_file','placed.place')]:assert digest(cmd[cmd.index(option)+1])==m['outputs'][name]['sha256']
 assert cmd[cmd.index('--router_max_convergence_count')+1]=='8' and cmd[cmd.index('--seed')+1]=='11'
 has_sdc=label=='robot_s23_SDC'
 if has_sdc:cmd += ['--sdc_file',str(sdc)]
 for arm in ['native','domain']:
  c=copy.deepcopy(template);c.update(circuit=Path(cmd[2]).stem,route_command=cmd,domain_mode='unrestricted' if arm=='native' else 'paired',domain_feedback=arm=='domain',owner_escalation=True,owner_domain_mode='unrestricted_in_both_arms',owner_rank_windows=3,unified_controller_version='development_v1',final_state_policy='strict_timing_terminal_after_endpoint_wire_handoff',development_only=True,input_sha256=dict(common),source_manifest=str(source/'manifest.json'),explicit_sdc_spec=None if not has_sdc else dict(clock='clk',period_ns=20,max_IO_delay_ns=1,min_IO_delay_ns=0,origin='declared benchmark integration target, not external application requirement'))
  c['input_sha256'].update({f:digest(f) for f in inputs(cmd)})
  c['input_sha256'][str(source/'manifest.json')]=digest(source/'manifest.json')
  if has_sdc:c['input_sha256'][str(sdc)]=digest(sdc)
  c['phase_binary_sha256']['owner_coordination']=digest(D/'crossing_source_stage_01/bin/vpr')
  c['backend']='unified_resource_owner_terminal_wire_current_STA_development_v1'
  c['comparison']=c['qualification']='Fixed prospective development integration, not frozen confirmation. New fresh count8/1.01 route, K8/rank3/current STA resource search, per-net failure release in domain arm, matched unrestricted owner escalation on closure, endpoint-safe same-flow terminal wire handoff, then strict current-STA timing. Both arms use same binaries, inputs, engineering and opportunities. No external route/query/candidate results imported. Actual initial failure, no-cut, no-gain and worse retained. No total experiment date/call/step stop. Shared-host complete measurements descriptive. Root identity must be checked from actual outputs; directory seed labels are not independence evidence.'
  name=label+'_'+arm;out=r/'configs'/(name+'.json');write(out,c);cases[name]=str(out)
 provenance[label]=dict(source_manifest=str(source/'manifest.json'),source_manifest_sha256=digest(source/'manifest.json'),input_sha256={f:digest(f) for f in inputs(cmd)},explicit_SDC=has_sdc)
files=[Path(__file__).resolve(),D/'queue_unified_input_integration_01.py',D/'verify_complete_unified_method_v1.py',D/'confirmation_input_inventory_01/completion.json',D/'current_owner_transaction_validation_01/completion.json',D/'unified_resource_noop_preflight_01/completion.json',sdc,*map(Path,cases.values())]
write(r/'plan.json',dict(passed=True,fixed_order=list(cases),cases=cases,predecessor=str(D/'unexecuted_recovery_20261115_01/queue'),source_sha256={str(f):sha(f) for f in files},input_provenance=provenance,local_python_dependencies=len(seen),frozen_confirmation=False,registered_before_new_policy_outcomes=True,qualification='Four fixed development roles. Attention is a different circuit from existing modern full-repair cases. Robot s23/p0 has same packing but different actual coordinates versus prior s21/p0; the added SDC makes this a different constrained physical input, not a placement-only causal comparison. All controls paired within each input; no unseen-test or independent-root claim until actual route identity and complete outcomes. Old registered live work and recovery chain retain priority.'))
print(dict(passed=True,roles=list(cases),local_helpers=len(seen),explicit_SDC_pair='robot_s23_SDC',native_calls_new=0))
