"""Analyze already-admitted LSTM owner attempts without executing routing/STA."""
from pathlib import Path
from datetime import datetime,timezone
import fcntl,hashlib,json,time
from endpoint_timing_policy_streaming_v2 import compare

D=Path(__file__).resolve().parent
OUT=D/'LSTM_existing_owner_outcomes_01'
BASE=Path('/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home/confirmation_workspaces/cp1r3_distinct_input_cohort_01/lstm')
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):Path(p).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
def main():
 start=time.monotonic();decision=D/'LSTM_domain_whole_admission_03/admission_decision.json';d=read(decision)
 assert d['complete_pair_admission']=='passed' and not d['gaps']
 assert all(sha(p)==h for p,h in d['source_sha256'].items())
 assert not OUT.exists();OUT.mkdir();bound={str(decision):sha(decision),str(Path(__file__).resolve()):sha(Path(__file__).resolve())};summary=[];alternatives=[]
 for arm,round_name,raw in [('native','round_004',D/'LSTM_necessary_readonly_02/native_raw'),('domain','round_016',D/'LSTM_domain_whole_admission_03/raw')]:
  raw_completion=read(raw/'completion.json');assert raw_completion['passed'];raw_tx=read(raw/'transactions.json');states=read(raw/'states.json');flow=BASE/arm/'flow';repair=flow/'resource_flow/repair';attempts=read(repair/'attempts.json');select=repair/round_name/'owner_selection';selection=read(select/'completion.json');groups=read(select/'groups.json')
  assert selection['passed'] and selection['certified_escape_cuts']==5 and selection['eligible_joint_groups']==len(groups)==40
  selected=[x for x in attempts if x.get('mechanism')=='capacity_certified_owner_coordination'];assert len(selected)==3
  bound.update({str(p):sha(p) for p in [raw/'completion.json',raw/'transactions.json',raw/'states.json',repair/'attempts.json',select/'completion.json',select/'groups.json',flow/'completion.json']})
  final=Path(read(flow/'completion.json')['final_state']);final_vector=final/'endpoint_vector.json';bound[str(final_vector)]=sha(final_vector);final_summary=next(r for r in d['rows'] if r['arm']==arm)['quality']
  for rank,entry in enumerate(selected):
   tx=Path(entry['transaction']);role='joint_native';assert tx.name==f'owner_{rank:02d}' and not entry.get('accepted_role') and entry['roles'][role]['status']=='legal_evaluated'
   assert any(x['transaction']==str(tx) and any(y['role']==role and y['status']=='legal_evaluated' for y in x['roles']) for x in raw_tx)
   worker=tx/role/'completion.json';evaluation=tx/(role+'_evaluation')/'completion.json';policy=tx/(role+'_decisions.json');w=read(worker);e=read(evaluation);p=read(policy)['resources_under_timing'];assert w['passed'] and all(w['checks'].values()) and e['passed'] and not p['accepted'];assert str(worker) in raw_completion['source_sha256'] and str(evaluation) in raw_completion['source_sha256'];assert sha(worker)==raw_completion['source_sha256'][str(worker)] and sha(evaluation)==raw_completion['source_sha256'][str(evaluation)]
   candidate=tx/(role+'_evaluation');st=next(x for x in states if x['state']==str(candidate));assert st['actual_FULL_raw_STA_and_original_physical_proof_bound'];metrics=st['resources'];vector=candidate/'endpoint_vector.json';cmp=compare(read(final_vector),read(vector));assert cmp['compatible'];bound.update({str(q):sha(q) for q in [worker,evaluation,policy,vector]})
   summary.append(dict(arm=arm,rank=rank,certificates=selection['certified_escape_cuts'],eligible_groups=selection['eligible_joint_groups'],attempted_groups=3,current_state=entry['current_state'],target_net=groups[rank]['target_net'],owner_net=groups[rank]['owner_net'],resource_delta_from_own_state=p['resource_delta'],original_accepted=False,original_reason=p['reason'],candidate_quality={'CPD_ns':st['CPD_ns'],'resources':metrics},versus_own_final={k:v for k,v in cmp.items() if k!='changes'}))
   if rank==1:
    assert p['resource_delta']['SB_pairs']==p['resource_delta']['CB_sources']==0 and p['resource_delta']['wirelength']<0
    assert metrics['wirelength']<final_summary['resources']['wirelength'] and metrics['SB_pairs']==final_summary['resources']['SB_pairs'] and metrics['CB_sources']==final_summary['resources']['CB_sources'] and cmp['cpd_before_s']==cmp['cpd_after_s'] and cmp['setup_regressed']>0 and cmp['hold_violation_regressions']==0
    assert metrics['wirelength']<=p['resource_limits']['wirelength'] and metrics['SB_pairs']<=p['resource_limits']['SB_pairs'] and metrics['CB_sources']<=p['resource_limits']['CB_sources'] and cmp['cpd_after_s']<=p['cpd_limit_s']
    alternatives.append(dict(arm=arm,candidate_quality={'CPD_ns':st['CPD_ns'],'resources':metrics},final_quality=final_summary,versus_own_final={k:v for k,v in cmp.items() if k!='changes'},original_policy_rejection=p['reason'],candidate_was_originally_accepted=False,scope='Archived legal rejected local candidate, not a selected complete controller outcome.'))
 write(OUT/'owner_attempts.json',summary);write(OUT/'alternatives.json',alternatives)
 lines=['# LSTM 已执行 owner 候选：容量见证与预算结果','','两臂在各自不同中间状态均有 5 个受支持容量切口、40 个通过余量筛选的 owner 组；原计划各执行前三组，三组均被资源策略拒绝。它们不是同一起点的 owner 因果配对，也不能推出其余37组无效。','','| 臂 | rank | 相对自身事务前线长/SB/CB | 原资源策略 | 原因 |','|---|---:|---|---|---|']
 for x in summary:
  z=x['resource_delta_from_own_state'];lines.append(f"| {x['arm']} | {x['rank']} | {z['wirelength']}/{z['SB_pairs']}/{z['CB_sources']} | 拒绝 | {x['original_reason']} |")
 lines+=['','rank 1 已有原始 FULL、STA、物理、请求及端点只读证明，满足已登记绝对资源和 CPD 上限；原控制器因 SB/CB 无改善而拒绝。对比各自已准入最终终点：']
 for x in alternatives:
  a=x['candidate_quality']['resources'];b=x['final_quality']['resources'];v=x['versus_own_final'];lines.append(f"- {x['arm']}：候选 {a['wirelength']}/{a['SB_pairs']}/{a['CB_sources']}，最终 {b['wirelength']}/{b['SB_pairs']}/{b['CB_sources']}；CPD 相同，setup 相对最终改善 {v['setup_improved']}、退化 {v['setup_regressed']}，新增 hold 违例 {v['hold_violation_regressions']}。")
 lines+=['','这些候选是已拒绝的局部替代工作点，不是完整控制器选出结果，也不改写原判定；短线长与端点退化共同保留。此分析不执行新 native、STA 或路由查询，不拼接完整费用，不改变已冻结的确认规则或论文收益。']
 (OUT/'ANALYSIS.md').write_text('\n'.join(lines)+'\n');write(OUT/'completion.json',dict(passed=True,updated_at=datetime.now(timezone.utc).isoformat(),new_native_or_STA_calls=0,new_route_queries=0,complete_readonly_seconds=time.monotonic()-start,arms=2,original_attempts=6,untried_groups_per_state=37,alternatives=2,original_decisions_unchanged=True,paper_claims_changed=False,source_sha256=bound,artifact_sha256={n:sha(OUT/n) for n in ['owner_attempts.json','alternatives.json','ANALYSIS.md']}));print(json.dumps(dict(passed=True,alternatives=2,new_native_or_STA_calls=0)))
if __name__=='__main__':
 with (D/'critical_scope_runner.lock').open() as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);main()
