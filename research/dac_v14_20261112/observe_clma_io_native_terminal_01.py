"""One terminal native observation, before final paired raw admission."""
from pathlib import Path
from datetime import datetime,timezone
import time
from retained_prefix_workflow import D,read,write,sha
from endpoint_timing_policy_streaming_v2 import compare
from seed_census_analysis_pool_v2 import process_identity
C=D/'cp1r6_clma_io_pair_01';r=read(C/'clma_io_results.json')['native'];case=Path(r['case']);done=read(case/'completion.json');assert r['status']=='complete_legal_verified' and done['passed']
initial=Path(done['initial_state']);final=Path(done['final_state']);iv=read(initial/'endpoint_vector.json');fv=read(final/'endpoint_vector.json');ep=compare(iv,fv);assert ep['compatible']
phase=read(C/'queue/status.json');identity=process_identity(phase['pid']);assert phase['arm']=='domain' and identity and identity['start_ticks']==phase['start_ticks']
elapsed=time.monotonic()-int(identity['start_ticks'])/100;attempts=read(case/'flow/timing/attempts.json');steps=read(case/'flow/timing/steps.json')
files=[Path(__file__).resolve(),case/'completion.json',case/'measurement/completion.json',initial/'endpoint_vector.json',final/'endpoint_vector.json',case/'flow/timing/steps.json',case/'flow/timing/attempts.json']
out=dict(observed_at=datetime.now(timezone.utc).isoformat(),original_native_execution_and_full_verifier_passed=True,raw_admission_pending=True,complete_pair_pending=True,quality=r['quality'],initial_CPD_ns=iv['cpd_s']*1e9,CPD_reduction_percent=(1-fv['cpd_s']/iv['cpd_s'])*100,own_root_endpoints={k:v for k,v in ep.items() if k!='changes'},resource_accepted_steps=done['resource_accepted_steps'],timing_accepted_steps=len(steps),timing_attempted_proposals=len(attempts),visited_state_rejections=sum(a.get('already_visited',False) for a in attempts),complete_command_seconds=r['complete_seconds'],original_verification_seconds=r['independent_research_verification_seconds'],sampled_PSS_kib=r['sampled_PSS_kib'],missing_memory_observations=r['missing_memory_observations'],conditional_ETA=dict(domain_elapsed_seconds=elapsed,reference_same_instance_native_complete_seconds=r['complete_seconds'],domain_remaining_if_same_total_work_seconds=max(0,r['complete_seconds']-elapsed),remaining_original_roles=1,remaining_raw_pair_stages=3,additional_terminal_decision_stages=1,qualification='Same-instance whole native command reference, conditional on comparable trajectory/host load. Raw/pair/decision costs are additional. Queued next-input packing/place starts after these gates, not in parallel; no deterministic ETA or complete paired ratio yet.'),source_sha256={str(p):sha(p) for p in files},new_native_or_STA_calls=0,new_independent_input=False,qualification='Explicit-I/O clma instance on same old physical inputs, fresh initial route differs. Native original verifier passed; complete raw/pair remains required. No domain increment or cross-SDC causal saving claim.')
write(C/'native_complete_checkpoint_01.json',out);(C/'NATIVE_COMPLETE.md').write_text(f'''# clma显式I/O native整臂结束及条件性ETA

原完整命令{r['complete_seconds']:.6f}秒，独立原核验{r['independent_research_verification_seconds']:.6f}秒。CPD{iv['cpd_s']*1e9:.9f}→{fv['cpd_s']*1e9:.9f}ns；最终资源{r['quality']['resources']}。setup{ep['setup_improved']}改善/{ep['setup_regressed']}退化，新增hold违规{ep['hold_violation_regressions']}，分量数{ep['setup_components']}/{ep['hold_components']}。时序接受{len(steps)}，访问状态拒绝{out['visited_state_rejections']}，原资源阶段接受{done['resource_accepted_steps']}。

原核验通过，raw/完整配对仍待原队列。domain按相同工作量参考剩余约{out['conditional_ETA']['domain_remaining_if_same_total_work_seconds']/60:.1f}分钟，加实际只读准入；轨迹/同机负载可能改变耗时，不推算正式比值。后续独立s38584.1输入准备排在所有必要核验后。旧SDC与新SDC的初始树不同，不把跨实例变化当作domain机制收益。投稿13保持。
''')
print({k:out[k] for k in ['quality','complete_command_seconds','own_root_endpoints','conditional_ETA']})
