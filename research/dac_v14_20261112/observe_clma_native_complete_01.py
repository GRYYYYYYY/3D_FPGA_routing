"""Bind the actual native terminal checkpoint; final pair remains pending."""
from pathlib import Path
from datetime import datetime,timezone
import json,time
from retained_prefix_workflow import D,read,write,sha
from endpoint_timing_policy_streaming_v2 import compare
from seed_census_analysis_pool_v2 import process_identity
B=D/'cp1r6_clma_pair_01';r=read(B/'clma_results.json')['native'];case=Path(r['case']);v=read(case/'completion.json');assert r['status']=='complete_legal_verified' and v['passed']
initial=Path(v['initial_state']);final=Path(v['final_state']);e=compare(read(initial/'endpoint_vector.json'),read(final/'endpoint_vector.json'));assert e['compatible']
steps=read(case/'flow/timing/steps.json');attempts=read(case/'flow/timing/attempts.json');assert len(steps)==v['timing_accepted_steps']==5 and len(attempts)==8
active=read(B/'queue/status.json');identity=process_identity(active['pid']);assert active['arm']=='domain' and identity and identity['start_ticks']==active['start_ticks']
elapsed=time.monotonic()-int(identity['start_ticks'])/100
files=[Path(__file__).resolve(),case/'completion.json',case/'measurement/completion.json',case/'flow/timing/steps.json',case/'flow/timing/attempts.json',initial/'endpoint_vector.json',final/'endpoint_vector.json']
cpd_before=read(initial/'endpoint_vector.json')['cpd_s']*1e9
out=dict(observed_at=datetime.now(timezone.utc).isoformat(),native_original_execution_and_full_verifier_passed=True,native_raw_admission_pending=True,complete_pair_admission_pending=True,quality=r['quality'],initial_CPD_ns=cpd_before,own_root_endpoints={k:v for k,v in e.items() if k!='changes'},CPD_reduction_percent=(1-r['quality']['CPD_ns']/cpd_before)*100,wire_delta=100,resource_accepts=0,timing_accepts=5,timing_attempts=8,visited_state_rejections=sum(a.get('already_visited',False) for a in attempts),complete_command_seconds=r['complete_seconds'],independent_original_verification_seconds=r['independent_research_verification_seconds'],sampled_PSS_kib=r['sampled_PSS_kib'],missing_memory_observations=r['missing_memory_observations'],current_domain_owner=identity,conditional_ETA=dict(domain_elapsed_seconds=elapsed,reference_native_complete_seconds=r['complete_seconds'],domain_remaining_if_same_total_work_seconds=max(0,r['complete_seconds']-elapsed),remaining_original_roles=1,remaining_registered_raw_pair_stages=3,additional_registered_readonly_followup_stages=2,qualification='Conditional same-work reference only; domain may take different repair trajectory, host activity varies, and raw/pair/followup costs are additional. No deterministic completion promise or time ratio. Stage limits remain guards.'),source_sha256={str(p):sha(p) for p in files},new_native_or_STA_calls=0,qualification='Native final state and original88-assert checker passed; supplementary raw and complete pairing still pending. Shared native timing improvement cannot be attributed to domain. Only33setup/hold clocked components observed under clock-only20ns SDC; no external I/O/app closure claim.')
write(B/'native_complete_checkpoint_01.json',out)
(B/'NATIVE_COMPLETE.md').write_text(f'''# clma native整臂已执行结束并通过原核验

完整命令{r['complete_seconds']:.6f}秒；原独立核验{r['independent_research_verification_seconds']:.6f}秒单列。原88断言检查通过，但后续raw/配对仍待原队列。

CPD {cpd_before:.9f}→{r['quality']['CPD_ns']:.9f}ns（降低{out['CPD_reduction_percent']:.4f}%）；106027→106127线长，SB/CB同4/450。5次时序接受、3次访问状态拒绝，资源接受0。自身根setup{e['setup_improved']}改善/{e['setup_regressed']}退化，新增hold违规{e['hold_violation_regressions']}；观察到33个setup/hold分量，不能扩大为所有I/O均被显式约束。

Domain原臂已启动；按native668.98秒和相同工作量条件估计，仍需约{out['conditional_ETA']['domain_remaining_if_same_total_work_seconds']/60:.1f}分钟，加实际raw/配对及既有选择器解释费用。不同搜索轨迹或同机活动会改变时间，不承诺固定完成时刻。只有完整配对通过后才进入正文主表。
''')
print({k:out[k] for k in ['quality','own_root_endpoints','CPD_reduction_percent','complete_command_seconds','conditional_ETA']})
