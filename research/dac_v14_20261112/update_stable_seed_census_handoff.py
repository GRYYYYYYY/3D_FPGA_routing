#!/usr/bin/env python3
"""Record fresh owners and sealed evidence without altering any live cohort."""
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path

from export_policy_analysis_pool import process_identity
from retained_prefix_workflow import D, read, sha, write


def owner(name, directory, session):
    reg = read(directory / 'registration.json')
    actual = process_identity(reg['pid'])
    live = bool(actual and actual['state'] != 'Z'
                and actual['start_ticks'] == reg['start_ticks'])
    terminal = next((read(directory / f) for f in ['completion.json', 'failure.json']
                     if (directory / f).exists()), None)
    assert live or terminal is not None, (name, 'Missing owner needs reconciliation')
    phase = read(directory / 'status.json') if (directory / 'status.json').exists() else {}
    result = dict(batch=name, pid=reg['pid'], start_ticks=reg['start_ticks'],
                  verified_live=live, actual_process=actual, observed_at=now,
                  registration=str(directory / 'registration.json'), phase=phase,
                  terminal_receipt=terminal, tool_session=session)
    if 'pid' in phase:
        child = process_identity(phase['pid'])
        result['phase_child_actual'] = child
        result['phase_child_live'] = bool(child and child['state'] != 'Z'
                                         and child['start_ticks'] == phase.get('start_ticks'))
    return result


now = datetime.now(timezone.utc).isoformat()
history = D / 'continuation_history' / ('stable_seed_census_' + str(time.time_ns()))
history.mkdir()
receipts = {name: owner(name, D / directory, session) for name, directory, session in [
    ('fused_resource_development_01', 'fused_resource_development_01/queue', 53193),
    ('fused_resource_archive_queue_01', 'fused_resource_archive_queue_01', 24213),
    ('merge_seed_resource_archive_queue_01', 'merge_seed_resource_archive_queue_01', 88338),
    ('seed_census_client_validation_01', 'seed_census_client_validation_01', 33227),
    ('stable_seed_transfer_dev_01', 'stable_seed_transfer_dev_01/queue', 67432),
]}
active = [r for r in receipts.values() if r['verified_live']]
queued = [r for r in active if r['phase'].get('status', '').startswith('waiting_')]
running = [r for r in active if r not in queued]
archive_name = 'multiobjective_archive_52'
merged = D / 'multiobjective_merged_seed_resource_01/completion.json'
if merged.exists() and read(merged).get('passed'):
    archive_name = merged.parent.name
archive = read(D / archive_name / 'completion.json')
native = read(D / 'BNN_extended_native_menu_01.json')
seed = read(D / 'repair_seed_order_mechanism_01.json')
census = read(D / 'native_resource_census_eltwise_02/completion.json')
paper = read(D / 'stable_seed_census_paper_binding_01.json')
assert native['passed'] and seed['passed'] and census['passed'] and paper['passed']
steps_path = D / 'fused_resource_development_01/bnn_A0_feedback_K8/steps.json'
steps = read(steps_path) if steps_path.exists() else []
next_actions = [
    'Preserve registered native-order fused cohort: same version, roots, acceptance and K8/rank3. Native actor sealed5accepts/8scopes at13.607436066820355ns,2059591wire/82SB/5062CB. Paired private prefix remains provisional until actor-final context seal. Extended native control is stronger than the old2accept86SB pilot; compare whole own-current trajectories, not unequal prefixes.',
    'Existing single archive owner24213 waits for cohort53193; merge owner88338 then combines all sealed resource observations with the301-record seed diagnostic branch. Do not duplicate writers or promote unsealed prefixes. Diagnose actual terminal failures in the main model and retain partial passed actors; branch/menu exhaustion never stops the research goal.',
    'Actual source-by-policy diagnostic passed6transactions plus6independent candidate LOADs: native source serializations yield217214 vs217191wire; rr_id yields217214 for both; delay_rr_id yields217183 for both, all at6.018101128546505ns/24SB/965CB. This is one fixed repaired-source diagnostic, not pristine-root automatic success. Three later real native cost rows differ; whole23wire effect is not proved to be an equal-cost heap tie. Exact ordered source bytes remain in query/cache identity.',
    'Seed census client owner33227 waits for original cohort to terminate before pool2 launch. Validate actual flags/receipts/cache identity, counter source/candidate/restored binding, representation invariance, mutation and forged-record rejection. Do not infer client completion from standalone native proof. No live source/config edits or competing pool owners.',
    'After actual client validation passes, registered transfer owner67432 runs8 own-current pristine-root cases: eltwiseA0 andBNN A0/R1/Tf, native and paired. Global delay_rr_id, K8/rank3/compact, same rootCPD and absolute resource budgets; no manual repaired prefix, per-circuit history-best or inherited candidate timing. All existing Python physical/scope/tree audits remain enabled; new native counts are shadow checks. This is development, not frozen confirmation or equal-compute evidence.',
    'Native counter standalone proof passed2reused OFF/ON workers plus2new jobs; ordered route body, full-precision STA, seeds and actual search costs unchanged, all physical metrics match independent audit for source/candidate/restored/plain input. Counter assurance is native_actual_route_tree_census, explicitly not independent physical audit. The first validation failed an overstrict private header path byte guard; preserve failure/cost, compare bound placement plus exact ordered route body instead.',
    'Runtime profile of sealed extended native actor2061.278666s imported workflow: native requests572.636, reconstruction330.428, tree equivalence136.646, candidate materialization/physical audit543.796, selector167.255, other stages recorded. Native census fast acceptance consumer is NOT implemented. After client/shadow proof, build an explicit native-assurance consumer and separate final independent validation; never fabricate independent_audit.json. Evaluate matched native controls and retain failed checks/STA/rollback costs.',
    'Resource-first strict timing trajectory remains3accepts ending13.228145689936355ns/2059882wire/79SB/5061CB, whole vectors equal prior timing-first endpoint but different ordered route body. No new quality point or general commutation. Old low-wire andCB5059/5060 states remain on distinct tradeoffs pending matched complete runtime; strong-baseline dominated states remain diagnostic evidence, not quality wins.',
    'Joint Pareto archive includes strongA0/R1/U/Tf, native extra opportunities and guided states; retain legal CPD/resource/time tradeoffs with precision-aware dominance and unknown-time status. Different versions/convergence/batches remain distinct. No borrowing U time, summing recovery/shared/replay into cold route+repair time, or calling occupancy area/power. Fixed intermediate budgets are design parameters, not goal stops.',
    'Focused manuscript C175v2 is6pages with stronger82SB native control and explicit archive52+9sealed-native-state figure population. Keep the separate64page evidence manuscript. Actual current client/global transfer and whole cold timing are outstanding; do not upgrade component proofs to global quality/speed claims. New work remains local; public snapshot f7167bd unchanged.',
    'Continue evidence-led capacity release plus grouped critical repair and timing/resource objective variants with native FULL, freshSTA, realTdel/counters and rollback. Confirmation freezes circuit-independent policy/version after development; no whole-goal date, route cap, fixed matrix or author-list termination. New failures require diagnosis and another supported branch, not only adjacent parameter sweeps.',
]
for filename in ['CONTINUATION.json', 'live_handoff.json']:
    path = D / filename
    shutil.copy2(path, history / filename)
    value = read(path)
    value.update(updated_at=now, observed_at=now, research_state='active',
                 current_goal_state='active', previous_goal_turn_classification='progress',
                 research_blockers=[], old_caps_revoked=True, author_metadata_blocks_research=False,
                 running_jobs=running, queued_jobs=queued, active_jobs=active, active_owners=active,
                 supervisors=active, runners=active, next_actions=next_actions,
                 latest_owner_verification=receipts, latest_paper=paper)
    value['latest_multiobjective'] = dict(archive=archive_name, points=archive['records'],
        diagnostic_branch='multiobjective_seed_order_diag_01', diagnostic_branch_records=301,
        merge_owner=receipts['merge_seed_resource_archive_queue_01'],
        record_count_is_not_configuration_count=True, complete_cold_configuration_seconds=None,
        new_work_pushed=False)
    value['multiobjective_policy']['archive'] = archive_name
    value['latest_fused_resource_development'] = receipts['fused_resource_development_01']
    value['latest_fused_resource_archive'] = receipts['fused_resource_archive_queue_01']
    value['latest_extended_native_control'] = dict(summary='BNN_extended_native_menu_01.json',
        sealed=True, CPD_ns=native['CPD_ns'], resources=native['resources'],
        accepted_steps=native['accepted_steps'], complete_imported_workflow_seconds=native['complete_imported_workflow_seconds'],
        complete_cold_configuration_seconds=None)
    value['latest_paired_private_prefix'] = dict(accepted_steps_observed=len(steps),
        latest_committed_evaluation=steps[-1]['committed_evaluation'] if steps else None,
        actor_seal_required=True, not_a_final_archive_point=True)
    value['latest_seed_order'] = dict(stage='repair_seed_order_stage_01',
        mechanism='repair_seed_order_mechanism_01.json', native_binding='repair_seed_order_native_binding_01.json',
        source_representation_invariance=seed['source_representation_invariance'],
        actual_resources=seed['actual_resources'], global_transfer=receipts['stable_seed_transfer_dev_01'])
    value['latest_native_resource_census'] = dict(stage='native_resource_census_stage_01',
        validation='native_resource_census_eltwise_02/completion.json', standalone_passed=True,
        assurance_kind='native_actual_route_tree_census', independent_physical_audit=False,
        fast_acceptance_consumer_implemented=False, shadow_keeps_independent_audits=True,
        actual_client=receipts['seed_census_client_validation_01'], complete_algorithm_speedup=None)
    value['latest_native_pending'] = dict(status='registered_own_current_cohort_and_seed_transfer', owners=active)
    value['active_current_sta_batch'] = dict(owners=active, registered_versions_unchanged=True,
        combined_native_VPR_maximum=3, per_pool_parent_plus_child=2,
        complete_cold_configuration_seconds=None)
    value['next_algorithm_hypothesis'] = next_actions[4:7]
    value['git_publication']['new_work_pushed'] = False
    write(path, value)
protocol = D / 'RESEARCH_PROTOCOL.md'
marker = '20261114_explicit_seed_native_census_transfer'
if marker not in protocol.read_text():
    with protocol.open('a') as out:
        out.write(f'\n\n{now} {marker}\n'
            '原运行批次及冻结规则不变。BNN原生own-current actor已终封5接受/8scope：'
            '13.607436066820355ns/2059591wire/82SB/5062CB，比原始A0多24wire少12SB；'
            '旧2接受86SB只能作为pilot前缀。配对actor继续，须终封才归档。原归档owner24213与新合并owner88338单写者链保留。\n'
            '独立源码增加native/rr_id/delay_rr_id种子顺序，实际3×2表示对照证明两种稳定策略消除本例源序列化差异；'
            'delay_rr_id得到217183wire/24SB/965CB/6.018101ns。真实后续搜索代价有差异，不把全部23wire归因为等成本heap tie。'
            '12tiny、6实际事务+6独立LOAD和6强制分支/后续查询检查通过；不外推为全局算法提升。\n'
            '独立native资源计数与原物理审查单位一致，源/实际候选/恢复/普通输入验证通过；原生计数不是独立审查。'
            '原计数验证01因私有PlaceFile头路径字节guard失败，02复用2实际worker并新运行2job校正，不重写原失败。'
            'client owner33227待原cohort结束验证固定flag/receipt/cache与伪造/可变控制拒绝，'
            'transfer owner67432仅在其实际通过后启动8个原始A0/R1/Tf own-current native/paired开发case，'
            '统一delay_rr_id/K8/rank3/compact及原根绝对预算；Python全套审查仍保留作shadow对照。\n'
            '2061.28s原生导入研究流程中原生request572.64s，重建330.43s、树检查136.65s、候选物理审查543.80s；'
            '后续据此研究明确原生保证接口的快速consumer+最终独立审查，目前未实现，不宣称完整加速。'
            '导入/双策略/恢复/core/冷route+repair各自记录，不拼接旧U时间。\n'
            '现有档案52为295观测，独立seed诊断分支301，合并待真实owner结果；'
            '六页C175v2论文与64页详细证据分开封存。保留强A0/R1与联合前沿、CPD稍差的资源/时间取舍；'
            '预算/菜单耗尽不是Goal终止条件。当前新增本地未推送，Goal持续active，无日期/总调用/矩阵/作者清单停止。\n')
write(history / 'update_binding.json', dict(passed=True, observed_at=now, owners=receipts,
    native_calls=0, route_calls=0, source_sha256={str(p): sha(p) for p in [
        Path(__file__).resolve(), D/'BNN_extended_native_menu_01.json',
        D/'repair_seed_order_mechanism_01.json', D/'native_resource_census_eltwise_02/completion.json',
        D/'stable_seed_census_paper_binding_01.json', D/archive_name/'completion.json']},
    updated_artifact_sha256={str(D/n): sha(D/n) for n in ['CONTINUATION.json','live_handoff.json','RESEARCH_PROTOCOL.md']}))
print(dict(active=[r['batch'] for r in active], queued=[r['batch'] for r in queued],
           archive=archive_name, records=archive['records'], paired_private_accepts=len(steps),
           history=str(history)), flush=True)
