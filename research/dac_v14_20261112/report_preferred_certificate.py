#!/usr/bin/env python3
"""Bind candidate-specific query evidence, costs, and cache-context limitations."""
import csv
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
b=D/'preferred_query_certificate_offline_03';r=read(b/'analysis.json');assert r['passed'] and read(b/'index_reproduction.json')['passed']
rec=read(D/'preferred_native_context_reconciliation_01.json');assert rec['passed']
checks={};owners=[]
for name in ['preferred_query_certificate_offline_01','preferred_query_certificate_offline_02','preferred_query_certificate_offline_03']:
 d=D/name;a=read(d/'analysis.json');ex=read(d/'execution.json');reg=read(d/'execution_registration.json');proc=Path('/proc')/str(reg['pid'])/'stat';live=proc.exists() and proc.read_text().split(') ',1)[1].split()[19]==reg['start_ticks'];assert not live;owners.append(dict(batch=name,pid=reg['pid'],start_ticks=reg['start_ticks'],live=live))
 for p,h in a['source_sha256'].items():assert sha(p)==h;checks[p]=h
 for p,h in ex['source_sha256'].items():assert sha(p)==h;checks[p]=h
 for p,h in ex['output_sha256'].items():assert sha(d/p)==h;checks[str(d/p)]=h
 names=['registration.json','execution.json','analysis.json','unit_validation.json']
 for n in ['control_reproduction.json','index_reproduction.json']:
  if (d/n).exists():assert read(d/n)['passed'];names.append(n)
 for n in names:checks[str(d/n)]=sha(d/n)
labels={'0':'P0','1':'Ph','2':'Pf','3':'Pt','4':'Pi'};p=D/'paper';csvp=p/'data/preferred_query_v14.csv';assert not csvp.exists()
with csvp.open('w') as f:
 w=csv.writer(f);w.writerow(['arm','contexts','paths','online_exact','certified_no_cross_better','expansions','core_query_seconds','crossing_records_examined'])
 for k,x in r['summaries'].items():
  examined=sum(v['full_crossing_records' if k=='3' else 'indexed_crossing_records'] for v in r['crossing_lookup_work'].values()) if k in ['3','4'] else 0
  w.writerow([labels[k],x['queries'],x['paths'],x['exact'],x['certified_no_cross_better'],x['expansions'],x['query_seconds'],examined])
summary=dict(passed=True,native_route_calls=0,scope='Offline post-publication query prototype, one seen circuit,10guided complete-source focus contexts',summaries=r['summaries'],crossing_records_full=sum(v['full_crossing_records'] for v in r['crossing_lookup_work'].values()),crossing_records_indexed=sum(v['indexed_crossing_records'] for v in r['crossing_lookup_work'].values()),one_time_index_input_crossing_records=next(iter(r['crossing_lookup_work'].values()))['full_crossing_records'],targeted_index_all_non_time_records_exact=True,unit_final_comparisons=5760,unit_graphs=240,unit_index_stage_strictly_reused=True,source_sha256=checks,owners=owners,native_cache_hit_focus=rec['native_cache_hits'],sparse_offline_cache_hit_focus=rec['sparse_offline_prior_cache_hits'],quality_promoted=False,qualification='Physical one-preferred-cross graph-walk UBs with zero RC and actual saved seed Tdel; no native congestion/multi-cross/tree-extension/STA certificate. No runtime dominance certificates. Prefix shift unused on real cases because floor=0. Core times exclude graph/index/selected-list construction; full index requires one traversal of858216crossing records. Sparse offline cache state differs from full native trajectory. Fixed per-query cap does not prove no extra actual online work.')
write(D/'preferred_query_development_summary_01.json',summary)
tex=r'''A separate offline query study asks whether search ordering can improve actual candidate-delay information without enlarging the per-query work cap. It reuses all ten guided contexts among the 31 completely captured focus seed groups, with the same zero-RC directed RRG, native bounding box and actual queued-prefix delays. The graph-walk model permits a same-layer prefix, exactly one recommended crossing and a same-layer suffix. It is not the native congestion objective or an arbitrary multi-cross route optimum. A common minimum seed-prefix delay can be removed from virtual terminal edges and restored to both upper and pending-frontier bounds. Independent forward phase-graph Floyd checks validate the adapter on 240 random graphs under work/storage limits and arbitrary, potentially inadmissible, ordering values (5,760 final comparisons). In these actual contexts the minimum prefix is always zero, so that transformation has no observed effect. Memory-limited searches expose no lower certificate.

With the same 256-expansion and storage caps, ordinary seed-directed ordering finds three preferred-candidate walks. Ordering sink-side expansion toward actual recommended crossing heads finds four, using 2,094 rather than 2,242 expansions across the ten contexts. Every returned real edge, switch delay, direction, single crossing, bounding box and actual seed prefix passes independent physical checking; bounds agree with the previously sealed unlimited oracle. The extra returned path equals its offline optimum, but the bounded engine cannot certify that fact. None of these queries yields an online exactness or no-extra-cross dominance certificate. The other three returned preferred walks remain 15.099\% above the offline optimum. Thus path availability does not make a cached upper bound an exact distance or calibrated confidence.

\begin{table}[t]
\centering
\caption{Offline preferred-query ordering at a fixed cap. All arms use the same ten observed contexts; no new native route is run.}
\label{tab:preferred-query-v14}
\begin{tabular}{lrrrr}
\hline
Arm & Paths & Exact & Expansions & Query (ms)\\
\hline
'''
for k,x in r['summaries'].items():tex+=f"{labels[k]} & {x['paths']} & {x['exact']} & {x['expansions']} & {1000*x['query_seconds']:.3f} \\\\\n"
tex+=r'''\hline
\end{tabular}
\end{table}
P0 uses zero ordering, Ph seed-directed ordering, Pf additionally factors the common prefix, Pt targets mandatory crossing heads, and Pi performs the same targeted query through a static preferred-source index. Pi reproduces every Pt non-time result, bound, search counter and path. Across ten calls, preferred-crossing lookup examines 31 records instead of 8,582,160. Index construction itself traverses 858,216 crossing records once; construction, graph loading and selected-list assembly are outside the core query timer. The query-only times therefore do not establish an online or whole-process speedup. The original variants are reproduced exactly, and the unchanged final adapter tests are strictly reused for indexing.

Cache provenance is a material limitation. These same ten native search domains and complete sink-layer seed sets match the frozen native reuse run, but that run has zero cache hits in the focus set. The sparse offline replay had three prior hits because it queried all 31 focus contexts, including unguided ones, whereas the native run queried actual guided searches across the full trajectory. Consequently, those three offline hits cannot fund an asserted native budget reallocation. The next registered diagnostic will capture complete actual seeds and current route-tree membership across guide-bearing searches before evaluating broader fixed-budget schedules or legal extensions. It has not been submitted. This study neither changes final CPD nor promotes a routing policy.
'''
fragment=p/'data/preferred_query_discussion_v14.tex';fragment.write_text(tex)
main=p/'main.tex';s=main.read_text();a='\\input{data/current_eligibility_discussion_v14.tex}';assert s.count(a)==1;s=s.replace(a,a+'\n\\input{data/preferred_query_discussion_v14.tex}');main.write_text(s)
with (p/'claims_evidence.md').open('a') as f:
 f.write('\n| C62 | 候选定向查询在同256工作上限提高一个已观测上下文的路径覆盖，仍无运行时排序证书 | [三阶段汇总](../preferred_query_development_summary_01.json)、[最终物理审计](../preferred_query_certificate_offline_03/analysis.json)、[最终5760独立Floyd检查](../preferred_query_certificate_offline_02/unit_validation.json)、[查询费用CSV](data/preferred_query_v14.csv) | 240随机图×4模式×3预算×2存储=5760检查，含任意不可采纳heuristic、零环/重复seed/缺源/断连和storage loss；index阶段测试严格复用。10guided完整起点focus场景：Ph3path/2242展开，Pt/Pi4path/2094展开，预算各256，真实RRG/BB/单cross/实际prefix核查。新增path与离线最优相同但bounded算法没有exact证书；其他3path比最优高15.099%。全部prefix floor0，不能以unit通过宣称真实数据变换有益。无native route调用、无CPD/多cross/价格/全树合法extension证明，不推广 |\n')
 f.write('| C63 | 静态推荐入口索引减少候选过滤工作，缓存历史差异阻止直接外推原生收益 | [索引逐字段等价](../preferred_query_certificate_offline_03/index_reproduction.json)、[原生上下文核对](../preferred_native_context_reconciliation_01.json)、[下一输入采集登记](../actual_search_tree_experiment_01.json) | 同Pt所有非时间输出/路径/上下界/工作计数精确Pi；10次候选过滤8582160→31条，但全索引构建另需遍历858216条，query timer不含构建/图加载/selected-list，不能写成原生总进程speedup。同10actual domain及全sink层seed精确native Qs，却native cachehit0、稀疏offline priorhit3，后者含nonguided focus查询且历史不同；不能声称原生空闲预算。下一完整实际seed/当前tree只读trace已登记未实施/提交；先看覆盖和合法extension，再考虑native方法组合 |\n')
for n in ['mechanisms_and_ablation.md','DEVELOPMENT_STATUS.md']:
 with (p/n).open('a') as f:f.write('\n\n2026-11-13 离线推荐候选查询与索引证据见[C62/C63](claims_evidence.md)。同256工作限额，10focus contexts中路径3→4、总展开2242→2094，所有路径/非时间输出在索引前后精确，查询候选记录8582160→31；一次性索引扫描858216条及构建费用未进入query timer，不作native速度结论。依然无exact/dominance证书，prefix floor均0，physical单cross步行非全树合法或STA保证。native Qs在同10上下文cachehit0，offline sparse history为3，历史不可混用。下一actual_search_tree_experiment_01仅登记，尚无新路由调用，公开快照仍f7167bd。\n')
ledger=p/'data/evidence_v14_ledger.json';v=read(ledger)
for rel in ['preferred_query_development_summary_01.json','preferred_query_certificate_offline_01/analysis.json','preferred_query_certificate_offline_02/analysis.json','preferred_query_certificate_offline_03/analysis.json','preferred_query_certificate_offline_03/index_reproduction.json','preferred_native_context_reconciliation_01.json','actual_search_tree_experiment_01.json','paper/data/preferred_query_v14.csv','paper/data/preferred_query_discussion_v14.tex']:v['sources_sha256'][rel]=sha(D/rel)
v['preferred_candidate_query']=dict(status='offline_physically_audited_not_promoted',contexts=10,paths_seed_targeted=[3,4],expansions_seed_targeted=[2242,2094],native_route_calls=0,exact_certificates=0,lookup_records=[8582160,31],native_sparse_cache_hits=[0,3])
write(ledger,v);print('C62/C63 and next diagnostic registration reported; native route calls0')
