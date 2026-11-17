"""Read closed small receipts; resolve nested timing without executing workers."""
import json
import math
import statistics
from datetime import datetime, timezone
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha

out = D/'LSTM_observation_cost_layers_01'
assert not out.exists()
plan = read(D/'cp1r3_distinct_input_cohort_01/plan.json')
base = Path(next(x for x in plan['inputs'] if x['id']=='lstm')['workspace'])
bound = {}
def small(path):
    assert path.stat().st_size < 1024*1024
    bound[str(path)] = sha(path)
    return read(path)

workers = []; transactions = []
for arm in ['native', 'domain']:
    repair = base/arm/'flow/resource_flow/repair'
    # Ordinary transactions only; owner callbacks have a different cost scope.
    for path in sorted(repair.glob('round_*/candidate_*/completion.json')):
        done = small(path); tx = path.parent
        assert done['passed']
        costs = small(tx/'process_costs.json')
        assert all(r['status']=='completed' and r['returncode']==0 for r in costs)
        total = done['complete_orchestrator_seconds']
        child = sum(r['complete_process_seconds'] for r in costs)
        assert math.isclose(child,done['complete_child_process_seconds'],abs_tol=1e-6)
        assert total >= child
        transactions.append(dict(arm=arm,transaction=str(tx),complete_seconds=total,
            child_seconds=child,outer_unclassified_seconds=total-child))
        for role,row in done['roles'].items():
            if row['status']=='not_executed_domain_candidate_accepted':continue
            assert row['status']=='legal_evaluated'
            for suffix,tag,kind in [('',role+'_native','source_observation'),
                                    ('_evaluation',role+'_FULL_STA','candidate_evaluation')]:
                matches = [c for c in costs if c['tag']==tag]
                if not matches:
                    assert kind=='candidate_evaluation' and row['reused_FULL_STA']
                    continue  # Reused historical observation is not charged again.
                assert len(matches)==1
                cost = matches[0]; receipt = small(tx/(role+suffix)/'completion.json')
                assert receipt['passed'] and receipt['process_status']=='completed'
                timing = receipt['timing']; observed = timing['complete_evaluation_seconds']
                components = {k:timing[k] for k in ['preparation_seconds','native_process_seconds','independent_audit_seconds']}
                assert all(math.isfinite(v) and v>=0 for v in components.values())
                residual = observed-sum(components.values())
                wrapper = cost['complete_process_seconds']-observed
                assert residual>=0 and wrapper>=0
                core = row['native_core_seconds'] if kind=='source_observation' else None
                if core is not None:assert 0<=core<=components['native_process_seconds']
                workers.append(dict(arm=arm,kind=kind,transaction=str(tx),worker=str(tx/(role+suffix)),
                    **components,worker_unclassified_seconds=residual,launcher_overhead_seconds=wrapper,
                    complete_worker_seconds=cost['complete_process_seconds'],nested_native_role_timer_seconds=core,
                    transaction_seconds=total,observation_only=receipt['observation_only']))

assert workers and transactions
fields=['preparation_seconds','native_process_seconds','independent_audit_seconds',
        'worker_unclassified_seconds','launcher_overhead_seconds','complete_worker_seconds']
groups=[]
for arm in ['native','domain']:
    for kind in ['source_observation','candidate_evaluation']:
        rows=[r for r in workers if r['arm']==arm and r['kind']==kind]
        assert rows
        groups.append(dict(arm=arm,kind=kind,count=len(rows),
            seconds={k:dict(min=min(r[k] for r in rows),mean=statistics.mean(r[k] for r in rows),
                           max=max(r[k] for r in rows)) for k in fields},
            nested_native_timer_fraction_of_transaction_range=(
                [min(r['nested_native_role_timer_seconds']/r['transaction_seconds'] for r in rows),
                 max(r['nested_native_role_timer_seconds']/r['transaction_seconds'] for r in rows)]
                if kind=='source_observation' else None)))

for name in ['run_serial_seed_resource_state_analysis_stream_v1.py',
             'run_serial_census_state_analysis_stream_v1.py','runtime_io.py']:
    source=Path(plan['release'])/'runtime'/name
    assert source.stat().st_size<1024*1024
    bound[str(source)]=sha(source)
assert all(sha(p)==h for p,h in bound.items())
out.mkdir(); (out/'receipts').mkdir()
for i,(path,digest) in enumerate(bound.items()):
    target=out/'receipts'/f'{i:03d}_{Path(path).name}'
    target.write_bytes(Path(path).read_bytes()); assert sha(target)==digest
write(out/'workers.json',workers); write(out/'transactions.json',transactions); write(out/'groups.json',groups)
write(out/'completion.json',dict(passed=True,observed_at=datetime.now(timezone.utc).isoformat(),
    closed_ordinary_transactions=len(transactions),observation_workers=len(workers),groups=groups,
    source_sha256=bound,new_native_or_STA_calls=0,whole_pair_quality_admitted=False,
    formal_pair_cost_ratio=None,original_failure_rewritten=False,
    qualification='Nested completed-receipt cost attribution only. Owner transactions excluded because callback work differs. Native process timer includes the supervised launch/wait/observer-stop envelope, not pure search or pure STA. Unclassified worker time includes work outside the three recorded intervals; it cannot all be assigned to hashing or Python. Preparation and audit scopes are read from frozen source. Historical reused candidate evaluation is never charged again. No complete algorithm time is assembled, no speedup claimed, no frozen code or running process changed.'))
lines=['# LSTM 已结束观测费用的层次归因','',
       '只读取已结束事务的小型回执及冻结源码，不启动native、STA或物理求解。owner事务因回调范围不同而单独排除。',
       '', '| 臂／观测类型 | 数量 | 准备均值 | 原生进程封装均值 | 独立审计均值 | 未细分工作均值 | 观测完整均值 |',
       '|---|---:|---:|---:|---:|---:|---:|']
for g in groups:
    t=g['seconds']; lines.append(f"| {g['arm']} / {g['kind']} | {g['count']} | "+
        ' | '.join(f"{t[k]['mean']:.2f}s" for k in ['preparation_seconds','native_process_seconds','independent_audit_seconds','worker_unclassified_seconds','complete_worker_seconds'])+' |')
lines += ['',
    '完整观测还包含少量启动封装时间，完整事务另有候选审计、域审计和控制器工作；JSON分别保留。原生角色内部timer嵌套在原生进程封装中，不能再次相加。', '',
    '源码边界：准备区间包含worker准入、源状态检查、输入准备及命令构造；原生进程区间覆盖启动、等待和observer停止，不是纯搜索或纯STA；独立审计区间对相同源路由复用并绑定物理证明，对新候选执行完整物理检查。整向量解析、输出及输入最终封存等位于未细分区间中，不能把该区间全部称为哈希开销。', '',
    '工程优先级由此细化：同时分析原生进程的初始化/加载/STA与封装层准备、候选物理审计，不能只优化内层搜索，也不能把其余全部归给Python。下一开发版本应在这些现有边界内细分计时，并对native/domain对称应用；不得删减完整向量、字节或物理门槛。只有同环境完整流程行为核验及实际计时后，才能报告优化收益。', '',
    '这不是新增独立输入、完整LSTM配对结果或工程加速证据。原native核验失败、当前domain未完成及全部已登记规则保持；投稿稿件不变。']
(out/'ENGINEERING_SCOPE.md').write_text('\n'.join(lines)+'\n')
print(dict(passed=True,transactions=len(transactions),workers=len(workers),groups=groups))
