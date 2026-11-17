"""Interpret a completed single-flag intervention; never upgrade failed quality."""
from pathlib import Path
import json,hashlib,datetime
D=Path(__file__).resolve().parent;B=D/'LSTM_release_ablation_01'
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for x in iter(lambda:f.read(8*1024*1024),b''):h.update(x)
 return h.hexdigest()
def write(p,v):Path(p).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
assert read(B/'queue/completion.json')['passed'];v=read(B/'verification.json');assert v['passed']
p=read(B/'plan.json');O=Path(p['reference_transaction']);N=B/'transaction';row=p['reference_accepted_step']
a=read(O/'reuse_on/runs/state/manifest.json');b=read(N/'reuse_on/runs/state/manifest.json')
assert a['status']==b['status']=='completed' and a['metrics']['native_full_check_passed'] and b['metrics']['native_full_check_passed']
# Normalize only artifact destinations; immutable input paths and all options remain.
def command(m):
 c=list(m['command'])
 for opt in ['--net_file','--place_file','--route_file']:
  pos=c.index(opt)+1;assert sha(c[pos])==m['outputs'][Path(c[pos]).name]['sha256'];c[pos]='{'+opt+'}'
 return c
assert command(a)==command(b),'Actual native options differ'
def environment(m):
 e=dict(m['environment'])
 for key in ['VPR_JOINT_NATIVE_REUSE_CROSSINGS','VPR_JOINT_NATIVE_REQUEST']:e[key]=sha(e[key])
 for key in ['VPR_JOINT_NATIVE_VERTICAL_DOMAIN_TRACE','VPR_H3D_FINAL_STA_TRACE','VPR_JOINT_NATIVE_OUTPUT']:e[key]='{output}'
 return e
x,y=environment(a),environment(b);assert x.pop('VPR_JOINT_NATIVE_DOMAIN_FAILURE_RELEASE')=='1';assert y.pop('VPR_JOINT_NATIVE_DOMAIN_FAILURE_RELEASE',None) in [None,'0'];assert x==y,(x,y)
old=(O/'reuse_on/runs/state/joint_native.log').read_text().splitlines();new=(N/'reuse_on/runs/state/joint_native.log').read_text().splitlines()
def norm(line):
 tokens=line.split();return ' '.join(tokens[:-1]) if tokens[0]=='QUERY' else line
release=next(i for i,line in enumerate(old) if line.startswith('DOMAIN_RELEASE '))
prefix=[norm(line) for line in old[:release]];exact=[norm(line) for line in new[:release]]==prefix
assert exact,'Actual shared search prefix differs before release'
release_query=old[release].split()[1:];assert release_query==['2896','3']
oldattempts=[line for line in old[:release] if line.startswith('ATTEMPT 2896 3 ')];assert len(oldattempts)==9 and all(line.split()[-1]=='0' for line in oldattempts)
terminal=new[-1].split();assert terminal[0]=='COMPLETE' and terminal[-1]=='occupancy_restored'
old_dec=read(O/'reuse_on_decisions.json');assert old_dec['resources_under_timing']['accepted']
status=v['actual_status'];failed=status=='transaction_failed_rolled_back'
if failed:
 assert v['quality'] is None and terminal[1]=='0'
 assert any(q['net']==2896 and q['pin']==3 and not q['feasible'] for q in v['actual_queries'])
 interpretation='At this fixed input, group, query order, native search schedule and budget, turning off per-net failure release prevents group completion. Release enables the already admitted resource-feasible point; this does not prove global domain infeasibility or necessity for all LSTM groups/complete70SB difference.'
else:interpretation='No-release produced a legal candidate; retain its exact budgets/endpoints and compare against the original release candidate. Release necessity is not established by prior release participation.'
measure=read(B/'measurement/completion.json');vm=read(B/'verification_measurement/completion.json')
sources=[B/'plan.json',B/'queue/completion.json',B/'verification.json',B/'measurement/completion.json',B/'verification_measurement/completion.json',O/'reuse_on/runs/state/manifest.json',N/'reuse_on/runs/state/manifest.json',O/'reuse_on/runs/state/joint_native.log',N/'reuse_on/runs/state/joint_native.log',O/'reuse_on_decisions.json',D/'LSTM_domain_whole_admission_03/admission_decision.json',Path(__file__).resolve()]
result=dict(passed=True,decided_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='one retrospective-selected matched LSTM group, new no-release intervention only',only_actual_native_algorithm_environment_difference='VPR_JOINT_NATIVE_DOMAIN_FAILURE_RELEASE',actual_native_options_equal=True,full_search_prefix_before_release_identical_ignoring_elapsed_time=True,release_query=[2896,3],constrained_failed_attempts_before_release=len(oldattempts),release_reference=row,no_release_status=status,no_release_quality=v['quality'],original_source_route_and_full_vector_restored=v['all_original_source_bytes_and_full_vector_restored'],release_necessary_for_this_registered_search_completion=failed,complete_LSTM_causal_attribution=False,new_independent_inputs=0,component_wall_seconds=measure['complete_command_wall_seconds'],independent_verification_seconds=vm['complete_command_wall_seconds'],sampled_tree_PSS_peak_kib=measure['sampled_tree_PSS_peak_kib'],native_workers_new=v['native_repair_workers_new'],candidate_LOADs_new=v['candidate_LOADs_new'],interpretation=interpretation,source_sha256={str(f):sha(f) for f in sources})
write(B/'decision.json',result)
text='# LSTM失败释放：同源单标志消融已完成\n\n'
text+='**准入通过。** 实际原生命令一致；环境仅失败释放标志不同。相同源路由、8条请求、共享域、native binary、顺序及预算均保留。释放前搜索日志（除实际耗时）逐条一致。\n\n'
text+='| 处理 | 实际结果 | 资源/时序 |\n|---|---|---|\n'
text+='| 原开启释放（复用） | 整组完成，原资源规则接受 | 2388312线长/488SB/8316CB，14.600438192ns；相对本组源+206线长/−8SB，setup3改善/5退化 |\n'
text+=f'| 新关闭释放 | {status} | '+('无合法候选，质量为空；源路由与全部端点精确恢复' if failed else json.dumps(v['quality']))+' |\n\n'
text+='net2896/pin3的9档受限搜索均失败；原开启释放后继续完成，关闭时'+('回滚。' if failed else '结果如上。')+'这支持该固定搜索组的机制作用，不证明域在数学上不可路由，不将LSTM完整70SB差值全部归因于释放。该组按已有接受轨迹中最早有释放者选择，不是盲测或新独立输入。\n\n'
text+=f'新组件完整实测{measure["complete_command_wall_seconds"]:.6f}秒，独立核验{vm["complete_command_wall_seconds"]:.6f}秒；源字节预检{read(B/"source_preflight.json")["complete_readonly_seconds"]:.6f}秒另列。旧release执行及FULL/STA直接复用、不重跑，不用两种处理的组件耗时推算完整速度比。原ctime失败/回退/拒绝及LSTM完整费用限制不变。\n\n'
text+='本批剩余角色0。后续只更新论文失败释放归因及局部费用说明；投稿11独立主张保留，研究Goal继续active。\n'
(B/'RESULT.md').write_text(text);(B/'STATUS.md').write_text(text)
print({k:result[k] for k in ['passed','no_release_status','release_necessary_for_this_registered_search_completion','component_wall_seconds','independent_verification_seconds']})
