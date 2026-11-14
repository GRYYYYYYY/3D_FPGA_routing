#!/usr/bin/env python3
"""Fresh authoritative owners and direct-audit progress; zero native submissions."""
from datetime import datetime,timezone
from pathlib import Path
import shutil
import time
from retained_prefix_workflow import D,read,write,sha
from seed_census_analysis_pool_v2 import process_identity

now=datetime.now(timezone.utc).isoformat()
history=D/'continuation_history'/('direct_scope_'+str(time.time_ns()));history.mkdir()
owners=[];receipts={}
for name,directory,session in [
    ('fused_resource_development_01','fused_resource_development_01/queue',53193),
    ('fused_resource_archive_queue_01','fused_resource_archive_queue_01',24213),
    ('merge_seed_resource_archive_queue_01','merge_seed_resource_archive_queue_01',88338),
    ('seed_census_client_validation_01','seed_census_client_validation_01',33227),
    ('stable_seed_transfer_dev_01','stable_seed_transfer_dev_01/queue',67432),
    ('direct_scope_resource_equivalence_02','direct_scope_resource_equivalence_02/queue',60372),
]:
    root=D/directory;reg=read(root/'registration.json');p=process_identity(reg['pid'])
    live=bool(p and p['state']!='Z' and p['start_ticks']==reg['start_ticks'])
    terminal=next((read(root/f) for f in ['completion.json','failure.json'] if (root/f).exists()),None)
    assert live or terminal is not None,(name,'Missing authoritative owner')
    phase=read(root/'status.json') if (root/'status.json').exists() else {}
    row=dict(batch=name,pid=reg['pid'],start_ticks=reg['start_ticks'],verified_live=live,
        actual_process=p,phase=phase,terminal_receipt=terminal,observed_at=now,
        registration=str(root/'registration.json'),tool_session=session)
    if 'pid' in phase:
        c=process_identity(phase['pid']);row['phase_child_actual']=c
        row['phase_child_live']=bool(c and c['state']!='Z' and c['start_ticks']==phase.get('start_ticks'))
    receipts[name]=row
    if live:owners.append(row)
proof=read(D/'direct_native_transaction_validation_01/completion.json');assert proof['passed']
assert read(D/'direct_scope_actor_preparation_01.json')['passed']
paired=D/'fused_resource_development_01/bnn_A0_feedback_K8'
steps=read(paired/'steps.json');last=steps[-1]
winner=next(row for row in last['pair'].values() if row.get('evaluation')==last['committed_evaluation'])
private=dict(accepted_steps_observed=len(steps),latest_committed_evaluation=last['committed_evaluation'],
    CPD_s=winner['CPD_s'],resources=winner['resources'],actor_seal_required=True,
    not_a_final_archive_point=not (paired/'completion.json').exists())
queued=[r for r in owners if r['phase'].get('status','').startswith('waiting_')]
actions=[
    'Original native-order paired actor still retains its registered inputs/rules. Latest private prefix is read from accepted steps, not stale status;7accepts observed at13.607436066820355ns/2061265wire/45SB/5060CB. Compared with individually sealed native82SB point this is+1674wire/-37SB/-2CB, not a final equal-runtime or cold superiority claim. Wait for full actor seal; registered resource archive and merge single writers then reconcile all legal states/rejections with strong baselines.',
    'DirectTransactionAudit independently checks actual installed candidate trees, exact source/request/static/native receipt binding, source/restored full-precision equality, requested sinks, retained edges, every untouched net, logged NODE identity, actual selected graph edges and complete capacity. It never serializes another candidate or alters search order; physical-equivalence checks are not cache keys. Forced-path reservations explicitly unsupported by this API; FULL/newSTA, domain and independent physical/resource checks remain separate.',
    'New direct audit passed6 predetermined sealed accepted/legal-rejected transactions (first/last per eltwise native/paired andBNN native actor), same scope/query/attempt/switch-delay changes as old reconstruction and6corruption guards,0VPRcalls. BNN replay21.53/20.79s vs historical reconstruction34.73/35.68s are component observations, not a formal paired speedup. Direct scope does not yet replace resource materialization/independent physical audit or claim full algorithm speed.',
    'New independent actor run_direct_scope_shadow_resource_repair.py retains selector, global seed policy, native search, full independent physical audit, native-counter shadow and acceptance; replaces reconstruction+second full-tree comparison with direct audit. Actual owner60372 waits for existing stable-seed cohort67432 to finish, then runs4 predetermined pristine A0 native/paired eltwise/BNN cases. Requires complete matching predecessor case; verifies all scopes/arm acceptance, every accepted ordered route and full vector, final independent metrics and search-child count. No per-circuit winner choice or competing native pool.',
    'The first newly-created direct-equivalence waiter was replaced before any native submission solely to correct absent-commit normalization. Its completion receipt records0nativecalls and replacement direct_scope_resource_equivalence_02. Original experiments and every registered original source remain untouched. No blind restarting of native jobs.',
    'After original cohort, actual client33227 validates fixed seed/census controls; stable-seed67432 then runs8 pristine A0/R1/Tf native/paired cases with global delay_rr_id and full Python audits. These earlier real owners remain authoritative, not just plans. Any failure or trajectory mismatch goes to substantive diagnosis; other passed matching branches can proceed. Native parent+child2, totalVPRmax3; per-child memory/time/disk protection remains.',
    'Once the resource-rich paired actor seals, analyze whether its lower SB/CB endpoint admits current-STA timing repair at the same resource slice; reselect on its own latest STA. Reuse static identities/references only after graph/root/sink matching, and give native timing controls the same scope/selector/opportunity. Do not import the old79SB repaired vector or declare general phase commutation from one matching endpoint.',
    'Native resource counter has separate native assurance, not independent audit. Fast native-count acceptance consumer still unimplemented; priority after actual client/shadow proof is explicit state/resource interface plus final independent validation, guided by recorded physical/reconstruction costs. Cold full route+repair and frozen broad confirmation remain outstanding. Do not borrow U timing or combine historical/core/shared/recovery times.',
    'Joint archive and manuscript still keep all strong A0/R1/U/Tf quality tradeoffs and uncertainty, including CPD-slower low-wire/lowCB candidates. Current6pageC175v2 excludes private45SB point until final seal. New direct-audit evidence is local development evidence, not an integrated result. Goal active; no dates/totalcalls/matrix/authors stopping conditions. No new push requested or made.',
]
for filename in ['CONTINUATION.json','live_handoff.json']:
    path=D/filename;shutil.copy2(path,history/filename);value=read(path)
    value.update(updated_at=now,observed_at=now,research_state='active',current_goal_state='active',
        previous_goal_turn_classification='progress',research_blockers=[],old_caps_revoked=True,
        author_metadata_blocks_research=False,active_jobs=owners,active_owners=owners,
        runners=owners,supervisors=owners,queued_jobs=queued,
        running_jobs=[r for r in owners if r not in queued],next_actions=actions,
        latest_owner_verification=receipts,latest_paired_private_prefix=private)
    value['latest_direct_native_scope_audit']=dict(validation='direct_native_transaction_validation_01/completion.json',
        passed=True,cases=proof['cases'],native_calls=0,negative_controls=proof['negative_controls'],
        actor='run_direct_scope_shadow_resource_repair.py',
        queue=receipts['direct_scope_resource_equivalence_02'],actual_integrated_equivalence_passed=None,
        native_count_fast_consumer_implemented=False,complete_algorithm_speedup=None,
        old_waiter_terminal='direct_scope_resource_equivalence_01/queue/completion.json')
    value['latest_fused_resource_development']=receipts['fused_resource_development_01']
    value['latest_fused_resource_archive']=receipts['fused_resource_archive_queue_01']
    value['active_current_sta_batch']=dict(owners=owners,registered_original_versions_unchanged=True,
        combined_native_VPR_maximum=3,per_pool_parent_plus_child=2,complete_cold_configuration_seconds=None)
    value['latest_native_pending']=dict(status='own_current_cohort_then_registered_seed_and_direct_scope_controls',owners=owners)
    value['next_algorithm_hypothesis']=actions[5:8]
    value['git_publication']['new_work_pushed']=False
    merged=D/'multiobjective_merged_seed_resource_01/completion.json'
    if merged.exists() and read(merged).get('passed'):
        value['latest_multiobjective'].update(archive=merged.parent.name,points=read(merged)['records'])
        value['multiobjective_policy']['archive']=merged.parent.name
    write(path,value)
protocol=D/'RESEARCH_PROTOCOL.md';marker='20261114_direct_actual_scope_engineering'
if marker not in protocol.read_text():
    with protocol.open('a') as out:
        out.write(f'\n\n{now} {marker}\n'
            '原cohort/规则不变，配对actor已观察7接受13.607436066820355ns/2061265wire/45SB/5060CB，'
            '比终封native82SB多1674wire少37SB/2CB；仍私有未终封，不作最终前沿/公平完整时间结论。'
            '封存后优先检查同资源条件的current-STA修复，不套用旧目标或旧79SB结果。\n'
            '独立direct_native_transaction_audit.py直接审查VPR实际候选，保留树/端点/其他net/实际边/完整容量、'
            '实际receipt/request/source及恢复向量均核对，不再重建另一份候选；该API明确不支持forced reservations。'
            '六个预定封存真实事务及六类损坏检查通过，0新VPR；两个BNN审查21.53/20.79s，'
            '旧重建34.73/35.68s为历史组件值，不能宣称正式匹配加速。\n'
            '独立run_direct_scope_shadow_resource_repair保留全物理/FULLSTA/domain/native-counter shadow审查；'
            'equivalence_02真实owner60372在原stable-seed队列结束后做四个预定A0 native/paired自动流程，'
            '要求所有接受/拒绝与scope、逐步有序路由/完整向量/最终独立物理指标等价，失败记录后诊断。'
            '初建waiter01仅修正无commit状态比较记录，提交0实验后封存替换，无原实验被终止。\n'
            '当前原生计数快速接受consumer仍未实现；导入流程和冷完整route+repair分别记录，'
            '不借旧U时间，不将占用称面积/功耗，不从四case或八case结束推断整个Goal完成。'
            '新增本地未推送，研究持续active。\n')
write(history/'update_binding.json',dict(passed=True,observed_at=now,owners=receipts,
    native_calls=0,route_calls=0,source_sha256={str(p):sha(p) for p in [Path(__file__).resolve(),
    D/'direct_native_transaction_validation_01/completion.json',D/'direct_scope_actor_preparation_01.json']},
    updated_artifact_sha256={str(D/n):sha(D/n) for n in ['CONTINUATION.json','live_handoff.json','RESEARCH_PROTOCOL.md']}))
print(dict(active=[r['batch'] for r in owners],private_prefix=private,history=str(history)),flush=True)
