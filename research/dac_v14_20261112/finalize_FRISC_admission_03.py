"""Report actual terminal gates; no rerouting, new raw audit or inferred benefit."""
from datetime import datetime, timezone
from pathlib import Path
import fcntl
from retained_prefix_workflow import D, read, write, sha
from recovery_prefix_v1 import live_identity

ROOT=D/'FRISC_sdc_readonly_02'
COHORT=D/'cp1r5_frisc_pair_01'


def main():
    assert not (ROOT/'admission_decision.json').exists()
    with (D/'critical_scope_runner.lock').open() as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        for q in [COHORT/'queue',ROOT/'queue']:
            reg=read(q/'registration.json')
            assert not live_identity(reg['pid'],reg['start_ticks'])
            assert (q/'completion.json').exists()
        terminal=read(ROOT/'admission_stage_accounting_03.json')
        pair=read(ROOT/'pair/completion.json')
        original=read(COHORT/'frisc_results.json')
        raw={arm:read(ROOT/arm/'completion.json') for arm in ['native','domain']}
        matched=bool(pair.get('passed') and pair.get('matched_complete_quality_pair'))
        sources=[Path(__file__).resolve(),ROOT/'plan.json',ROOT/'queue/completion.json',ROOT/'admission_stage_accounting_03.json',ROOT/'pair_recovery_registration_03.json',ROOT/'pair_recovery_measurement_03/completion.json',
                 ROOT/'pair/completion.json',COHORT/'frisc_results.json',COHORT/'queue/completion.json']
        rows=[];gaps=[]
        for arm,r in raw.items():
            path=ROOT/arm/'completion.json';sources.append(path)
            expected=pair.get('source_sha256',{}).get(str(path.resolve()))
            if expected is None:
                assert not matched
                gaps.append(dict(arm=arm,gate='pair_source_binding',reason='Pair gate did not bind this role receipt'))
            else:assert sha(path)==expected
            admitted=bool(r.get('passed') and r.get('quality_admitted'))
            ep=None
            if admitted:
                p=ROOT/arm/'own_initial_final_endpoints.json';ep=read(p);sources.append(p)
                replay=read(ROOT/'supplement/cases/frisc'/arm/'replayed_verifier/completion.json')
                assert r['quality']=={k:replay[k] for k in ['CPD_ns','resources']}
                assert original[arm]['quality'] is None and original[arm]['status']=='execution_or_verification_failed'
                assert r['complete_algorithm_seconds']==original[arm]['complete_seconds']
            else:gaps.append(dict(arm=arm,status=r.get('status'),reason=r.get('error',r.get('reason'))))
            rows.append(dict(arm=arm,execution_ended=True,original_status=original[arm]['status'],
                quality_admission='passed' if admitted else 'not_passed',quality=r.get('quality') if admitted else None,
                own_root_endpoint_summary={k:v for k,v in ep.items() if k!='changes'} if ep else None,
                legal_no_gain_to_own_root=r.get('legal_no_gain'),timeout=r.get('timeout'),
                infrastructure_error=r.get('infrastructure_error'),
                complete_command_seconds=original[arm]['complete_seconds'],
                original_verification_seconds=original[arm]['independent_research_verification_seconds'],
                sampled_PSS_GiB=original[arm]['sampled_PSS_kib']/1024**2,
                missing_memory_observations=original[arm]['missing_memory_observations']))
        same=None
        if matched:
            assert all(r['quality_admission']=='passed' for r in rows)
            same=(raw['native']['quality']==raw['domain']['quality'] and
                  raw['native']['final']['vector_semantic_sha256']==raw['domain']['final']['vector_semantic_sha256'])
        elif not gaps:gaps.append(dict(gate='pair',reason=pair.get('error',pair.get('status'))))
        decision=dict(decided_at=datetime.now(timezone.utc).isoformat(),rows=rows,
            complete_pair_admission='passed' if matched else 'not_passed',gaps=gaps,
            domain_minus_native=pair.get('delta_domain_minus_native') if matched else None,
            paired_endpoint_summary=pair.get('paired_endpoint_summary') if matched else None,
            identical_final_working_point_including_full_vector=same,
            descriptive_single_pair_time_ratio=pair.get('descriptive_single_pair_time_ratio') if matched else None,
            formal_interleaved_time_ratio=None,readonly_stage_costs=terminal.get('stages',[]),
            waiting_seconds=terminal.get('wait_for_predecessor_seconds'),
            complete_readonly_queue_seconds=terminal.get('complete_queue_seconds'),
            new_native_or_STA_calls=0,new_architecture=False,new_to_current_CP1_circuit=True,architecture_configuration="Hybrid_O",
            original_failures_rewritten=False,automatic_manuscript_update=False,
            source_sha256={str(p):sha(p) for p in sources},
            qualification=('Supplementary frozen-check replay with original report-only SDC declaration plus existing raw/request/FULL/STA/physical and state continuity gates passed; original verifier failures retained; actual initial trees/vectors/constraints/six graph payloads paired. ' if matched else 'Original checkers passed, but additional raw admission did not pass; actual complete pair matching is not admitted. Null quality denotes an admission gap, not routing failure or infeasibility. ')+
                'Own-root gain and domain increment are separate. Costs are real whole commands; audits/waiting separate. Single N/D observation on shared host is not symmetric interleaved timing or universal superiority.')
        write(ROOT/'admission_decision.json',decision)
        lines=['# Frisc整臂判定与完整配对','',
               '**实际配对：'+('通过' if matched else '未通过')+'。**','',
               '| 角色 | 质量准入 | CPD(ns) | 线长/SB/CB | 自身根setup改善/退化/hold新增 | 完整命令(s) | PSS(GiB) |',
               '|---|---|---:|---:|---:|---:|---:|']
        for row in rows:
            q=row['quality'];e=row['own_root_endpoint_summary']
            quality=f"{q['CPD_ns']:.9f} | "+'/'.join(str(q['resources'][k]) for k in ['wirelength','SB_pairs','CB_sources']) if q else '— | —'
            endpoints=f"{e['setup_improved']}/{e['setup_regressed']}/{e['hold_violation_regressions']}" if e else '—'
            lines.append(f"| {row['arm']} | {row['quality_admission']} | {quality} | {endpoints} | {row['complete_command_seconds']:.6f} | {row['sampled_PSS_GiB']:.3f} |")
        if matched:
            delta=decision['domain_minus_native'];e=decision['paired_endpoint_summary']
            lines += ['',f"D−N：线长{delta['wirelength']:+d}、SB{delta['SB_pairs']:+d}、CB{delta['CB_sources']:+d}、CPD{delta['CPD_ns']:+.9f}ns；setup {e['setup_improved']}改善/{e['setup_regressed']}退化，hold新增{e['hold_violation_regressions']}。"]
            if same:lines += ['','完整终态工作点与全端点向量相同；本输入未观察到domain增量。两臂共有的时序或资源改善不能归给域限制或失败释放。']
            ratio=decision['descriptive_single_pair_time_ratio']
            lines += ['',f"单次完整N/D实测费用比{ratio:.6f}（{(ratio-1)*100:+.3f}%），仅描述该次配对，不是N/D/D/N对称计时或统计速度主张。未拼接组件费用。"]
        else:lines += ['','具体缺口：']+[str(x) for x in gaps]
        lines += ['','原独立检查及后续只读费用另列：']
        for row in rows:lines.append(f"- {row['arm']}原检查：{row['original_verification_seconds']}秒。")
        for stage in terminal.get('stages',[]):lines.append(f"- {stage['stage']}只读阶段：{stage['complete_command_seconds']:.6f}秒，{stage['status']}。")
        lines += ['','Frisc为当前CP1确认中的不同公开顺序电路，使用新生成的实际布局和现有Hybrid-O架构族。不称新架构、未见留出集或外部应用要求。原始输入准备失败、全部拒绝及费用保留；上游打包和布局不拼入完整命令。原SDC报告缺字段失败保持；补充重放仅从登记前20ns时钟SDC填充报告元数据，88条断言不变，I/O约束未补造。配对入口重复取锁的独立失败及后续单项恢复均保留。只有本次实际准入支持的表格和适用性可更新，投稿10在此之前保持。']
        (ROOT/'PAIR_TABLE.md').write_text('\n'.join(lines)+'\n')
        print(dict(pair_admitted=matched,identical_working_point=same,gaps=gaps))


if __name__=='__main__':main()
