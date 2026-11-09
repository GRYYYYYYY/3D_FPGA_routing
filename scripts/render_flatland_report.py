#!/usr/bin/env python3
"""Render the completed experiment's factual report; never invent missing data."""
import argparse
from collections import Counter
from html import escape
from pathlib import Path
from statistics import median

from flatland_benchmark import BASE,read
from lazagna_common import ROOT,sha256,utc,write_json

LABELS=dict(sb='SB',cb_o='CB-O',hybrid_o='Hybrid-O',matched_2d='匹配容量 2D')


def e(value):return escape(str(value))
def number(value,digits=3):return '—' if value is None else f'{value:.{digits}f}'
def percent(value):return '—' if value is None else f'{value:+.2f}%'
def cohort(data):return f"{len(data['complete_circuits'])}/{data['registered_circuits']}"


def table(headers,rows):
    return '<div class="table"><table><thead><tr>'+''.join('<th>'+e(h)+'</th>' for h in headers)+'</tr></thead><tbody>'+''.join(
        '<tr>'+''.join('<td>'+e(v)+'</td>' for v in row)+'</tr>' for row in rows)+'</tbody></table></div>'


def figure(name,caption):
    return '<figure><img src="figures/'+name+'.svg" alt="'+e(caption)+'"><figcaption>'+e(caption)+\
        ' <a href="figures/'+name+'.pdf">PDF</a></figcaption></figure>'


def document(data,physical):
    q,t,p,selected,observations=(data[k] for k in ['evaluation','serial','protocol','selection','observations'])
    sections=['<h1>三维 FPGA：布局、布线与架构探索受控实验</h1>',
        '<p>生成时间：'+e(utc())+'。本报告汇总已结束的登记实验；最终研究验收与证据封存另见完成记录。</p>',
        '<p>R1 是本项目对固定官方 VTR 9 开发提交的路由修改；P0 为官方布局，P1 为集成论文布局与 TritonPart、保留字面参数 0.03 的流程。'
        '每个布线对照共享图、打包网表及布局坐标。P1 的实际打包语义必须与共同输入匹配。</p>',
        '<p>R1 根据同层可达性构建跨层候选，用几何或有预算的开关时延查询评估候选，结合关键性筛选和共享/拆分代理规划生成软引导。'
        '最终路径仍由时序与拥塞驱动路由器完成。该有限候选代理模型不等于全图 Steiner 最优解；当前范围限于两层和 clustered routing。</p>']
    sections += ['<h2>实验范围与三套基线</h2>',table(['对象','身份','比较口径'],[
        ['B1','LaZagna 论文发表结果，VTR 8.1','保留作者二维分母；缺少共同绝对分母，直接 R1/B1 比率不计算'],
        ['B2','LaZagna 后续移植 VTR 9 代码的作者分支 5abd3aca','与 A0、R1 使用同一物理图、打包网表和布局；属于工具链/路由器比较'],
        ['B3 / A0','官方 0b912334fdd83bb754b302146ac0d1ec9edc9a0e','同输入的原生路由对照'],
        ['R1off','与 R1 相同的构建，关闭引导','串行子集控制构建差异；成功配对要求与 A0 的完整路径一致']]),
        '<p>B2 的版本元数据仍标为 8.1.0-dev，不能仅凭该字符串判断迁移状态。B1 论文表 IV 的 SB 100% / 66% / 33% '
        'CPD/作者二维 CPD 分别为 0.821 / 0.819 / 0.809，不能与本实验改善百分比相减。'
        '来源与适用条件见<a href="../../docs/三基线对比_2026-10-27.md">历史三基线报告</a>。</p>',
        table(['项目','登记范围'],[
            ['训练','6 电路，seed 11；每种架构 4 个变体 × 8 组参数，576 条 R1 + 18 条 A0'],
            ['主评估','14 电路，seeds 21/23/25；3 架构 × 2 布局 × A0/R1/B2，另有匹配容量 2D'],
            ['消融','14 电路，seed 21，P1；固定配置 0 与各变体同等预算调参'],
            ['宽度敏感性','W300：spmv、bnn 为训练用例；robot_rl、conv_layer_hls 为测试用例；参数从 W100 转移'],
            ['串行计时','spmv / robot_rl，3 架构 × 2 布局，每组 3 次；轮换 A0/R1/B2 顺序并增加 R1off'],
            ['测量执行约束','单 VPR worker，200 轮，关闭失败预测器；路由 1800 秒、布局 3600 秒；路由/布局测量进程虚拟地址空间上限 64 GiB'],
            ['已解析登记项',f"{q['planned_cases']} 个案例、{q['planned_roles']} 个角色；{q['unique_attempted_route_runs']} 个独立路由运行"]]),
        '<p>本次采用新划分与新种子；这些电路家族曾用于历史研究，不能称为此前完全未观察过的数据。'
        '相同输入及参数的角色可以引用同一运行，其复用不构成独立重复。</p>']
    rows=[];maxima=[];modern=[];components=[]
    for family,result in q['heldout'].items():
        for flow in ['p0','p1']:
            d=result[flow]['routing_dual'];a=d['vs_3d'];b=d['vs_2d'];m=d['maximum_vs_3d_same_sample']
            rows.append([LABELS[family],flow.upper(),percent(a['geomean_improvement_percent'])+' ('+percent(b['geomean_improvement_percent'])+')',
                cohort(a),f"{a['paired_legal_samples']}/{a['registered_samples']}",
                f"{a['improved_samples']} / {a['tied_samples']} / {a['regressed_samples']}",
                percent(result[flow]['planar_wirelength']['geomean_improvement_percent'])+' ['+cohort(result[flow]['planar_wirelength'])+']'])
            if m:maxima.append([LABELS[family],flow.upper(),m['circuit'],m['seed'],number(m['cpd_ns']),
                percent(m['improvement_vs_3d_percent'])+' ('+percent(m['improvement_vs_2d_percent'])+')'])
            for label,key in [('R1/B2','modern_lazagna_paired'),('A0/B2','official_vs_modern')]:
                v=result[flow][key];modern.append([LABELS[family],flow.upper(),label,number(v['geomean_ratio'],6),
                    percent(v['geomean_improvement_percent']),cohort(v),f"{v['paired_legal_samples']}/{v['registered_samples']}"])
        placement=result['placement_only'];combined=result['combined_flow_dual'];interaction=q['factorial_interactions'][family]
        components.append([LABELS[family],percent(placement['geomean_improvement_percent']),cohort(placement),
            percent(combined['vs_3d']['geomean_improvement_percent'])+' ('+percent(combined['vs_2d']['geomean_improvement_percent'])+')',
            cohort(combined['vs_3d']),number(interaction['geomean_interaction_ratio'],6),len(interaction['complete_common_circuits'])])
    sections += ['<h2>固定布局下的布线收益</h2>',
        '<p>改善为 100×(1−R1/基线)，正值表示 CPD 降低。括号内采用匹配容量 2D；两组几何均值使用完全相同的完整电路集合。'
        '每个电路先平均三个种子的 CPD，再对电路比值取几何均值。改善/相同/退化计数使用所有配对合法种子样本。</p>',
        table(['架构','布局','CPD 改善：3D (2D)','完整电路','合法配对样本','改善/相同/退化','平面线长改善（自身配对集）'],rows),
        figure('routing_effect','点为电路种子均值的比值，菱形为共同完整电路的几何均值。'),
        '<h3>最大单样本改善</h3><p>在 3D 与 2D 均有合法配对的样本中选择最大 3D 改善。以下每行的两个数字绑定同一电路和种子；最大值不能代替整体表现。</p>',
        table(['架构','布局','电路','seed','R1 CPD ns','改善：3D (2D)'],maxima),
        '<h3>与后续 LaZagna 的配对结果</h3><p>同时展示 A0/B2，帮助区分本项目修改与工具链差异。</p>',
        table(['架构','布局','比较','CPD 几何均值比','改善','完整电路','合法配对样本'],modern),
        '<h2>布局贡献、组合收益与架构排序</h2>',
        table(['架构','仅布局 P1A0/P0A0 改善','完整电路','组合 P1R1/P0A0 改善 (相对2D)','完整电路','乘性交互比','交互完整电路'],components),
        '<p>交互比为 (P1R1/P1A0)/(P0R1/P0A0)，小于 1 表示该共同样本中 P1 下相对布线收益更强；不自动构成显著性结论。'
        '仅布局、组合、交互各自使用的共同集合可能不同，集合详见统计 JSON。</p>']
    ranks=q['architecture_rankings'];rank_rows=[]
    for flow,panel in ranks['by_flow'].items():
        order=' < '.join(' = '.join(LABELS[f] for f in group) for group in panel['rank_groups'])
        rank_rows.append([flow,order,*[number(panel['absolute_geomean_cpd_ns'][f]) for f in ['sb','cb_o','hybrid_o']]])
    sections += ['<p>架构排序统一使用 '+str(len(ranks['complete_common_circuits']))+'/14 个共同完整电路。'
        '比较依据是最终绝对 CPD 或共同 2D 归一化值；各架构相对自身的改善百分比不用于排序。</p>',
        table(['流程','CPD 从小到大','SB ns','CB-O ns','Hybrid-O ns'],rank_rows),
        figure('architecture_ordering','同一共同样本上的整体排序与逐种子结果；无共同集合时明确留空。'),
        '<p>检测到的严格成对排序反转条目数：'+str(len(ranks['strict_pairwise_reversals']))+'。'
        '该计数包含不同流程比较，不等于独立实验数量；具体架构对与种子稳定性见统计 JSON。</p>']
    selected_rows=[];ablation_rows=[]
    for f,choice in selected['selections'].items():
        selected_rows.append([LABELS[f],choice['R1']['variant'],choice['R1']['config'],
            ', '.join(v+':'+str(x['selected']) for v,x in choice['per_variant'].items())])
        for kind,group in q['ablations'][f]['joint_cohort'].items():
            for v,x in group.items():ablation_rows.append([LABELS[f],kind,v,percent(x['geomean_improvement_percent']),cohort(x)])
    sections += ['<h2>超参数探索与消融</h2>',
        '<p>参数仅依据训练集合选择：先最大化合法案例数，再在并列候选的共同成功集合比较 CPD，最后按路由耗时及固定顺序打破平局。'
        '八组设计点同时改变多个参数，可用于预算受限的搜索，不用于宣称某个单参数的因果效应。</p>',
        table(['架构','选中 R1 变体','配置号','各变体配置号'],selected_rows),figure('training_search','训练探索：共同样本 CPD 比值与合法数；不属于测试集结论。'),
        table(['架构','参数策略','变体','相对 P1 A0 的 CPD 改善','共同完整电路'],ablation_rows),
        figure('ablations','固定参数与同等调参预算消融；每种架构八个柱使用相同电路集合。')]
    parameter_rows=[]
    for item in p['tuning']['variants']['delay_critical']:
        env=item['environment'];parameter_rows.append([item['id'],*[env[k] for k in [
            'VPR_H3D_CANDIDATES','VPR_H3D_MISS_WEIGHT','VPR_H3D_OPENING_WEIGHT','VPR_H3D_DELAY_BUDGET','VPR_H3D_MIN_CRITICALITY']]])
    sections += [table(['配置号','候选 K','偏离权重','开通权重','延迟查询预算','关键性阈值'],parameter_rows),
        '<p>上表为 D+C 的参数向量；G/C 关闭延迟候选评分，G/D 的关键性阈值固定为 0。完整环境变量以冻结协议为准。</p>']
    training=data['training']
    sections += ['<p>训练阶段独立尝试：'+str(training['registered_attempts'])+'；合法：'+str(training['legal_attempts'])+'。'
        '失败保留在每组登记的六个电路分母中，失败运行输出的 CPD 不用于选参或性能统计。'
        '内存分配失败、进程超时和布线失败分别记录；分配失败本身不能证明布线问题无解，也不能定位具体分配点。</p>',
        '<details><summary>训练阶段逐配置覆盖与失败原因</summary>'+table(
            ['架构','路由器','变体','配置号','合法/登记电路','失败原因及数量'],
            [[LABELS[r['family']],r['router'],r['variant'] or '—',r['config'] if r['config'] is not None else '—',
              f"{r['legal']}/{r['registered']}",', '.join(k+': '+str(v) for k,v in sorted(r['failure_counts'].items())) or '—']
             for r in training['groups']])+'</details>',
        '<p><a href="training_analysis/summary.json">训练阶段逐运行记录与证据摘要</a></p>']
    width_rows=[]
    for f,flows in q['width300_sensitivity'].items():
        for flow,splits in flows.items():
            for split,comparisons in splits.items():
                for name,x in comparisons.items():width_rows.append([LABELS[f],flow.upper(),split,name,
                    percent(x['geomean_improvement_percent']),cohort(x),f"{x['paired_legal_samples']}/{x['registered_samples']}"])
    sections += ['<h2>W300 固定参数敏感性</h2>',table(['架构','布局','数据划分','比较','CPD 改善','完整电路','合法配对'],width_rows)]
    diagnostics=[]
    for row in q.get('algorithm_diagnostics',{}).get('groups',[]):
        if row['role'] not in ['R1','fixed_delay','tuned_delay','fixed_delay_critical','tuned_delay_critical']:continue
        def rate(key):
            value=row['run_mean_fractions'].get(key)
            return '— (0/'+str(row['legal_roles'])+')' if value is None else f"{100*value['mean']:.2f}% ({value['valid_runs']}/{row['legal_roles']})"
        diagnostics.append([row['phase'],LABELS[row['family']],row['flow'].upper(),row['role'],
            f"{row['legal_roles']}/{row['registered_roles']}",rate('selected_pin_fraction'),
            rate('fully_delay_scored_pin_fraction'),rate('truncated_query_fraction')])
    sections += ['<h3>候选与延迟查询覆盖</h3>',
        table(['阶段','架构','布局','角色','合法/登记','引脚筛选比例','完整延迟候选覆盖','查询截断比例'],diagnostics),
        '<p>比例为合法运行内比例的算术均值，括号为该项有效运行数/合法运行数，不属于 CPD 统计。'
        '完整延迟覆盖要求前向、反向查询共同覆盖足够的 K 个候选；未启用延迟查询或分母为零时留空。'
        '查询预算耗尽表示未获知距离，不构成不可达证明。不同角色可能复用同一运行。</p>']
    timing_rows=[];setup_rows=[]
    for comparison,groups in t['comparisons'].items():
        for row in groups['per_case']:
            timing_rows.append([row['circuit'],row['split'],LABELS[row['family']],row['flow'].upper(),comparison,
                f"{row['paired_legal_repeats']}/3",number(row.get('router',{}).get('ratio')),
                number(row.get('route_process',{}).get('ratio'))])
    for case in t['cases']:
        successful=[r['setup'] for r in case['repeats'] if r['setup']['status']=='completed']
        def med(key):
            values=[r[key] for r in successful if r.get(key) is not None]
            return number(median(values)) if len(values)==3 else '—'
        setup_rows.append([case['circuit'],LABELS[case['family']],case['flow'].upper(),len(successful),
            med('process_wall_seconds'),med('packing_reported_seconds'),med('partition_wall_seconds'),med('placement_reported_seconds')])
    sections += ['<h2>串行耗时与代价</h2>',
        '<p>每个比值使用三次全部成功重复的中位数；不足三次保留覆盖数并留空。比值小于 1 表示 R1 更快。'
        '计时期间排除了本研究其它进程重叠，主机仍为共享环境。结论限于登记的两个电路，训练与测试结果分列。</p>',
        table(['电路','划分','架构','布局','比较','合法重复','路由时间比','整个路由进程时间比'],timing_rows),
        figure('runtime_quality','串行子集中的耗时与 CPD；左下方向较好。'),
        table(['电路','架构','布局','成功/3','准备进程中位秒','打包报告秒','实际划分秒','布局报告秒'],setup_rows),
        '<p>P0 复用普查打包输入，P1 实际重新打包以构建关键性权重；两者的原始准备进程耗时代表各自执行工作，'
        '不能直接称为等工作量的跨流程端到端加速比。图生成、格式转换与物理审计为共享前置成本，未计入路由器速度比。'
        'R1/A0 与 R1/R1off 分别回答相对官方程序、相同构建内算法开销的问题。</p>']
    balance=data.get('balance',{})
    sections += ['<h2>分区参数语义与独立敏感性对照</h2>',
        '<p>当前 OpenROAD 的分区上限为总权重乘以 (目标比例 + 参数×0.01)。'
        '字面参数 0.03 不代表相对均分容量允许 3% 偏差。spmv 训练诊断的 1337 个等权顶点在该参数下不存在满足约束的整数二分，'
        '工具仍返回成功及 1057∶280 的分区。因此，主矩阵中的 P1 不应描述为已验证的 3% 平衡流程，也不是作者实验环境的精确复现。</p>',
        '<p>另行登记的 relative3 流程使用参数 1.5，表示两分区下相对均分容量 ±3%。'
        '修正组独立检查实际分区权重，未满足约束的结果保留为失败。字面组与修正组分开统计；'
        '同一布局内的 R1/A0 衡量布线贡献，同一路由器下的 relative3/literal 衡量布局参数修正影响。'
        '两种影响不能合并归因于布线算法。每个数据划分仅含两个电路，不据此宣称普遍的架构排序变化。</p>',
        table(['数据划分','W','架构','比较方向','登记配对','合法配对','CPD 比率'],
            [[r['split'],r['width'],r['family'],r['contrast'],r['registered_pairs'],r['legal_pairs'],number(r['geomean_ratio'],6)]
             for r in balance.get('comparisons',[])]),
        '<p><a href="balance_analysis/summary.json">逐电路敏感性结果及证据</a> · '
        '<a href="partition_balance_sensitivity_protocol.json">独立登记协议</a></p>']
    failures=Counter((r['phase'],r['family'],r['flow'],r['role'],r.get('failure_class',r['status']))
        for r in observations['rows'] if r['status']!='legal')
    sections += ['<h2>失败与物理模型边界</h2>',
        table(['角色状态','数量'],sorted(q['role_status_counts'].items())),
        table(['独立路由状态','数量'],sorted(q['unique_run_status_counts'].items())),
        table(['阶段','架构','布局','角色','原因','数量'],[(*key,count) for key,count in sorted(failures.items())]),
        '<p>上述角色计数保留未启动的下游角色与明确的复用关系；独立运行计数用于区分实际尝试。'
        '合法路由同时要求 VPR FULL 和独立的有向边、开关、树及 RR 节点容量审计。独立审计的范围不替代 FULL 的全部检查。</p>',
        '<p>三种 3D 架构采用显式派生的共同平面图，保留原跨层连接与时延；这是控制模型，不是未经改动的作者架构。'
        '2D 与 3D 的逻辑容量一致，但芯片形状、IO 密度与平面线资源不同。Hybrid-O 增加 CB 连接，未建立等面积、等功耗或等独立垂直连接预算。'
        '模型导线 R/C 为零，开关时延仍保留；测量采用理想时钟。结果不构成实体 FPGA 或比特流验证。</p>',
        '<details><summary>各尺寸物理资源核对</summary>'+table(['模型','CLB','DSP','BRAM','IO','2D/3D 平面线容量','SB 配对数','CB 跨层源 OPIN 数'],physical)+'</details>',
        '<p>平面线长排除 CHANX/NONE 的 SB 半节点。CB 跨层边共享源 OPIN 和接收通道容量，边数不能直接当作独立物理过孔数。</p>',
        '<h2>可复核材料</h2><p><a href="benchmark_protocol.json">冻结实验协议</a> · '
        '<a href="selected_configs.json">训练选择及证据绑定</a> · <a href="evaluation_analysis/summary.json">完整统计</a> · '
        '<a href="evaluation_analysis/observations.csv">逐角色 CSV</a> · <a href="serial_analysis/summary.json">串行明细</a> · '
        '<a href="published_reference_analysis.json">原论文公开数据重算</a> · <a href="requirements.json">研究验收项目</a></p>']
    return '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'+\
        '<title>三维 FPGA 架构探索实验报告</title><style>body{font:16px/1.65 system-ui,sans-serif;max-width:1150px;margin:35px auto;padding:0 20px;color:#24323d}h1,h2,h3{line-height:1.3}h2{margin-top:2.4em;border-bottom:1px solid #c9d5dd;padding-bottom:.4em}table{border-collapse:collapse;width:100%;font-size:13px;margin:14px 0}th,td{padding:8px 10px;border:1px solid #d8e0e5;text-align:left}th{background:#edf3f6}.table{overflow-x:auto}figure{margin:24px 0}img{width:100%}figcaption{font-size:13px;color:#566773}a{color:#17658d}details{margin:20px 0}summary{cursor:pointer}</style><body>'+''.join(sections)+'</body></html>'


def main(output):
    output=Path(output);assert not output.exists()
    files=dict(evaluation=BASE/'evaluation_analysis/summary.json',serial=BASE/'serial_analysis/summary.json',
        protocol=BASE/'benchmark_protocol.json',selection=BASE/'selected_configs.json',observations=BASE/'evaluation_analysis/role_observations.json',
        balance=BASE/'balance_analysis/summary.json',training=BASE/'training_analysis/summary.json')
    data={k:read(p) for k,p in files.items()}
    assert data['evaluation']['status']=='all_registered_evaluation_cases_resolved'
    assert data['serial']['observed_repetitions']==36 and data['serial']['isolation']['passed']
    assert data['balance']['status']=='complete' and len(data['balance']['observations'])==144
    assert data['training']['status']=='all_registered_training_attempts_accounted'
    assert data['training']['registered_attempts']==len(data['training']['observations'])==594
    figures=read(BASE/'figures/manifest.json')
    for name,digest in figures['artifact_sha256'].items():assert sha256(BASE/'figures'/name)==digest
    physical=[];bindings={str(p):sha256(p) for p in files.values()}
    for path in sorted((BASE/'benchmark_models').glob('*/manifest.json')):
        m=read(path);assert m['status']=='ready';bindings[str(path)]=sha256(path)
        sb=read(m['fixtures']['sb']['physical_audit']);cb=read(m['fixtures']['cb_o']['physical_audit'])
        physical.append([path.parent.name,*[m['logical_slots'][k] for k in ['clb','complex_dsp','spram','io']],
            number(m['planar_wire_2d_over_3d'],6),sb['sb_pair_count'],cb['cb_crossing_source_rr_nodes']])
    output.write_text(document(data,physical),encoding='utf-8')
    write_json(BASE/'report_manifest.json',dict(utc=utc(),report=str(output),report_sha256=sha256(output),
        source_sha256=sha256(__file__),input_sha256=bindings,figures_manifest_sha256=sha256(BASE/'figures/manifest.json'),
        status='Factual report generated; final scientific interpretation and full acceptance audit remain separate requirements'))
    print(output)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=BASE/'report.html');main(p.parse_args().output)
