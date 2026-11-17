"""Reuse closed LSTM candidate records; no routing or new validation framework."""
import csv
import datetime
import json
import os
import re
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha

OUT=D/'LSTM_existing_tradeoffs_01'
BASE=Path('/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home/confirmation_workspaces/cp1r3_distinct_input_cohort_01/lstm')
assert not OUT.exists();OUT.mkdir()
target=BASE/'domain/flow/resource_flow/repair/round_012/candidate_02'
assert read(target/'completion.json')['passed']
# Keep complete existing payloads without rereading graphs/STA or copying GBs.
# Hardlinks retain the original inode if its old pathname is later removed.
saved=OUT/'retained_candidate_transaction';saved.mkdir();retained=[]
for p in sorted(target.rglob('*')):
    if not p.is_file() or p.suffix=='.lock':continue
    q=saved/p.relative_to(target);q.parent.mkdir(parents=True,exist_ok=True)
    before=p.stat();os.link(p,q,follow_symlinks=True);after=p.stat();copy=q.stat()
    assert (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns)
    assert (copy.st_dev,copy.st_ino,copy.st_size)==(after.st_dev,after.st_ino,after.st_size)
    retained.append(dict(original=str(p),retained=str(q),bytes=copy.st_size,device=copy.st_dev,inode=copy.st_ino))
write(OUT/'retained_payload_inventory.json',dict(files=retained,method='hardlinks_to_closed_immutable_transaction',
    original_data_bytes_rewritten=False,fresh_large_payload_hashing=False,
    qualification='Complete local payload retention, not an independent byte/STA re-audit. No permissions changed on original or linked files. Original manifest/STA/route hashes remain authoritative.'))

rows=[];bindings={};identity=None;roots={}
def small(path):
    assert path.stat().st_size<2*1024**2
    bindings[str(path)]=sha(path);return read(path)

def physical(path):
    # Existing independent audit records end with their resource summary.
    with path.open('rb') as f:
        head=f.read(8192).decode();f.seek(max(0,path.stat().st_size-8192));tail=f.read().decode()
    assert re.search(r'"passed"\s*:\s*true',head) and '"errors": []' in head
    start=tail.rfind('"physical_metrics":');assert start>=0
    result,end=json.JSONDecoder().raw_decode(tail[start+len('"physical_metrics":'):].lstrip())
    return dict(wirelength=result['planar_wirelength_excluding_sb_half_nodes'],
        SB_pairs=result['sb_pairs_used'],CB_sources=result['cb_crossing_output_sources_used'])

for controller in ['native','domain']:
    repair=BASE/controller/'flow/resource_flow/repair';reg=small(repair/'registration.json');roots[controller]=reg['anchor']
    assert reg['anchor']['wirelength']==2388086 and reg['resource_limits']==dict(wirelength=2390475,SB_pairs=509,CB_sources=8316)
    root=reg['anchor'];cap=reg['resource_limits']
    for closed in sorted(repair.glob('round_*/*/completion.json')):
        done=small(closed)
        if not done.get('passed') or 'roles' not in done:continue
        tx=closed.parent;tr=small(tx/'registration.json')
        for name,result in done['roles'].items():
            if result.get('status')!='legal_evaluated':continue
            state=Path(result['evaluation']);ev=small(state/'completion.json');m=small(state/'runs/state/manifest.json')
            decisions=small(tx/(name+'_decisions.json'));ep=decisions['endpoint_vector']['comparison']
            assert ev['passed'] and all(ev['checks'].values()) and m['metrics']['native_full_check_passed']
            cpd=ev['full_precision_cpd_s']
            assert cpd==result['cpd_s']==ep['cpd_after_s']
            with (state/'endpoint_vector.json').open() as f:header=f.read(512)
            own_cpd=float(re.search(r'"cpd_s"\s*:\s*([\deE+.\-]+)',header).group(1));assert own_cpd==cpd
            resources=physical(state/'runs/state/independent_audit.json');assert resources==result['resources']
            assert m['metrics']['wirelength']==resources['wirelength']
            cmd=m['command'];inputs={k:m['shared_inputs'][str(Path(cmd[i]))]['sha256'] for k,i in [('architecture',1),('circuit',2),('graph',cmd.index('--read_rr_graph')+1)]}
            inputs.update({k:m['outputs'][n]['sha256'] for k,n in [('packing','packed.net'),('placement','placed.place')]})
            if identity is None:identity=inputs
            assert inputs==identity,'Different declared physical input'
            policy=decisions['resources_under_timing'];over=resources['wirelength']-cap['wirelength']
            rows.append(dict(id=controller+'/'+str(tx.relative_to(repair))+'/'+name,
                controller=controller,search='guided' if tr['roles'][name].get('crossing_reuse_enabled') else 'native',
                transaction=str(tx),evaluation=str(state),route_legal_existing_checks=True,
                CPD_ns=cpd*1e9,CPD_s=cpd,**resources,wire_delta_from_root=resources['wirelength']-root['wirelength'],
                required_wire_increment_percent=(resources['wirelength']/root['wirelength']-1)*100,
                wire_over_registered_cap=max(0,over),inside_original_all_budgets=(cpd<=root['CPD_s'] and all(resources[k]<=cap[k] for k in cap)),
                resource_policy_accepted=policy['accepted'],resource_policy_reason=policy['reason'],
                endpoint_policy_accepted=decisions['endpoint_vector']['accepted'],
                setup_improved_vs_own_source=ep['setup_improved'],setup_regressed_vs_own_source=ep['setup_regressed'],
                hold_violation_regressions_vs_own_source=ep['hold_violation_regressions'],
                setup_components=ep['setup_components'],hold_components=ep['hold_components'],
                full_endpoint_count=ev['endpoints'],endpoint_reference='own immediate source, not a different SB state or common root',
                route_sha256=m['outputs']['routed.route']['sha256'],timing_echo_sha256=ev['timing_echo_sha256'],
                complete_transaction_seconds=done['complete_orchestrator_seconds'],
                original_role_quality_admitted=False))

assert roots['native']==roots['domain']
focus=[r for r in rows if r['evaluation']==str(target/'reuse_on_evaluation')];assert len(focus)==1
focus=focus[0];assert focus['SB_pairs']==419 and focus['wire_over_registered_cap']==402 and not focus['resource_policy_accepted']
same=[r for r in rows if r['CPD_s']==roots['domain']['CPD_s'] and r['CB_sources']==8316]
front=[]
for r in same:
    r['wire_SB_projected_nondominated']=not any(s['wirelength']<=r['wirelength'] and s['SB_pairs']<=r['SB_pairs'] and (s['wirelength']<r['wirelength'] or s['SB_pairs']<r['SB_pairs']) for s in same)
    if r['wire_SB_projected_nondominated']:front.append(r)
write(OUT/'candidate_rows.json',rows)
with (OUT/'candidate_rows.csv').open('w',newline='') as f:
    fields=sorted(set().union(*(r.keys() for r in rows)));w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
write(OUT/'focused_419_SB_candidate.json',dict(**focus,retained_full_transaction=str(saved),
    route_legality='Existing candidate FULL/fresh-STA and independent physical/capacity checks passed.',
    budget_acceptability='Original0.1% wire envelope exceeded by402; original rejection preserved.',
    tradeoff_value='Observed legal lower-SB/higher-wire working point outside the fixed policy envelope. No broader-budget full experiment was run.',
    full_role_and_supplement_raw_admission='Pending or original failed. This analysis does not admit whole-role benefit.'))

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig,axes=plt.subplots(1,2,figsize=(10,4),layout='constrained')
for ax in axes:
    ax.axvspan(-100,2389,color='#edf5ec',zorder=0)
    ax.axvline(2389,color='black',linestyle='--',linewidth=1,label='registered0.1% cap (+2389)')
    for search,color,marker in [('guided','#276ca4','s'),('native','#bd671a','o')]:
        rr=[r for r in rows if r['search']==search]
        ax.scatter([r['wire_delta_from_root'] for r in rr],[r['SB_pairs'] for r in rr],s=28,
            facecolors=color,edgecolors='white',linewidths=.4,marker=marker,label=search+' candidates')
    xy=sorted(set((r['wire_delta_from_root'],r['SB_pairs']) for r in front))
    ax.plot([x for x,y in xy],[y for x,y in xy],color='#555555',linewidth=.8,zorder=1,label='W/SB projection (same CPD/CB)')
    ax.set_xlabel('Wire increment from fixed root');ax.set_ylabel('SB occupancy');ax.grid(alpha=.2)
axes[0].scatter([0],[509],color='black',marker='*',s=65,label='fixed root')
axes[0].set_title('All closed legal candidate observations')
axes[0].set_xlim(min(-30,min(r['wire_delta_from_root'] for r in rows)-50),max(r['wire_delta_from_root'] for r in rows)+80)
axes[1].set_xlim(2100,2950);axes[1].set_ylim(416,437);axes[1].set_title('Original budget boundary (zoom)')
axes[1].annotate('419 SB / +402 over cap',xy=(focus['wire_delta_from_root'],419),xytext=(2440,417),fontsize=8,arrowprops=dict(arrowstyle='->',lw=.7))
native=[r for r in rows if r['evaluation']==str(target/'reuse_off_evaluation')][0]
axes[1].annotate('native425 SB, accepted',xy=(native['wire_delta_from_root'],425),xytext=(2120,432),fontsize=8,arrowprops=dict(arrowstyle='->',lw=.7))
axes[0].legend(fontsize=7,loc='best')
fig.savefig(OUT/'wire_SB_working_points.pdf');fig.savefig(OUT/'wire_SB_working_points.png',dpi=170);plt.close(fig)
write(OUT/'completion.json',dict(passed=True,observed_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    observed_closed_legal_candidates=len(rows),native_candidates=sum(r['search']=='native' for r in rows),
    guided_candidates=sum(r['search']=='guided' for r in rows),focus_id=focus['id'],
    root=roots['domain'],registered_wire_cap=2390475,integer_rounding='ceil(root_wire*1.001); mathematical0.1% boundary2390474.086',
    same_declared_physical_identity=identity,focused_candidate_full_payloads_retained=True,
    source_sha256=bindings,new_native_or_STA_calls=0,new_acceptance_rules=False,new_verification_framework=False,
    wider_budget_complete_experiment=False,whole_role_quality_admitted=False,
    qualification='Descriptive reuse of completed candidate checks/metrics. Original rejections preserved. Endpoints are compared to each own source; projected W/SB nondominance is not endpoint/full multiobjective dominance. Original whole-role failures and pending supplemental/raw admission remain. Large payloads retained by hardlinks without fresh heavy rehash or STA.'))
lines=['# LSTM已有合法候选的线长—SB取舍','',
    f'419 SB候选自己的完整CPD为{focus["CPD_ns"]:.12f}ns，资源为{focus["wirelength"]}/419/8316；setup相对自己的直接源为{focus["setup_improved_vs_own_source"]}改善/{focus["setup_regressed_vs_own_source"]}退化，hold违例增加{focus["hold_violation_regressions_vs_own_source"]}。这些值来自该候选自己的FULL/STA、物理汇总和端点决策记录，不借用426 SB前态。',
    '', '路由合法性：现有候选FULL、新STA及独立物理/容量检查通过。预算接受性：线长2390877超过原上限2390475共402，原判定保持策略拒绝。多目标取舍价值：它是已经观察到的合法低SB/高线长工作点；不等于路由失败，也不等于运行了更宽预算完整控制器。',
    '', f'复用{len(rows)}条已经闭合的合法候选观察，包含native控制器、domain控制器的guided候选及native回退；原始记录全部保留。所有CPD来自各自评价完成回执，SB/CB/线长与各自已有物理汇总一致。输入归属复用现有manifest的网表/图/架构/packing/placement声明。完整角色质量仍等待原检查、补充与raw准入，本次不重新执行它们。',
    '', '| 工作点 | 线长 | SB | CB | CPD(ns) | 相对自己的源setup改善/退化 | 原资源规则 |', '|---|---:|---:|---:|---:|---:|---|']
for r in [r for r in rows if r['transaction']==str(target)]:
    lines.append(f'| {r["search"]} | {r["wirelength"]} | {r["SB_pairs"]} | {r["CB_sources"]} | {r["CPD_ns"]:.12f} | {r["setup_improved_vs_own_source"]}/{r["setup_regressed_vs_own_source"]} | {"接受" if r["resource_policy_accepted"] else "策略拒绝"} |')
lines+=['','图中的线是相同CPD/CB子集的W/SB二维投影前沿，不比较完整端点向量，不作为更宽预算控制器结果。记录的“所需线长增幅”仅描述已有点所在位置，不重新执行预算策略。图外全部明细见candidate_rows.csv。','',
    '完整目标事务通过本地硬链接保留，包括原生请求/轨迹、两臂候选评价、实际路由、完整端点、时序echo、物理审计和费用。未重写原文件、未改权限、未重跑查询；retained_payload_inventory.json给出原路径、保留路径及inode。大文件保留不当作新的字节/STA审计。','',
    '正文与已登记基线保持原样。本结果用于理解当前预算边界，后续重点继续LSTM/DLA完整配对、已登记代价对照和有证据支持的正文更新。']
(OUT/'TRADEOFFS.md').write_text('\n'.join(lines)+'\n')
print(dict(rows=len(rows),focus_CPD_ns=focus['CPD_ns'],focus_setup=[focus['setup_improved_vs_own_source'],focus['setup_regressed_vs_own_source']],retained_files=len(retained),retained_apparent_bytes=sum(f['bytes'] for f in retained)))
