"""Add the admitted elliptic applicability result, protecting submission09."""
import fcntl
import shutil
from datetime import datetime, timezone
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha


def main():
    old=D/'submission_narrative_09'; new=D/'submission_narrative_10'
    root=D/'ELLIPTIC_complete_admission_01'
    decision=read(root/'admission_decision.json')
    assert decision['complete_pair_admission']=='passed' and decision['gaps']==[]
    # This edit is for a confirmed absent-domain-increment case, not an assumed outcome.
    assert decision['identical_final_working_point_including_full_vector'] is True
    rows={r['arm']:r for r in decision['rows']}
    assert all(r['quality_admission']=='passed' for r in rows.values())
    assert all(r['quality']['resources']['SB_pairs']==0 and r['quality']['resources']['CB_sources']==0 for r in rows.values())
    assert all(r['own_root_endpoint_summary']['setup_improved']==260 and
               r['own_root_endpoint_summary']['setup_regressed']==0 and
               r['own_root_endpoint_summary']['hold_violation_regressions']==0 for r in rows.values())
    assert read(old/'verification.json')['passed']
    assert not new.exists();new.mkdir()
    for directory in ['data','supplement']:
        shutil.copytree(old/directory,new/directory,copy_function=shutil.copyfile)
    for filename in ['LSTM_PAIR_TABLE.md','TPU_OS_PAIR_TABLE.md','CLSTM_SB_PAIR_TABLE.md']:
        shutil.copyfile(old/filename,new/filename)
    supplementary=new/'supplement/ELLIPTIC_complete_pair';supplementary.mkdir()
    for rel in ['admission_decision.json','PAIR_TABLE.md','plan.json','stages.json','queue/completion.json',
                'native/completion.json','domain/completion.json','pair/completion.json',
                'native/own_initial_final_endpoints.json','domain/own_initial_final_endpoints.json',
                'pair/endpoint_changes.json']:
        dest=supplementary/rel;dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(root/rel,dest)
    for directory in ['VTR_elliptic_input_01','cp1r5_elliptic_pair_01']:
        src=D/directory
        names=['completion.json','registration.json','capacity_selection.json','packing_provenance.json'] if directory.startswith('VTR') else ['plan.json','native_resource_terminal_01.json','native_complete_checkpoint_01.json','elliptic_results.json']
        for name in names:
            dest=supplementary/directory/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src/name,dest)
    shutil.copyfile(root/'PAIR_TABLE.md',new/'ELLIPTIC_PAIR_TABLE.md')
    shutil.copyfile(root/'admission_decision.json',new/'data/ELLIPTIC_complete_pair_admission.json')
    source=(old/'main.tex').read_text();text=source
    text=text.replace('TPU-OS shows no additional domain saving.',
        'TPU-OS adds no domain saving; a distinct elliptic circuit has no vertical occupancy and identical native/domain timing gains.')
    text=text.replace('BNN, LSTM, TPU-OS and CLSTM-SB include resource and subsequent timing repair;',
        'BNN, LSTM, TPU-OS, CLSTM-SB and elliptic include resource and subsequent timing repair;')
    text=text.replace('TPU-OS and CLSTM-SB are single N/D observations.',
        'TPU-OS, CLSTM-SB and elliptic are single N/D observations.')
    marker='CLSTM-SB CP1r5 D&6.590324&234970/940/0&918.13&2.770&193/644/0\\\\\n'
    assert text.count(marker)==1
    added=[]
    for arm,label in [('native','N'),('domain','D')]:
        row=rows[arm];q=row['quality'];r=q['resources']
        added.append(f"Elliptic CP1r5 {label}&{q['CPD_ns']:.6f}&{r['wirelength']}/{r['SB_pairs']}/{r['CB_sources']}&{row['complete_command_seconds']:.2f}&{row['sampled_PSS_GiB']:.3f}&260/0/0\\\\\n")
    text=text.replace(marker,marker+''.join(added))
    text=text.replace('later GEMM, TPU-OS and CLSTM-SB pairs remain accounted for',
        'later GEMM, TPU-OS, CLSTM-SB and elliptic pairs remain accounted for')
    paragraph=("Elliptic is a distinct public sequential circuit with a fresh native placement on Hybrid-O. Its legal root occupies no counted SB or CB, yielding no resource group. Both arms instead make one timing commit: 12.426958129 to 12.419319795 ns for 32 extra wire, with 260 setup improvements and no regressions. Final full vectors match; there is no domain increment. Complete N/D costs are "
        f"{rows['native']['complete_command_seconds']:.2f}/{rows['domain']['complete_command_seconds']:.2f} s. Three visited-state rejections per arm remain; packing/placement and audits are separate.\n\n")
    marker='\\section{Mechanism Attribution and Budget Sensitivity}'
    assert text.count(marker)==1;text=text.replace(marker,paragraph+marker)
    text=text.replace('Historical recovery trajectories remain supplementary.',
        'Elliptic illustrates the absent-crossing boundary: native timing improvement is not domain benefit. Historical recovery remains supplementary.')
    text=text.replace('TPU-OS adds no domain benefit. These positive and negative cases bound the method\'s measured applicability.',
        'TPU-OS and elliptic add no domain benefit, bounding the measured applicability.')
    # Freeze problem, insight, design, prior art and mechanism controls exactly.
    begin='\\section{Introduction}';end='\\section{Validation and Matched Complete Results}'
    assert source.split(begin)[1].split(end)[0]==text.split(begin)[1].split(end)[0]
    begin='\\section{Mechanism Attribution and Budget Sensitivity}';end='\\section{Complete Cost, Scope and Conclusions}'
    assert source.split(begin)[1].split(end)[0]==text.split(begin)[1].split(end)[0]
    (new/'main.tex').write_text(text)
    write(new/'edit_registration.json',dict(prepared_at=datetime.now(timezone.utc).isoformat(),
        parent='submission_narrative_09',parent_main_sha256=sha(old/'main.tex'),parent_pdf_sha256=sha(old/'build/main.pdf'),
        admitted_decision_sha256=sha(root/'admission_decision.json'),
        source_sha256={str(p):sha(p) for p in [Path(__file__).resolve(),root/'admission_decision.json',old/'main.tex',old/'verification.json']},
        main_table_old_rows_preserved=True,method_prior_art_mechanism_controls_unchanged=True,
        new_native_or_STA_calls=0,scope='Add distinct-circuit no-domain-increment result; own-root timing gain is shared native work, not vertical-release benefit.'))
    (new/'EXPERIMENT_IMPACT.md').write_text('''# 投稿10：已核验结果与作者审阅

从投稿09另存，保留原稿。Elliptic完整配对通过后仅更新主表、摘要、实验覆盖、适用性及结论；问题、洞察、方法、prior-art和四档代价机制证据不变。新增两行均为真实完整流程，不是阶段费用拼接。

| 项目 | 已有证据与对应主张 | 剩余实验影响 |
|---|---|---|
| Elliptic不同电路 | 两臂初始SB/CB均0；共同时序改善、无domain增量 | 本批次无待准入角色；未来不同输入只影响新增对应行与范围 |
| BNN完整取舍 | 对称开销24.91%；SB与SB+CB比例分别报告 | 不受Elliptic负增量结果改变 |
| LSTM完整质量 | 整臂配对通过；归档干扰保留 | 无干净完整费用比，不估算无干扰时间 |
| TPU-OS、CLSTM-SB | 前者无domain收益，后者条件性1SB取舍 | 单次费用不作统计加速 |
| 四档跨层代价 | 已完成固定同源组机制对照 | 不主张全部权重或全部输入优势 |
| 历史CLSTM及四臂恢复 | 补充材料 | 不作为主稿统一前置条件 |

稿件独立于研究Goal收束。本文支持的主张是条件性资源—时序取舍及局部机制归因；Elliptic的原生时序收益不得归因于不存在的跨层释放。编译和版式状态以本稿verification.json为准。
''')
    write(new/'REVISION_STATUS.json',dict(status='source_prepared_compile_pending',parent='submission_narrative_09',
        elliptic_pair_admitted=True,main_table_rows=40,method_and_prior_art_unchanged=True,
        four_strength_baseline_completed=True,new_native_or_STA_calls=0))
    print(str(new))


if __name__=='__main__':
    with (D/'critical_scope_runner.lock').open() as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        main()
