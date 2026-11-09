#!/usr/bin/env python3
"""Collect reproducible LaZagna controls without altering prior study results."""
import argparse
from collections import Counter
import csv
import html
import json
from pathlib import Path
import re
from lazagna_common import BASE,ROOT,sha256,utc,write_json


def read(path):return json.loads(Path(path).read_text())


def main():
    p=argparse.ArgumentParser();p.add_argument('--allow-incomplete',action='store_true');a=p.parse_args()
    state=read(BASE/'route_state.json');protocol=read(BASE/'protocol.json')
    audits=read(BASE/'route_audit_summary.json') if (BASE/'route_audit_summary.json').exists() else {}
    diagnostic=read(BASE/'clock_diagnostic_state.json') if (BASE/'clock_diagnostic_state.json').exists() else None
    da=read(BASE/'clock_diagnostic_audit_summary.json') if (BASE/'clock_diagnostic_audit_summary.json').exists() else {}
    compat=read(BASE/'native_compat_state.json') if (BASE/'native_compat_state.json').exists() else None
    ca=read(BASE/'native_compat_audit_summary.json') if (BASE/'native_compat_audit_summary.json').exists() else {}
    repaired=read(BASE/'repaired_pnr_state.json') if (BASE/'repaired_pnr_state.json').exists() else None
    ra=read(BASE/'repaired_pnr_audit_summary.json') if (BASE/'repaired_pnr_audit_summary.json').exists() else {}
    guard=read(BASE/'guardfix_pnr_state.json') if (BASE/'guardfix_pnr_state.json').exists() else None
    ga=read(BASE/'guardfix_pnr_audit_summary.json') if (BASE/'guardfix_pnr_audit_summary.json').exists() else {}
    if da:
        audits=dict(count=audits.get('count',0)+da.get('count',0),passed=audits.get('passed',True) and da['passed'],
                    results=audits.get('results',[])+da['results'])
    if ca:
        audits=dict(count=audits.get('count',0)+ca.get('count',0),passed=audits.get('passed',True) and ca['passed'],
                    results=audits.get('results',[])+ca['results'])
    if ra:
        audits=dict(count=audits.get('count',0)+ra.get('count',0),passed=audits.get('passed',True) and ra['passed'],
                    results=audits.get('results',[])+ra['results'])
    if ga:
        audits=dict(count=audits.get('count',0)+ga.get('count',0),passed=audits.get('passed',True) and ga['passed'],
                    results=audits.get('results',[])+ga['results'])
    amap={r['name']:r for r in audits.get('results',[])}
    complete=state['stage']=='finished' and bool(audits)
    if diagnostic:complete &= diagnostic['stage']=='finished' and bool(da)
    if compat:complete &= compat['stage']=='finished' and bool(ca)
    if repaired:complete &= repaired['stage']=='finished' and bool(ra)
    if guard:complete &= guard['stage']=='finished' and bool(ga)
    if (BASE/'table_tracks_protocol.json').exists():
        complete &= (BASE/'table_tracks_complete.json').exists() and (BASE/'dsp_paper_table_100_w300.json').exists()
    complete &= all((BASE/f'dsp_correspondence_100_w{w}.json').exists() for w in (100,300))
    if (BASE/'clock_graph_mode_protocol.json').exists():complete &= (BASE/'clock_graph_mode_complete.json').exists()
    if not complete and not a.allow_incomplete:raise RuntimeError('Runs/audits incomplete')
    rows=[]
    for j in state['jobs']+(diagnostic['jobs'] if diagnostic else [])+(compat['jobs'] if compat else [])+(repaired['jobs'] if repaired else [])+(guard['jobs'] if guard else []):
        row={k:j[k] for k in ['name','case','family','width','arm','state']}
        d=BASE/'runs'/j['name'];log=(d/'stdout.log').read_text(errors='replace') if (d/'stdout.log').exists() else ''
        m=read(d/'manifest.json') if (d/'manifest.json').exists() else {}
        result=read(d/'result.json') if (d/'result.json').exists() else j
        classification=result.get('classification',j['state'])
        row['clock_model']='ideal' if '_ideal_' in j['name'] else 'route'
        row['binary_variant']='guardfix' if 'guardfix' in j['name'] else 'original'
        if (d/'clock_preflight_cancel.json').exists():classification='cancelled_structural_clock_unreachable'
        if (d/'capacity_proof_cancel.json').exists():classification='cancelled_proven_dsp_capacity_cut'
        if 'spram[0].clk[0]' in log and '-- no possible path' in log:classification='structural_clock_unreachable'
        if 'clb[0].clk[0]' in log and '-- no possible path' in log and j['family']=='native' and row['clock_model']=='route':
            classification='clock_graph_generation_mode_mismatch'
        if 'unknown net $undef' in log:classification='constant_net_preprocessing_incompatibility'
        if 'Wire length usage ratio' in log and 'exceeds limit' in log:classification='initial_wirelength_abort'
        if 'Failed to find device which satisfies resource requirements' in log:classification='device_capacity_failure'
        if result.get('native_legal'):classification='legal_audited' if amap.get(j['name'],{}).get('passed') else 'native_legal_audit_pending_or_failed'
        if (d/'input_registration_race.json').exists():classification='excluded_input_registration_race'
        row.update(classification=classification,native_full=result.get('native_legal',False),independent_audit=amap.get(j['name'],{}).get('passed'),
                   wall_seconds=m.get('wall_seconds'),returncode=m.get('returncode'),**result.get('metrics',{}))
        if not row['native_full'] and 'critical_path_ns' in row:
            row['infeasible_reported_critical_path_ns']=row.pop('critical_path_ns')
        # Adopted jobs killed at their deadline may have an empty GNU-time
        # receipt whose mtime is the start time. Preserve the raw manifest and
        # report an explicitly labelled completion-observer upper bound.
        correction=d/'timeout_timing_observation.json'
        if correction.exists():
            observed=read(correction)
            row['wall_seconds']=observed['observed_wall_seconds_upper_bound']
            row['wall_seconds_source']='result-file completion observer; upper bound, not performance measurement'
        patterns={'placement_temperatures':r'Placement number of temperatures:\s+(\d+)',
                  'placement_swap_attempts':r'Placement total # of swap attempts:\s+(\d+)',
                  'placement_aborted_percent':r'Swaps aborted:\s+\d+\s+\(([0-9.]+)\s*%',
                  'placement_seconds':r'# Placement took ([0-9.]+) seconds'}
        for key,pat in patterns.items():
            match=re.search(pat,log)
            if match:row[key]=int(match[1]) if key in ('placement_temperatures','placement_swap_attempts') else float(match[1])
        iterations=[int(x[1]) for line in log.splitlines() if (x:=re.match(r'\s*(\d+)\s+[0-9.]+\s+[0-9.e+-]+\s+\d+\s+[0-9.e+-]+\s+\d+\s+\d+\s+\d+\s+\(',line))]
        if iterations:row['last_completed_iteration']=iterations[-1]
        if j['arm']=='fixed' and m:
            primary=BASE/'runs'/f"paper_primary_{j['case']}_w300"
            row['same_packed_netlist']=m['inputs'].get(str(primary/'packed.net'))==sha256(primary/'packed.net')
            row['same_placement']=m['inputs'].get(str(primary/'fixed.place'))==sha256(primary/'fixed.place')
            if not row['same_packed_netlist'] or not row['same_placement']:
                if not (d/'input_registration_race.json').exists():raise RuntimeError('Unexplained fixed input mismatch')
                assert not row['native_full'] and '# Load Placement' not in log
        rows.append(row)
    graph=[]
    for width in [100,300]:
        d=read(BASE/f'graph_comparison_40_w{width}.json')
        assert d['left']['dsp_profiles']==d['right']['dsp_profiles']
        graph.append({'width':width,'same_all_dsp_pin_destinations':True,'dsp_sites':d['left']['dsp_site_count'],
                      'dsp_exit_histogram':d['left']['dsp_exit_capacity_histogram'],**d['comparison']})
    vertical={f'{family}_w{width}':read(BASE/f'vertical_{family}_100_w{width}.json') for family in ['paper','native'] for width in [100,300]}
    protected={path:sha256(path)==expected for path,expected in protocol['protected_files'].items()}
    assert all(protected.values())
    data={'utc':utc(),'complete':complete,'rows':rows,'status_counts':dict(Counter(r['classification'] for r in rows)),
          'primary_status_counts':dict(Counter(r['classification'] for r in rows if r['name'].startswith('paper_primary_'))),
          'graph_correspondence':graph,'vertical':vertical,'protected_files_unchanged':protected,
          'sources':protocol['sources'],'audits':{'count':audits.get('count',0),'passed':audits.get('passed')},
          'scope':'Paper-era source/toolchain and published architecture-condition PnR on exact existing BLIFs, followed by shared packed-netlist/placement W100/W300 controls. Not authors exact historical experiment or full unpublished synthesis/bitstream reproduction.'}
    by_name={r['name']:r for r in rows}
    fixed=[]
    for case in protocol['diagnostics']['focus_cases']:
        for width in (100,300):
            paper=by_name[f'paper_ideal_{case}_w{width}_i200']
            native=by_name[f'native_ideal_{case}_w{width}_i200']
            if native['classification']=='constant_net_preprocessing_incompatibility':
                native=by_name[f'native_ideal_compat_{case}_w{width}_i200']
            fixed.append({'case':case,'width':width,'paper':paper['name'],'native':native['name'],
                          'paper_status':paper['classification'],'native_status':native['classification'],
                          'paper_cpd_ns':paper.get('critical_path_ns'),'native_cpd_ns':native.get('critical_path_ns')})
    data['canonical_ideal_fixed_controls']=fixed
    data['full_grid_dsp_correspondence']={str(w):read(BASE/f'dsp_correspondence_100_w{w}.json')
                                         for w in (100,300) if (BASE/f'dsp_correspondence_100_w{w}.json').exists()}
    data['canonical_ideal_success_by_width']={str(w):{family:sum(by_name[x[family]]['native_full'] for x in fixed if x['width']==w)
                                                  for family in ('paper','native')} for w in (100,300)}
    data['guardfix_pairs']=[{'case':case,'before':prefix+case+'_w300',
                            'after':('paper_guardfix_route_pnr_' if case=='bnn' else 'paper_guardfix_ideal_pnr_')+case+'_w300'}
                           for case,prefix in [('bnn','paper_primary_'),('conv_layer','paper_ideal_pnr_'),('dla_like.small','paper_ideal_pnr_')]]
    write_json(BASE/'analysis.json',data)
    fields=list(dict.fromkeys(k for r in rows for k in r))
    with (BASE/'analysis.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
    names={'legal_audited':'成功，双重检查通过','native_legal_audit_pending_or_failed':'VPR 成功，独立检查待完成/未通过',
           'structural_clock_unreachable':'BRAM时钟物理无路径','cancelled_structural_clock_unreachable':'已由零入边证明排除（取消重复运行）',
           'constant_net_preprocessing_incompatibility':'旧网表与新版本常量合并不兼容',
           'cancelled_proven_dsp_capacity_cut':'DSP容量割已独立验证，停止无解运行',
           'initial_wirelength_abort':'首轮线长阈值提前终止',
           'excluded_input_registration_race':'输入摘要读取竞态，排除数值比较',
           'clock_graph_generation_mode_mismatch':'RRG时钟生成模式与布线模式不匹配',
           'device_capacity_failure':'CLB 容量不足','routing_failure':'布线未收敛','timeout':'达到时间上限',
           'not_run_no_fixed_placement':'上游未产生固定布局','running':'运行中','queued':'排队中'}
    def esc(x):return html.escape(str(x))
    cells=[]
    for r in rows:
        label=r['family']+('＋guard修复' if r['binary_variant']=='guardfix' else '')+('（常量合并off）' if '_compat_' in r['name'] else '')
        directory=BASE/'runs'/r['name']
        links=f'<a href="runs/{esc(r["name"])}/manifest.json">命令</a> · <a href="runs/{esc(r["name"])}/stdout.log">日志</a>' if (directory/'manifest.json').exists() else '上游未产生输入 / 不需兼容重试'
        cells.append('<tr>'+''.join(f'<td>{esc(v)}</td>' for v in [r['case'],label,r['arm']+'/'+r['clock_model'],r['width'],names.get(r['classification'],r['classification']),r.get('iterations',r.get('last_completed_iteration','—')),r.get('critical_path_ns','—')])+f'<td>{links}</td></tr>')
    fixed_cells=[]
    for x in fixed:
        values=[x['case'],x['width']]+[names.get(x[f'{family}_status'],x[f'{family}_status']) for family in ('paper','native')]+[x['paper_cpd_ns'] or '—',x['native_cpd_ns'] or '—']
        fixed_cells.append('<tr>'+''.join(f'<td>{esc(v)}</td>' for v in values)+'</tr>')
    guard_cells=[]
    for pair in data['guardfix_pairs']:
        before,after=(by_name[pair[key]] for key in ('before','after'))
        values=[pair['case'],before['clock_model'],names.get(before['classification'],before['classification']),
                names.get(after['classification'],after['classification']),
                f"{before.get('placement_temperatures','—')} → {after.get('placement_temperatures','—')}",
                f"{before.get('placement_aborted_percent','—')} → {after.get('placement_aborted_percent','—')}",
                f"{before.get('critical_path_ns','—')} → {after.get('critical_path_ns','—')}"]
        guard_cells.append('<tr>'+''.join(f'<td>{esc(v)}</td>' for v in values)+'</tr>')
    vrows=[]
    for key,v in vertical.items():
        active=sum(x['count'] for x in v['fanin_fanout_histogram'] if x['fanin'] and x['fanout'])
        vrows.append('<tr>'+''.join(f'<td>{esc(x)}</td>' for x in [key,v['physical_vertical_channels'],active,v['vertical_locations'],v['sample_channel_at_20_20_layer0'],v['plane_to_plane_switch_delay_ps_values']])+'</tr>')
    status='已完成并审计' if complete else '进行中：下列结果随收集时间标明状态'
    out=f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>LaZagna 复现对照与架构对应检查</title>
<style>body{{max-width:1200px;margin:36px auto;padding:0 24px;font:16px/1.7 system-ui;color:#213047;background:#f7f9fc}}h1,h2{{color:#122b49}}table{{border-collapse:collapse;background:white;width:100%;font-size:14px}}td,th{{padding:8px;border:1px solid #d4dce6;text-align:left}}.card{{background:white;padding:18px 24px;margin:20px 0;border-left:4px solid #307aa5}}code{{background:#edf2f7}}a{{color:#126a9a}}input{{padding:8px;width:360px;max-width:90%}}</style>
<h1>LaZagna 复现对照与架构对应检查</h1><p>{esc(status)} · UTC {esc(data['utc'])}</p>
<div class="card"><b>已确认：</b>发布XML的DSP引脚出口保持一致，但平面网络、跨层资源与延迟模型并不等价。历史LaZagna分支还存在已复现的布局条件错误，发布模板存在BRAM时钟配置冲突。当前A0不是该历史分支；这些原因需要分别归因，不能把所有失败都归为H3D引导或未生成fabric RTL。</div>
<h2>复现范围与版本</h2><p>采用 <a href="https://arxiv.org/html/2505.05579v1">LaZagna 2025 论文</a>发布当日最后一个公开提交 <code>16fa62c9</code>，OpenFPGA <code>729e6187</code>、其 VTR <code>a80511e8</code>，未改其算法与 3D-SB 生成器。原生 A0 为独立 VTR <code>0b912334</code>。原始论文没有指定实际实验 commit。</p>
<table><thead><tr><th>名称</th><th>实际比较对象</th><th>允许得出的结论</th></tr></thead><tbody>
<tr><td>原A0</td><td>原生VTR 0b912334；原研究的自动阵列、W100、ideal时钟</td><td>原A1～A4的算法基线；−1.39%仍相对它</td></tr>
<tr><td>LaZagna公开配置主运行</td><td>VTR a80511e8＋原3D-SB生成器；100×100×2、W300、route时钟；11个选定电路</td><td>核对公开工具/参数在相同BLIF上的可运行性与失败原因</td></tr>
<tr><td>固定输入诊断</td><td>复用主运行packed/place；两工具/图、W100/W300；ideal及必要的常量兼容</td><td>资源与连通敏感性；不隔离单一算法因素</td></tr>
<tr><td>最小guard修复</td><td>同一历史版本，只修改两个布局条件，重新完整PnR</td><td>检验该历史分支布局缺陷的因果影响</td></tr>
</tbody></table>
<p>主对照：100×100×2、W=300、50% SB、repeated_interval、subset、垂直比例 0.739；cube_bb、seed=1、inner_num=0.5、clock_modeling=route。使用现有实验的同一 BLIF；显式执行 pack/place/route/analysis，保留默认路由迭代预算。每次进程最多 3600 秒，含图加载与 lookahead。后续固定对照复用主对照同一 packed.net/fixed.place，W=100/300、200次迭代上限、失败预测off、高强度拥塞阶段的起始阈值保持1.0；首轮线长阈值仍沿用默认0.85，触发情况单列。两条工具链均要求 VPR FULL 检查。</p>
<p>公开历史 Verilog 配置引用缺失的 yosys.ys，OpenFPGA 模板 VPR 行仅有 --pack，且含未完整替换的测试平台变量。本研究没有悄悄补用后来版本的综合脚本。因此这是论文架构条件下的 PnR 对照，不宣称作者原始网表、全部论文数值或端到端 bitstream 已精确复现。报告中的运行时间因并行执行，仅用于任务诊断。</p>
<p>两种架构均为两层且每层逻辑资源类型相同，没有触及论文所述的多于两层或跨层逻辑异构PnR限制。理想时钟对照跳过实际时钟网络的布线；成功仅表示该模型下合法，不代表时钟网络或可下载bitstream已完成实现。</p>
<h2>DSP 出口与平面连接</h2><p>40×40×2 全图逐边检查：两架构在 W100 的 473,768 个、W300 的 765,568 个平面节点均按类型、坐标、方向、ptc、segment 唯一对应；全部 380 个 DSP 的 74 个 OPIN 及其目标节点逐项相同。W100 内部 DSP 只有 44 个唯一出口（左右各22），W300 增为130～132；边界位置另计。OPIN 的边数不能当作独立通道容量。</p>
<p><b>完整论文阵列复核：</b>100×100×2的全部2548个DSP、188552个OPIN，在W100和W300两种宽度下的目标节点多重集合均完全一致；按物理坐标、层、方向、ptc、segment与容量比较，不依赖跨版本节点编号相同。W100有2496个内部DSP容量44、52个边界DSP容量110；W300内部容量130/131/132分别为624/1248/624个，52个边界DSP容量327。证据：<a href="dsp_correspondence_100_w100.json">全阵列W100</a>、<a href="dsp_correspondence_100_w300.json">全阵列W300</a>。</p>
<p>上述精确对应以发布XML的280/40权重为准；另列的表III字面260/40敏感性模型不能直接沿用逐边相同结论，其DSP容量另见<a href="dsp_paper_table_100_w300.json">全图扫描</a>。</p>
<p>表III字面260/40模型的内部DSP出口为129或131（各1248个），边界出口为324（52个）；它仍比原W100容量大，但不是发布XML模型的逐引脚等价替代。</p>
<p>W100 平面边分别为3,678,820 / 3,595,048，只有1,446,089条完全相同。LaZagna 使用内置 Wilton/fs=3，当前混合架构使用 Beyond Flatland 自定义规则；同版 VPR 更换规则只改变通道间连接。跨版本还存在 CHAN→IPIN 的具体连接变化。原 LaZagna 添加 Z 的过程保留了全部3,678,820条已有平面边。详见 <a href="graph_comparison_40_w100.json">W100</a>、<a href="graph_comparison_40_w300.json">W300</a>、<a href="old_builtin_vs_old_custom.json">同版规则对照</a>、<a href="old_builtin_vs_new_builtin_z.json">同名 Wilton 跨版本对照</a>、<a href="paper_base_vs_added_z.json">原脚本保边检查</a>。</p>
<p>图生成阶段的时钟参数也是区别之一：原图使用route、当前原生图沿用ideal。固定同一原生版本/XML/W100只切换生成参数，40×40×2图的2128个CLB时钟IPIN由全部零入边变为全部有入边（共29792条）；此外普通CHAN→IPIN的具体分配也重新排列，OPIN出口和通道间连接保持相同。因此，主图的平面边差异不能全部归因于版本或Wilton/custom，必须同时记录生成阶段的clock_modeling。见<a href="native_clock_graph_mode_comparison.json">同版本同XML时钟生成对照</a>。</p>
<h2>跨层资源与实际延迟</h2><table><thead><tr><th>100×100×2 图</th><th>物理资源组</th><th>有进有出</th><th>XY 位置</th><th>抽样平面通道组成</th><th>平面→跨层→平面开关延迟 / ps</th></tr></thead><tbody>{''.join(vrows)}</tbody></table>
<p>LaZagna 一个物理跨层通道由两个串行 CHANX/NONE 节点及其中间跨层边表示，上下方向为不同资源；当前原生模型每个 CHANZ 为共享容量的双向资源，并可能用于同层绕行。全部旧编码配对已验证：两端容量1、不同层、相同XY、无旁路、输入输出接本层平面通道。两架构都没有 DSP OPIN→Z 直接连接。</p>
<p>旧图的跨层出口还包含L16驱动器；当前scatter/gather定义只连接L4。LaZagna每次跨层必须到另一层，当前双向资源还允许输入与输出位于同一层。这些都是模型差异，不能通过把CHANX/NONE改名为CHANZ就视为等价。</p>
<p><b>延迟审计发现：</b>原架构修改函数把137.325 ps除以3；原图生成器实际使用两级45.775 ps的3D开关，再接L4/L16驱动器。因此路径实际为277.376/470.841 ps；原生模型为142+185.826=327.826 ps。不能用“137 ps 对142 ps”代表相同端点间的完整路径延迟。保留发布代码行为，不自行修正后冒称原版。</p>
<p>论文表格写260/40条L4/L16，而发布XML权重为280/40；本次实际W300抽样通道为262/38，W100为88/12。配置权重与最终离散通道数分别记录。</p>
<p>已另建字面采用表III的260/40敏感性图（仅修改L4权重）：实际通道确为260/40，所有2352个BRAM时钟IPIN仍无入边。因此该表格/代码差异不能解释或消除原参数时钟不可达。证据：<a href="table_tracks_protocol.json">表格参数协议</a>、<a href="clock_paper_table_w300.json">时钟扫描</a>、<a href="vertical_paper_table_100_w300.json">通道与跨层映射</a>。</p>
<h2>实际运行结果</h2><p>状态计数：{esc(data['status_counts'])}。独立审计已完成 {audits.get('count',0)} 个合法结果；原769次及后续故障诊断的证据文件哈希保持不变。</p>
<p>11个原参数主运行的结果为：{esc(data['primary_status_counts'])}。以下22行固定输入对照采用理想时钟；原生工具仅在旧网表常量不兼容时选用关闭常量合并的重试。每种宽度各11个电路，其中dla_like.medium因CLB容量不足没有固定布局。成功计数（VPR FULL）：{esc(data['canonical_ideal_success_by_width'])}。</p>
<table><thead><tr><th>Benchmark</th><th>W</th><th>原LaZagna工具/图</th><th>原生A0工具/图</th><th>原图CPD ns</th><th>原生图CPD ns</th></tr></thead><tbody>{''.join(fixed_cells)}</tbody></table>
<p>此表固定的是原版产生的布局，其中存在下述布局代码缺陷。因此它用于资源与连通诊断，不作为高质量论文性能基线；没有将共同成功子集的CPD比值解释为算法优势。</p>
<p><b>时钟配置冲突：</b>发布架构的 spram.clk Fc=0，但发布模板要求 clock_modeling=route。首批原配置运行直接报告 BRAM 时钟无路径；两架构的W300完整图扫描也确认所有BRAM时钟IPIN入度为0。原参数主运行继续保留；有活动BRAM时钟的重复固定对照按结构证明取消。另建 ideal 时钟诊断，复用原来的 packed.net、fixed.place 与 RRG，只排除这一时钟障碍；它不是未经修改的原版复现，也不重做可能受不可达时钟影响的布局。详见<a href="clock_diagnostic_protocol.json">协议修订</a>与<a href="clock_paper_w300.json">原图时钟证明</a>。</p>
<p><b>另一个需要排除的时钟输入问题：</b>两次native/fixed/bnn/route运行把按ideal生成的原生RRG用于route时钟，报告CLB时钟无路径。上述同版本生成对照及<a href="clock_all_native_ideal_100_w300.json">原生完整W300图扫描</a>将其归为图生成/布线模式不匹配，而非算法未收敛或CLB架构Fc=0。两次均不纳入有效性能比较；后续理想时钟固定对照使用与图匹配的模式。切换生成模式仍不能补足BRAM的Fc=0入口。</p>
<p><b>跨版本网表读取：</b>新VPR默认合并同值常量生成器，将$undef并入$false；旧版打包网表仍保留$undef，因此原生工具在进入布线前报unknown net。单列兼容性重试关闭新VPR的常量合并，保留网表和布局文件字节不变；该输入问题不计为算法布线失败。见<a href="native_compat_protocol.json">兼容性协议</a>。</p>
<p><b>输入审计例外：</b>历史VPR在只读入布局的流程中也会无条件重新写出该布局。一次已因时钟零入边而取消的重复原时钟运行，在另一个进程重写期间记录了不同的输入摘要，且取消前尚未加载布局。该次明确排除数值比较，原始记录保留；上述理想时钟固定对照及成功结果不包含此例外。证据见<a href="runs/paper_fixed_dla_like.small_w300_i200/input_registration_race.json">输入摘要竞态记录</a>。后续复用脚本改用每次运行的私有输入副本。</p>
<p><b>布局影响检查：</b>对conv_layer与dla_like.small另列两次paper/primary/ideal运行，从打包、布局开始只改时钟模型，检查原配置的不可达时钟是否影响上游布局。这两次重新布局不纳入固定布局比较。见<a href="repaired_pnr_protocol.json">重跑范围</a>。200轮只是固定对照上限；首轮线长阈值提前终止仍单列，没有把它当作跑满200轮。</p>
<p><b>已确认的历史分支代码缺陷：</b>2025-04-08提交af5b6a4434在两个布局搜索范围函数中，把有效坐标（!=OPEN）错误地作为返回无效范围的条件。原版和仅改理想时钟的conv_layer均只有2个退火温度点、约93%的交换中止。已直接提取原函数与修复函数编译验证，并单独构建仅修正这两个guard的VPR：bnn保留route时钟、conv_layer/dla_like.small与理想时钟完整PnR对照匹配。修复组不混入原版组，也不据此推断作者论文实际使用了这一有缺陷的公开快照。见<a href="../../patches/lazagna-placement-validity-guards.patch">最小补丁</a>和<a href="guardfix_pnr_protocol.json">因果对照协议</a>。</p>
<table><thead><tr><th>Benchmark</th><th>两组时钟</th><th>原版结果</th><th>仅修复guard</th><th>退火温度点：前→后</th><th>交换中止%：前→后</th><th>CPD ns：前→后</th></tr></thead><tbody>{''.join(guard_cells)}</tbody></table>
<p>三对控制的命令、架构、BLIF和RRG摘要一致；打包网表只归一化含输出文件路径的根节点name后，全部内容也一致。见<a href="guardfix_input_equivalence.json">匹配控制验证</a>。该错误的来源为公开的<a href="https://github.com/IY2002/vtr-verilog-to-routing/commit/af5b6a44340e69e4c2c9e44713626888a4b6bd5a">历史分支提交</a>。</p>
<p>这三对运行允许布局随代码修复改变；它们与前表的固定布局路由对照是不同实验。原版超时只能说明本次预算内未得到合法解，不能据此计算延迟改进率。跨运行时间采用并行任务条件，不能用作算法加速比。</p>
<p><input id="filter" placeholder="筛选 benchmark / paper / native / 状态" oninput="document.querySelectorAll('#runs tbody tr').forEach(r=>r.hidden=!r.textContent.toLowerCase().includes(this.value.toLowerCase()))"></p>
<table id="runs"><thead><tr><th>Benchmark</th><th>工具/架构</th><th>对照</th><th>W</th><th>状态</th><th>迭代</th><th>CPD ns</th><th>证据</th></tr></thead><tbody>{''.join(cells)}</tbody></table>
<h2>结论边界</h2><p>DSP 的原 W100 容量瓶颈也存在于 LaZagna 的同宽度直接出口，不支持“原生迁移漏接 DSP 出口”解释。W300消除这一局部必要条件障碍，不保证全局可布。dla_like.medium在论文阵列需要23,877个CLB，而只有14,308个，在打包阶段即超容量，应与布线不收敛分开。</p>
<p>论文阵列的两种W100图各有344个经独立复核的DSP局部容量证书：attention_layer可见28个不同网络必须穿过容量22的出口，conv_layer为64&gt;44，dla_like.small为48&gt;44。证书间有重叠，不能累加缺口；只约束所记录的固定终端与布局。证据：<a href="dsp_cuts_paper_w100.verified.json">原图容量复核</a>、<a href="dsp_cuts_native_w100.verified.json">原生图容量复核</a>。</p>
<p>固定对照比较的是“工具链＋架构图”；宽度变化同时改变了 LaZagna 跨层通道数，当前原生 Z 数量保持不变。它不构成单独算法或纯平面资源的因果对照。原 A3 关键路径延迟几何均值降低1.39%仍只相对原 A0、原12个共同成功样本，不能解释为优于LaZagna。</p>
<p>若后续要声称等价迁移，应冻结LaZagna原平面边，将每个已验证的串行Z节点对转换为独立且有方向的CHANZ资源，保留其输入/输出集合、容量、L4/L16连接和实际路径延迟，再在同一图上比较A0/A3。当前零RC模型允许对被收缩串行路径的开关延迟求和；一般非零RC模型不能直接照搬。该等价转换是后续工作，本轮未把混合架构重新标注成等价模型。</p>
<p><a href="analysis.json">机器可读结果</a> · <a href="analysis.csv">CSV</a> · <a href="protocol.json">冻结协议</a> · <a href="route_audit_summary.json">独立审计</a></p></html>'''
    (BASE/'report.html').write_text(out)
    print(json.dumps({'complete':complete,'counts':data['status_counts'],'audits':data['audits']},ensure_ascii=False))


if __name__=='__main__':main()
