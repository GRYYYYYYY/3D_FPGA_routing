"""Summarize existing original and raw gates after the registered queue ends."""
from pathlib import Path
from datetime import datetime,timezone
import fcntl,json,hashlib
from recovery_prefix_v1 import live_identity
D=Path(__file__).resolve().parent;B=D/'S38417_complete_admission_01';C=D/'cp1r6_s38417_pair_01'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):Path(p).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
def main():
 assert not (B/'admission_decision.json').exists()
 lock=(D/'critical_scope_runner.lock').open();fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 for root in [B,C]:
  reg=read(root/'queue/registration.json');assert not live_identity(reg['pid'],reg['start_ticks']);assert (root/'queue/completion.json').exists()
 pair=read(B/'pair/completion.json');original=read(C/'s38417_results.json');stages=read(B/'stages.json');rows=[];gaps=[]
 matched=bool(pair.get('passed') and pair.get('matched_complete_quality_pair'))
 files=[Path(__file__).resolve(),B/'plan.json',B/'pair/completion.json',B/'stages.json',B/'queue/completion.json',C/'s38417_results.json',C/'queue/completion.json']
 for arm in ['native','domain']:
  p=B/arm/'completion.json';raw=read(p);files.append(p);admitted=bool(raw.get('passed') and raw.get('quality_admitted'));ep=None;full=None
  if admitted:
   assert matched and pair['source_sha256'][str(p)]==sha(p)
   case=Path(original[arm]['case']);full=read(case/'completion.json');assert full['passed'] and original[arm]['status']=='complete_legal_verified'
   assert raw['quality']=={k:full[k] for k in ['CPD_ns','resources']};assert raw['complete_algorithm_seconds']==original[arm]['complete_seconds']
   ep=read(B/arm/'own_initial_final_endpoints.json');files.extend([case/'completion.json',B/arm/'own_initial_final_endpoints.json'])
  else:gaps.append(dict(arm=arm,status=raw.get('status'),reason=raw.get('error',raw.get('reason'))))
  rows.append(dict(arm=arm,execution_ended=True,original_status=original[arm]['status'],admission='passed' if admitted else 'not_passed',quality=raw.get('quality') if admitted else None,own_root_endpoints={k:v for k,v in ep.items() if k!='changes'} if ep else None,complete_command_seconds=original[arm]['complete_seconds'],original_verification_seconds=original[arm]['independent_research_verification_seconds'],sampled_PSS_GiB=original[arm]['sampled_PSS_kib']/1024**2,missing_memory_observations=original[arm]['missing_memory_observations'],legal_no_gain=raw.get('legal_no_gain'),timeout=raw.get('timeout'),infrastructure_error=raw.get('infrastructure_error')))
 if not matched and not gaps:gaps.append(dict(gate='pair',reason=pair.get('error',pair.get('status'))))
 equal=None
 if matched:
  n,d=[read(B/a/'completion.json') for a in ['native','domain']];equal=n['quality']==d['quality'] and n['final']['vector_semantic_sha256']==d['final']['vector_semantic_sha256']
 out=dict(decided_at=datetime.now(timezone.utc).isoformat(),complete_pair_admission='passed' if matched else 'not_passed',gaps=gaps,rows=rows,domain_minus_native=pair.get('delta_domain_minus_native') if matched else None,paired_endpoint_summary=pair.get('paired_endpoint_summary') if matched else None,identical_final_working_point_including_full_vector=equal,descriptive_single_pair_time_ratio=pair.get('descriptive_single_pair_time_ratio') if matched else None,formal_interleaved_time_ratio=None,readonly_stages=stages,upstream_costs=read(D/'VTR_s38417_input_01/completion.json')['costs'],new_native_or_STA_calls=0,new_to_current_CP1_circuit=True,new_architecture_family=False,source_sha256={str(p):sha(p) for p in files},qualification='Original full checker plus original raw/request/FULL/STA/vector/physical/state-chain and pair gates. This summary executes no new native queries. Explicit20ns clock plus IOmax1/min0 benchmark SDC, no external application timing claim. Whole measured commands only; preparation/audits separate. Single pair costs descriptive, not symmetric timing or statistical speedup. Preserve all original failed/rejected attempts.')
 write(B/'admission_decision.json',out)
 lines=['# S38417整臂判定与完整配对','','**配对：'+('通过' if matched else '未通过')+'。**','','| 角色 | 准入 | CPD(ns) | 线长/SB/CB | 自身根setup改善/退化/新增hold | 完整秒数 | PSS(GiB) |','|---|---|---:|---|---|---:|---:|']
 for r in rows:
  q=r['quality'];e=r['own_root_endpoints'];quality=f"{q['CPD_ns']:.9f} | "+'/'.join(str(q['resources'][k]) for k in ['wirelength','SB_pairs','CB_sources']) if q else '— | —';ends=f"{e['setup_improved']}/{e['setup_regressed']}/{e['hold_violation_regressions']}" if e else '—'
  lines.append(f"| {r['arm']} | {r['admission']} | {quality} | {ends} | {r['complete_command_seconds']:.6f} | {r['sampled_PSS_GiB']:.3f} |")
 if matched:lines+=['','D−N：'+json.dumps(out['domain_minus_native'],ensure_ascii=False),'','最终全端点向量及质量相同：'+str(equal)+'。共同原生时序改善与domain增量须区分；单次费用仅描述。']
 else:lines+=['','具体缺口：'+json.dumps(gaps,ensure_ascii=False)]
 lines+=['','完整费用属于实际同一臂命令；上游打包/布局、独立核验和只读准入单列，不拼接完整时间。新SDC报告来自实际文件，不补造I/O延迟。保留所有负结果、失败、策略拒绝及超时；不将局部出口未阻塞或无共享域组当全局不可行。研究Goal保持active。']
 (B/'PAIR_TABLE.md').write_text('\n'.join(lines)+'\n');print(dict(pair_admission=out['complete_pair_admission'],gaps=gaps))
if __name__=='__main__':main()
