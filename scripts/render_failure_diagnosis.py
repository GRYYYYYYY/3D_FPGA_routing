#!/usr/bin/env python3
"""Render checked diagnostic evidence into portable figures and a local report."""
import argparse
from collections import Counter
import html
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'results/failure_diagnosis'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native-primary',action='store_true')
    args=parser.parse_args()
    suffix='_native' if args.native_primary else ''
    data=json.loads((BASE/('analysis'+suffix+'.json')).read_text())
    validation=json.loads((BASE/('validation'+suffix+'.json')).read_text())
    if data['provisional'] or data['problems'] or validation['stage']!='validated':
        raise RuntimeError('Final report requires completed validation')
    rows=data['rows']; figures=BASE/'figures';figures.mkdir(exist_ok=True)
    def save(fig,name):
        for ext in ['png','svg']:fig.savefig(figures/f'{name}.{ext}',dpi=180,bbox_inches='tight')
        plt.close(fig)
    cases=sorted(set(r['circuit'] for r in rows))
    names={'a0':'A0','a0_prune':'A0 prune','a3':'A3','a4_subtree':'A4 subtree','flute_soft':'FLUTE soft'}
    colors={'a0':'#2563eb','a0_prune':'#64748b','a3':'#16a34a','a4_subtree':'#dc2626','flute_soft':'#9333ea'}
    fig,axes=plt.subplots(5,3,figsize=(15,18),layout='constrained')
    for ax,case in zip(axes.flat,cases):
        for variant in names:
            candidates=[r for r in rows if r['circuit']==case and r['variant']==variant and r['width']==100]
            if not candidates:continue
            trial=max(candidates,key=lambda r:r['budget'])
            history=json.loads((Path(trial['output'])/'iterations.json').read_text())
            ax.plot([i['iteration'] for i in history],[i['overused_resources'] for i in history],
                    label=names[variant],color=colors[variant],linewidth=1.2)
        ax.axvline(50,color='#777',linestyle='--',linewidth=.8)
        ax.set(title=case,xlabel='Routing iteration',ylabel='Overused resources')
        ax.set_yscale('symlog',linthresh=1);ax.set_ylim(bottom=0);ax.set_xlim(left=0)
        ax.grid(alpha=.2);ax.legend(fontsize=7)
    for ax in list(axes.flat)[len(cases):]:ax.set_visible(False)
    fig.suptitle('W=100, predictor off; native default congestion scheduling' if args.native_primary else
                 'W=100, predictor off; high-effort congestion mode after iteration 50',fontsize=15)
    save(fig,'convergence')
    width_keys=sorted(set((r['circuit'],r['variant']) for r in rows if r['width']!=100))
    matrix=np.full((len(width_keys),4),-1.);labels={}
    for i,(case,variant) in enumerate(width_keys):
        for k,width in enumerate([100,120,140,160]):
            trial=next((r for r in rows if r['circuit']==case and r['variant']==variant and
                        r['width']==width and r['budget']==200),None)
            if trial:
                matrix[i,k]=1 if trial['valid_solution'] else 2 if trial['status']=='timeout' else 0
                labels[i,k]=str(trial['metrics']['iterations']) if trial['valid_solution'] else 'TIME' if trial['status']=='timeout' else 'FAIL'
    fig,ax=plt.subplots(figsize=(9,max(8,len(width_keys)*.30)),layout='constrained')
    ax.imshow(matrix,aspect='auto',cmap=ListedColormap(['#e5e7eb','#fdba74','#86efac','#c4b5fd']),vmin=-1,vmax=2)
    ax.set_xticks(range(4),['W=100','W=120','W=140','W=160'])
    ax.set_yticks(range(len(width_keys)),[f'{c} / {names.get(v,v)}' for c,v in width_keys],fontsize=8)
    for (i,k),value in labels.items():ax.text(k,i,value,ha='center',va='center',fontsize=8)
    ax.set_title('Same packing and placement; predictor off / 200 iterations\nGreen: audited legal (iterations); orange: failed; purple: time limit')
    save(fig,'width_scan')
    counts=data['original_failure_classifications']
    summaries=''.join(f'<tr><td>{html.escape(s["stage"])}</td><td>{s["runs"]}</td><td>{s["native_success"]}</td><td>{s["audited_success"]}</td></tr>' for s in data['summaries'])
    rows_html=[]
    status_labels={'failed':'达到迭代上限仍失败','timeout':'时间截断（未完成迭代预算）'}
    for r in sorted(rows,key=lambda r:(r['circuit'],r['variant'],r['width'],r['budget'])):
        relative=Path(r['output']).relative_to(BASE)
        cells=[r['circuit'],r['variant'],r['width'],r['budget'],
               '成功且审计通过' if r['valid_solution'] else status_labels.get(r['status'],r['status']),r['metrics'].get('last_iteration',''),
               r['metrics'].get('last_overused_resources','')]
        rows_html.append('<tr>'+''.join(f'<td>{html.escape(str(v))}</td>' for v in cells)+
                         f'<td><a href="{relative}/vpr.log">日志</a> · <a href="{relative}/manifest.json">记录</a></td></tr>')
    specific=[]
    for case,variant in [('clstm_like.small','a4_subtree'),('robot_rl','flute_soft')]:
        c=next(x for x in data['classifications'] if x['circuit']==case and x['variant']==variant)
        specific.append(f'<li><code>{case} / {variant}</code>：{c["classification"]}，成功轮次 {c["success_iteration"]}。</li>')
    auxiliary=data.get('auxiliary_high_effort',[])
    auxiliary_status=Counter(r['status'] for r in auxiliary)
    aux_rows=[]
    for row in auxiliary:
        aux_rows.append('<tr>'+''.join(f'<td>{html.escape(str(v))}</td>' for v in
            [row['circuit'],row['variant'],row['status'],row['metrics'].get('last_iteration'),
             row['metrics'].get('last_overused_resources'),'审计通过' if row['valid_solution'] else '—'])+'</tr>')
    auxiliary_html=('''<section><h2>高强度搜索辅助对照与协议修订</h2><p>初始设置在第 50 轮后启动高强度拥塞模式，额外扩大搜索范围。观察到它显著增加部分大电路每轮耗时后，主实验修订为保留 VPR 原生默认模式，仅改变预测器和迭代上限。修订前完成的结果全部保留；中止的运行不是算法布线失败，未启动的运行不计入次数。</p>'''+
        f'<p>辅助运行状态：{html.escape(str(dict(auxiliary_status)))}。其中 {sum(r["valid_solution"] for r in auxiliary)} 次成功经过独立审计。该组未完整覆盖所有变体，不计算整体成功率或总体性能优势。</p>'+
        '<p><a href="protocol_amendment.json">修订及中止记录</a> · <a href="schedule_comparison.json">两个特定退化案例的搜索模式对照</a> · <a href="schedule_comparison_baselines.json">共同难例基线的搜索模式对照</a></p>'+
        '<div class="scroll"><table><tr><th>电路</th><th>变体</th><th>状态</th><th>最后轮次</th><th>剩余过用</th><th>检查</th></tr>'+''.join(aux_rows)+'</table></div></section>') if auxiliary else ''
    mode_note=('主实验保留 VPR 原生默认拥塞模式调度：阈值比例为 1.0，高强度模式在迭代预算结束前不参与搜索。额外高强度模式结果单独列出。' if args.native_primary else
               '高强度拥塞阶段固定在第 50 轮后，延长运行可能扩大搜索包围盒并集中处理冲突，不能解释为在原常规搜索模式下单纯多做几轮。')
    capacity_rows=[]
    for case,proof in sorted(data.get('capacity_certificates',{}).items()):
        certificate=json.loads(Path(proof['evidence']).read_text())['certificates'][proof['certificate_index']]
        links=' · '.join(f'<a href="{Path(proof[k]).relative_to(BASE)}">{label}</a>'
                         for k,label in [('evidence','容量割证书'),('verification','独立复核')])
        capacity_rows.append('<tr>'+''.join(f'<td>{html.escape(str(v))}</td>' for v in
            [case,certificate['coordinate'],proof['demand'],proof['capacity'],proof['demand']-proof['capacity']])+
            f'<td>{links}</td></tr>')
    checkpoint=data.get('capacity_checkpoint')
    checkpoint_html=('检查点记录：'+html.escape(str(checkpoint['statuses']))+
                     '。中止尝试和未启动任务均不计为算法失败；实际日志、退出码和旧队列另行保留。'
                     '<a href="native_500_checkpoint_attempts.json">检查点明细</a>。') if checkpoint else ''
    capacity_html=('''<section><h2>已证明的固定实例容量不足</h2>
<p>对给定布局和 RRG，下面的固定终端集合必须穿过指定资源边界。不同网络的需求数大于该边界的总容量，因此任何路由算法都无法同时满足这些需求。独立验证器重新枚举所有跨界有向边、容量和网络终端见证。</p>
<div class="scroll"><table><tr><th>电路</th><th>示例位置 (x,y,层)</th><th>不同网络需求</th><th>出口总容量</th><th>缺口</th><th>证据</th></tr>'''+''.join(capacity_rows)+'''</table></div>
<p>这些证书定位到 DSP 输出的局部引脚出口。attention_layer 的整块输出总量尚未超限，但其中一组固定输出可访问的出口不足；只看整块总容量会遗漏这一约束。重叠证书的缺口不能相加。证明仅适用于记录的固定网表、布局、终端映射和图，未找到证书也不等于已证明可布线。</p>
<p>全部 200 轮对照完成后，44 个已获证书的变体不再重复延长至 500 轮，仍全部纳入原 132 次失败的归因；这 4 个电路继续参加 A0/A3/A4 的宽度扫描。'''+checkpoint_html+'</p></section>') if capacity_rows else ''
    width_lookup={(r['circuit'],r['variant'],r['width']):r for r in rows if r['budget']==200}
    a0_width_rows=[]
    for case in cases:
        cells=[case]
        for width in [100,120,140,160]:
            trial=width_lookup.get((case,'a0',width))
            if trial is None:value='未执行'
            elif trial['valid_solution']:value=f'成功，第 {trial["metrics"]["iterations"]} 轮'
            elif trial['status']=='timeout':value=f'时间截断，第 {trial["metrics"].get("last_iteration")} 轮'
            else:value=f'失败，剩余 {trial["metrics"].get("last_overused_resources")} 个过用资源'
            cells.append(value)
        a0_width_rows.append('<tr>'+''.join(f'<td>{html.escape(v)}</td>' for v in cells)+'</tr>')
    contrasts=[]
    for width in [100,120,140,160]:
        baseline_only=[];variant_only=[];censored=[]
        for case,variant in width_keys:
            if variant=='a0':continue
            baseline=width_lookup[case,'a0',width];trial=width_lookup[case,variant,width]
            pair=f'{case}/{names.get(variant,variant)}'
            if baseline['status']=='timeout' or trial['status']=='timeout':censored.append(pair)
            elif baseline['valid_solution'] and not trial['valid_solution']:baseline_only.append(pair)
            elif trial['valid_solution'] and not baseline['valid_solution']:variant_only.append(pair)
        contrasts.append(f'<li>W={width}：A0 成功而变体失败 {len(baseline_only)} 组；变体成功而 A0 失败 {len(variant_only)} 组；含时间截断 {len(censored)} 组。'+
                         (f'<br>A0 单侧成功：{html.escape("、".join(baseline_only))}。' if baseline_only else '')+
                         (f'<br>变体单侧成功：{html.escape("、".join(variant_only))}。' if variant_only else '')+'</li>')
    baseline_width_html='<div class="scroll"><table><tr><th>A0 电路／布局</th><th>W=100</th><th>W=120</th><th>W=140</th><th>W=160</th></tr>'+''.join(a0_width_rows)+'</table></div>'
    protocol_name='failure_diagnosis_native.json' if args.native_primary else 'failure_diagnosis.json'
    report=f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>原生三维 FPGA 布线失败诊断</title><style>
body{{font:16px/1.65 system-ui,sans-serif;color:#172334;background:#f7f9fc;margin:0}}main{{max-width:1200px;margin:auto;padding:36px 24px}}
h1,h2{{line-height:1.3}}section{{background:white;border:1px solid #dce3ed;border-radius:12px;padding:24px;margin:20px 0}}
table{{border-collapse:collapse;width:100%;font-size:14px}}th,td{{padding:8px 12px;border-bottom:1px solid #e2e8f0;text-align:left}}
th{{background:#eef3fa}}img{{max-width:100%;height:auto}}a{{color:#155ac2}}code{{background:#f1f5f9;padding:2px 5px}}
.scroll{{overflow:auto}}input{{padding:10px;width:min(500px,90%);margin-bottom:15px}}.note{{color:#475569}}
</style><main><h1>原生三维 FPGA 布线失败诊断</h1><p>生成于 {data['utc']}。新增诊断数据独立保存，原 769 次实验及其 132 次失败记录保持不变。</p>
<section><h2>原 132 次失败的归因结果</h2><ul>
<li>只关闭提前终止，在 50 轮内恢复：<b>{counts.get('predictor_only',0)}</b> 次。</li>
<li>在相同初始搜索轨迹上延长至 200 轮恢复：<b>{counts.get('continued_search_51_200',0)}</b> 次。</li>
<li>继续延长至 500 轮恢复：<b>{counts.get('continued_search_201_500',0)}</b> 次。</li>
<li>已由独立复核的容量割证书证明固定实例不可行：<b>{counts.get('certified_resource_infeasible',0)}</b> 次；保留完整 200 轮实测，不再重复延长至 500 轮。</li>
<li>500 轮仍未解决：<b>{counts.get('unresolved_at_500',0)}</b> 次。</li>
<li>受进程时间上限截断、不能视为完成 500 轮：<b>{counts.get('censored_by_timeout',0)}</b> 次。</li></ul>
<ul>{''.join(specific)}</ul>
<p>主实验纳入 {len(rows)} 次正式布线运行，{sum(r['valid_solution'] for r in rows)} 次同时通过原生 FULL 检查与独立有向图／容量审计。共同输入、逐项参数和 {len(data['prefix_checks'])} 组搜索前缀核验通过；高强度辅助对照及中止尝试另列。</p>
<p class="note">“恢复”指当前设置下找到合法解；有限次迭代仍失败不能证明图不可布线。{mode_note} 该实验未修改算法实现。</p></section>
<section><h2>实验设置与检查</h2><p>固定输入实验保留每个变体原有二进制、参数、网表、布局和 RRG。宽度扫描固定架构、网表和布局，每个宽度重建一张图供对照算法共享。扫描涉及 A0/A3/A4 与两个特定退化案例的必要对照；未将它推广为全部变体的最小通道宽度。</p>
<p>宽度改变还可能改变连通关系、开关扇入与时延，不能将结果直接解释为仅增加了某一类资源。独立宽度任务与尚在运行的 W=100 任务共享并发上限，既有 VPR 进程保持运行，算法参数和迭代预算均不变。并发运行时间不用于性能加速比。各架构的物理模型限制沿用原研究报告。</p>
<div class="scroll"><table><tr><th>阶段</th><th>运行数</th><th>原生成功</th><th>独立审计通过</th></tr>{summaries}</table></div>
<p><a href="../../configs/{protocol_name}">冻结协议</a> · <a href="analysis{suffix}.json">分析 JSON</a> · <a href="analysis{suffix}.csv">完整 CSV</a> · <a href="validation{suffix}.json">验证记录</a> · <a href="original_regression_conflicts.json">原始两个退化案例的冲突网络</a></p></section>
{capacity_html}
<section><h2>收敛轨迹</h2><p>纵轴在零附近线性、其余对数。虚线为原 50 轮边界；曲线选择该变体最大预算的运行，遇到时间截断时只显示实际观测到的轮次。</p><a href="figures/convergence.svg"><img src="figures/convergence.png" alt="各电路的拥塞收敛轨迹"></a></section>
<section><h2>独立通道宽度扫描</h2><p>所有单元统一使用关闭预测器、200 轮预算。绿色数字为成功轮次，橙色表示用完预算仍失败，紫色表示在迭代预算前达到进程时间上限；每一个成功都经过审计。</p>{baseline_width_html}
<p>同一宽度、同一 200 轮预算下的配对结果如下。单侧成功证明该固定实例存在合法解，同时显示另一方在此预算下的搜索局限；它不证明对所有预算或工作负载的算法优劣。</p><ul>{''.join(contrasts)}</ul>
<p>对 <code>dla_like.medium/W=120</code> 的额外局部容量检查未找到不可行证书。因此，即使多个算法均在 200 轮后仍失败，也不能据此证明该实例无解。<a href="width_terminal_cut_check.json">探索性检查记录</a>。</p>
<a href="figures/width_scan.svg"><img src="figures/width_scan.png" alt="固定布局的通道宽度扫描"></a></section>
{auxiliary_html}
<section><h2>全部诊断运行</h2><input id="filter" aria-label="筛选运行" placeholder="输入电路、方法或状态筛选"><div class="scroll"><table id="runs"><thead><tr><th>电路／布局</th><th>方法</th><th>W</th><th>预算</th><th>状态</th><th>最后轮次</th><th>剩余过用</th><th>证据</th></tr></thead><tbody>{''.join(rows_html)}</tbody></table></div></section>
</main><script>document.getElementById('filter').addEventListener('input',e=>{{const q=e.target.value.toLowerCase();document.querySelectorAll('#runs tbody tr').forEach(r=>r.hidden=!r.textContent.toLowerCase().includes(q));}});</script></html>'''
    (BASE/'report.html').write_text(report)
    print(BASE/'report.html')


if __name__=='__main__':main()
