"""Read existing selectors and admitted pair decisions; no new queries."""
from pathlib import Path
import json,hashlib,datetime
D=Path(__file__).resolve().parent;O=D/'mechanism_applicability_current_03';O.mkdir(exist_ok=False)
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):Path(p).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
spec=[('TPU-OS','cp1r5_tpu_os_pair_01','TPU_OS_complete_admission_02'),('CLSTM-SB','cp1r5_clstm_sb_pair_01','CLSTM_SB_complete_admission_01'),('elliptic','cp1r5_elliptic_pair_01','ELLIPTIC_complete_admission_01'),('frisc','cp1r5_frisc_pair_01','FRISC_sdc_readonly_02'),('clma clock','cp1r6_clma_pair_01','CLMA_complete_admission_01'),('clma I/O','cp1r6_clma_io_pair_01','CLMA_IO_complete_admission_01'),('s38584 native only','cp1r6_s38584_pair_01',None)]
rows=[];files=[Path(__file__).resolve()]
for label,cohort,admit in spec:
 plan=D/cohort/'plan.json';v=read(plan);case=Path(v['inputs'][0]['workspace'])/'native/flow/resource_flow/repair/round_000';sp=case/'selection/completion.json';s=read(sp);assert s['passed'];files.extend([plan,sp]);op=case/'owner_selection/completion.json';o=read(op) if op.exists() else {};files.extend([op] if op.exists() else [])
 decision=read(D/admit/'admission_decision.json') if admit else None
 if decision:assert decision['complete_pair_admission']=='passed';files.append(D/admit/'admission_decision.json')
 r=s['actual_resources'];rows.append(dict(label=label,initial_multi_crossing_nets=s['multi_crossing_nets'],initial_STA_eligible_scopes=s['candidate_scopes'],initial_owner_groups=o.get('eligible_joint_groups'),initial_SB=r['sb_pairs_used'],initial_CB=r['cb_crossing_output_sources_used'],domain_minus_native=decision.get('domain_minus_native') if decision else None,complete_pair_admitted=bool(decision),scope='current native initial root only; paired final delta when admitted'))
write(O/'rows.json',rows)
lines=['# 当前输入上的机制适用性（既有证据）','','不同版本/预算/布局是不同配置，不把配置数当独立电路样本；此表不训练预测器，也不将初始机会直接当收益。s38584只包含原核验通过的native初始阶段，domain及raw配对待终结。','','| 配置 | 初始冗余跨层网 | 有限STA共享组 | 支持owner组 | 初始SB/CB | 最终D−N线长/SB/CB |','|---|---:|---:|---:|---|---|']
for r in rows:
 d=r['domain_minus_native'];delta='/'.join(str(d[k]) for k in ['wirelength','SB_pairs','CB_sources']) if d else '待配对';owner='未知' if r['initial_owner_groups'] is None else str(r['initial_owner_groups']);lines.append(f"| {r['label']} | {r['initial_multi_crossing_nets']} | {r['initial_STA_eligible_scopes']} | {owner} | {r['initial_SB']}/{r['initial_CB']} | {delta} |")
lines+=['','已完成反例约束后续规则：TPU-OS有19个初始共享组但完整配对没有垂直资源增量；CLSTM-SB有14组且最终少1 SB、多52线长，不是独立CLSTM电路。数量不是收益阈值。clma时钟型有3冗余网、3个结构可复用组，但原pin余量未知而全部屏蔽；I/O变体覆盖扩大时fresh树同时改变，不能把组消失归因于某个单独因素。','', '筛选规则只能提出可执行机会：需要完整共享分支、有限可用时序余量、域阻塞的实际失败或容量owner见证，以及整组合法与预算接受；无上述见证不编造机制收益。当前s38584原生资源阶段没有冗余网或共享组，后续时序与domain/配对仍需完整结果，不预判一般适用性。', '', '资源节省不是制造面积/功耗测量，完整费用和失败保留在投稿14主表及各原回执；新数据不增加任何domain收益主张。']
(O/'APPLICABILITY.md').write_text('\n'.join(lines)+'\n');write(O/'completion.json',dict(passed=True,rows=len(rows),complete_pair_rows=sum(r['complete_pair_admitted'] for r in rows),pending_native_only_rows=1,scope_count_is_not_gain_predictor=True,same_clma_variants_not_independent_circuits=True,new_native_or_STA_calls=0,source_sha256={str(p):sha(p) for p in files},artifact_sha256={n:sha(O/n) for n in ['rows.json','APPLICABILITY.md']}));print(dict(passed=True,rows=len(rows),new_native_or_STA_calls=0))
