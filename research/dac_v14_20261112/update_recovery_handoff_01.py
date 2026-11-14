"""Record reconciled interruptions and actual replacement owners, without changing the Goal."""
from datetime import datetime,timezone
from pathlib import Path
import shutil
import time
from retained_prefix_workflow import D,read,write,sha
from seed_census_analysis_pool_v2 import process_identity

now=datetime.now(timezone.utc).isoformat();history=D/'continuation_history'/('recovery_'+str(time.time_ns()));history.mkdir()
owners=[]
for name,session in [('completed_resource_timing_recovery_01',76992),('vector_feedback_subset_native_recovery_01',60108),
    ('stable_seed_transfer_recovery_01',88100),('direct_scope_resource_equivalence_recovery_01',27462),
    ('native_census_resource_equivalence_recovery_01',26617)]:
    q=D/name/'queue';r=read(q/'registration.json');actual=process_identity(r['pid'])
    live=bool(actual and actual['state']!='Z' and actual['start_ticks']==r['start_ticks'])
    terminal=read(q/'completion.json') if (q/'completion.json').exists() else None
    assert live or terminal is not None
    phase=read(q/'status.json') if (q/'status.json').exists() else {}
    owners.append(dict(batch=name,pid=r['pid'],start_ticks=r['start_ticks'],verified_live=live,
        actual_process=actual,phase=phase,terminal_receipt=terminal,observed_at=now,
        registration=str(q/'registration.json'),tool_session=session))
active=[r for r in owners if r['verified_live']];queued=[r for r in active if r['phase'].get('status','').startswith('waiting_')]
archive=read(D/'multiobjective_complete_resource_timing_01/completion.json');assert archive['passed']
summary=read(D/'multiobjective_complete_resource_timing_01/composition_summary.json')
actions=[
    'User explicitly resumed. Old five owner PIDs and recorded children were absent on repeated checks, exclusive old locks available, tool sessions lost, no terminal receipts. Cause unknown; do not claim numerical failure or continued original execution. See resume_interruption_reconciliation_01.json. Original artifacts remain untouched; replacement owners are actually running in private directories.',
    'completed_resource_timing_recovery_01 resumes the frozen v4 actor with --resume-from the original paired checkpoint, original initial state/caps/policy/source hashes and all three accepted states. Source observations/native82 completed trajectory are reused, not rerun. Old partial capacity-query evidence remains available for exact reuse. Recovery and missing interruption elapsed time remain separate from cold timing.',
    'vector_feedback_subset_native_recovery_01 waits on the actual recovered serial timing owner. Same pre-registered two-target/three-donor subset, original45SB source and strict/full-vector acceptance. Only private output and prerequisite owner changed. Never splice this45SB source with the complete43SB endpoint.',
    'stable_seed_transfer_recovery_01 reuses four fully sealed original A0 cases and runs only the three never-submitted R1-paired/Tf-native/Tf-paired cases, unchanged actor, global seed/ranking/caps/rules. The interrupted bnn_R1_native checkpoint has4accepts and completed worker receipts but lacks original pool final seal. Its dedicated checkpoint/materialization recovery remains outstanding; do not claim it failed numerically, discard it, fabricate its epoch seal, or rerun its pristine root.',
    'direct_scope_resource_equivalence_recovery_01 waits for the recovered transfer chain; its four references are the original fully sealed A0 cases. native_census_resource_equivalence_recovery_01 waits on that actual direct-scope owner. Scientific actors, parameter rules and comparators unchanged. Only one pool2 chain plus serial native1; no competing old owners.',
    'Archive multiobjective_complete_resource_timing_01 contains335legal observations, adding actual full-resource-endpoint timing states. At identical13.228145689936355ns native uses2059627wire/82SB/5062CB; paired saved third accept uses2061389/43/5060. +1762wire buys39SB/2CB; both nondominated in collected quality population and neither is dominated by strongA0/R1. Native timing terminal; paired trajectory closure pending. All state FULL/independent physical/input seals passed. Full endpoint comparison550better/799worse, so same CPD is not endpointwise superiority. No cold timing or initial routability claim.',
    'Next: complete serial recovery and failure-derived subset, interpret exact setup/donor/near-band outcomes; then integrate a general current-state feedback scope only if evidence supports it. Independently recover the interrupted R1-native private context with validated source/runtime/worker receipts and no repeated completed native requests. Missing final pool seal is a validation task, not overall blocked/termination.',
    'Keep stronger native controls and fixed global development rules; validate direct-scope/native-count whole trajectories before speedup claims. Timing-first resource opportunity extension and resource-priced unrestricted native search remain mechanism-distinct followups. Complete cold per-configuration times, broader frozen-policy suite and failure/tail accounting remain outstanding.',
    'Platform get_goal still usageLimited after explicit resume; tools cannot clear it. Scientific work ongoing; do not reset/create/complete/block Goal or restore date/count/matrix/author stops. Public snapshot f7167bd unchanged. Latest paper snapshot C183v2 remains immutable; new335-observation delta is documented separately pending next manuscript/PDF integration.'
]
for name in ['CONTINUATION.json','live_handoff.json']:
    p=D/name;shutil.copy2(p,history/name);v=read(p)
    v.update(updated_at=now,observed_at=now,research_state='ongoing',current_goal_state='usageLimited',
        explicit_user_resume_received=True,platform_automatic_continuation_limited=True,research_blockers=[],
        old_caps_revoked=True,author_metadata_blocks_research=False,active_jobs=active,active_owners=active,
        supervisors=active,runners=active,queued_jobs=queued,running_jobs=[r for r in active if r not in queued],
        latest_owner_verification={r['batch']:r for r in owners},next_actions=actions,
        latest_recovery_reconciliation='resume_interruption_reconciliation_01.json',
        latest_complete_resource_timing_states=summary,
        pending_interrupted_resource_case='stable_seed_transfer_dev_01/bnn_R1_native',
        active_current_sta_batch=dict(owners=active,combined_native_VPR_maximum=3,registered_versions_unchanged=True))
    v['latest_multiobjective']=dict(archive='multiobjective_complete_resource_timing_01',points=archive['records'],
        summary='multiobjective_complete_resource_timing_01/composition_summary.json',quality_counts=archive['quality_counts'],
        retention_counts=archive['retention_counts'],record_count_is_not_configuration_count=True,
        complete_cold_configuration_seconds=None,new_work_pushed=False)
    v['multiobjective_policy']['archive']='multiobjective_complete_resource_timing_01'
    v['latest_completed_resource_timing']=owners[0]
    v['latest_vector_feedback_subset'].update(owner=owners[1],actual_native_outcome_pending=owners[1]['terminal_receipt'] is None)
    v['latest_native_resource_census'].update(live_equivalence_owner=owners[4],full_automatic_equivalence_pending=True)
    v['latest_native_pending']=dict(status='reconciled_recovery_and_registered_followups',owners=active)
    v['next_algorithm_hypothesis']=actions[5:8]
    v['git_publication']['new_work_pushed']=False
    write(p,v)
protocol=D/'RESEARCH_PROTOCOL.md';marker='20261114_explicit_resume_interrupted_owners_01'
if marker not in protocol.read_text():
    with protocol.open('a') as f:
        f.write('\n\n'+now+' '+marker+'\n'
            '用户恢复后，旧五owner及子PID两次缺失、锁可取得、会话句柄不存在；原因未知，不能继续称其活跃或视为数值失败。'
            '在独立目录建立实际恢复owner：43SB strict从原v4检查点续跑，三次接受/原始anchor/绝对预算/精度规则保留；'
            '其后为原45SB五连接feedback，原科学输入接受不改。另原四A0终封case只复用，R1paired/Tf两模式此前未提交的原case继续。'
            'R1native四接受checkpoint及完成worker保留，原pool最终seal缺失，专门恢复验证待做，不能伪造seal或重新跑root。'
            'direct-scope及native-count真实后续owner重新挂接，仍pool2+serial1并发上限；每进程保护保留。\n'
            '档案335新增完整resource菜单后的实际时序状态：同CPD13.228145689936355ns，native2059627wire/82SB/5062CB，'
            'paired2061389/43/5060，多1762wire少39SB/2CB；FULL/独立物理/input seals通过。native终封，paired轨迹待恢复收口。'
            '全向量550改善799退化，不能称端点逐项支配；完整冷路由加修复时间未知，中断/恢复时间分列。'
            '论文原C183v2冻结，新增证据写独立delta待下一稿集成；研究持续，无总体日期/调用数/矩阵停止。\n')
write(history/'binding.json',dict(passed=True,observed_at=now,owners=owners,native_calls=0,
    source_sha256={str(p):sha(p) for p in [Path(__file__).resolve(),D/'resume_interruption_reconciliation_01.json',D/'multiobjective_complete_resource_timing_01/completion.json']},
    updated_artifact_sha256={str(D/n):sha(D/n) for n in ['CONTINUATION.json','live_handoff.json','RESEARCH_PROTOCOL.md']}))
print(dict(active=[r['batch'] for r in active],archive=archive['records'],history=str(history)),flush=True)
