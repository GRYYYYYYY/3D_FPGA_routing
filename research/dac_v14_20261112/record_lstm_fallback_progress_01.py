"""Bounded receipt snapshot; never admits an unfinished confirmation role."""
import datetime
import json
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha

out = D/'LSTM_native_fallback_progress_01'
assert not out.exists()
repair = Path('/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home/confirmation_workspaces/cp1r3_distinct_input_cohort_01/lstm/domain/flow/resource_flow/repair')
tx = repair/'round_011/candidate_00'
receipt = read(tx/'completion.json')
assert receipt['passed']
for p, h in receipt['source_sha256'].items():
    assert Path(p).stat().st_size < 2_000_000
    assert sha(p) == h
on, off = receipt['roles']['reuse_on'], receipt['roles']['reuse_off']
assert not on['policies']['resources_under_timing']['accepted']
assert off['policies']['resources_under_timing']['accepted']
assert off['resources'] == dict(wirelength=2390370, SB_pairs=426, CB_sources=8316)
out.mkdir()
bound = {}
for p in [tx/'completion.json', *map(Path, receipt['source_sha256'])]:
    target = out/'receipts'/p.name
    target.parent.mkdir(exist_ok=True)
    target.write_bytes(p.read_bytes())
    bound[str(p)] = sha(target)
current = (repair/'current_state.json').read_bytes()
(out/'current_state_snapshot.json').write_bytes(current)
observed = datetime.datetime.now(datetime.timezone.utc).isoformat()
state = json.loads(current)
roles = read(D/'submission_candidate_followup_02/role_status_and_eta.json')['role_states']
decisions = {name: read(tx/(name+'_decisions.json')) for name in ['reuse_on','reuse_off']}
comparison = {name: {k:v for k,v in d['endpoint_vector']['comparison'].items() if k != 'changes'} for name,d in decisions.items()}
single = [read(p)['complete_orchestrator_seconds'] for p in sorted(repair.glob('round_0[01][0-9]/candidate_00/completion.json')) if read(p).get('roles',{}).get('reuse_off',{}).get('status') == 'skipped_after_domain_resource_acceptance']
# Explicit historical calibration; the current double-pass observation is new.
single_low, single_high = 505.0548777580261, 530.2649465538561
double = receipt['complete_orchestrator_seconds']
owner = [655.658279,662.136143]
tail = 839.158877
scenarios = []
for extra in [0,3,6]:
    # Current partial transaction: 0 to one observed full double-pass duration.
    # Three closing probes/owner windows are conditional scheduling assumptions.
    lo = ((3+extra)*single_low+3*owner[0]+tail)/60
    hi = (double+(3+extra)*double+3*owner[1]+tail)/60
    scenarios.append(dict(hypothetical_further_accepts=extra,
        remaining_domain_minutes=[lo,hi],
        confirmation_and_supplement_hours=[lo/60+2+10/60,hi/60+8+40/60]))
write(out/'progress_and_eta.json',dict(observed_at=observed, accepted_prefix_steps=state['accepted_steps'],
    current_state=state, completed_round='round_011/candidate_00',
    completed_transaction_seconds=double, roles=roles, checkpoint_arms=dict(domain=on,native_fallback=off),
    endpoint_comparisons=comparison, source_sha256=bound,
    attribution='Domain candidate violates wire cap by327. Native fallback saves64wire/1SB from prior state, remaining wire105. This transition is native fallback, not evidence of a domain benefit.',
    conditional_scenarios=scenarios, ordinary_single_pass_seconds=[single_low,single_high],
    double_pass_seconds=double, additional_raw_admission_eta=None,
    assumptions=['Current transaction residual0..one double-pass duration, not a measured remaining runtime.',
                 'Three closing probes and three owner windows as in native menu; no new success count limit.',
                 'Remaining four roles2..8hours provisional; DLA not calibrated.',
                 'Supplemental original-check replay10..40min provisional; raw admission uncalibrated.',
                 'Any further accepted scopes, timeouts, additional owner work or infrastructure diagnosis extend ETA.'],
    whole_role_quality_admitted=False, whole_role_seconds=None, formal_paired_ratio=None,
    new_native_or_STA_calls=0, running_rules_changed=False, original_failures_preserved=True))
(out/'ETA.md').write_text('''# LSTM 原生回退与条件性排程

第十二次提交来自同源原生回退。域候选2390802/421/8316超出2390475线长上限327，原生候选2390370/426/8316满足资源规则；相对上一步少64线长/1SB，线长余量105。两者CPD均不变，但setup分别5改善/1退化与4改善/1退化，hold违例均不增加。该完整双臂事务实测1069.864590秒，不是完整角色费用。

运行中的第十三轮又进入域拒绝后的原生回退，不能再只用此前约505–530秒的单臂事务估算余量。条件性情景采用约1070秒的双臂观察、当前事务剩余0–1070秒、3个闭菜单探测、3个owner窗口和约14分钟历史尾段。假设另有0/3/6次接受，当前domain余量约72–118/97–171/122–225分钟。随后四角色暂估2–8小时，补充原检查重审暂估10–40分钟，因此整体约3.4–12.4小时，另加尚未标定的原始证据准入。情景计数是排程假设，不是停止条件；新接受、失败诊断或超时会延长。

LSTM/native已执行结束，但原验证失败，质量尚未准入；domain仍运行，其余四角色待执行。上述仅为小回执快照与排程预测，不是完整配对收益或拼接的算法费用。原始失败保持不变，补充与raw准入继续在原队列终结后优先执行。
''')
print(json.dumps(dict(output=str(out),observed_at=observed,scenarios=scenarios)))
