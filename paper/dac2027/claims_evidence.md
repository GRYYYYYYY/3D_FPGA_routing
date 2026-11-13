# DAC2027 主张与证据表

版本：2026-11-10 北京时间初稿。主文为 [main.tex](main.tex)，数据提取为 [evidence_snapshot.json](data/evidence_snapshot.json)。这里区分“已有可引用结果”和“完成全量最终验收”；后者仍待宽度队列收束。所有百分比的正号表示CPD降低，负号表示退化。

路径约定：`B=results/architecture_flow_20261027/serial_strict_reexecution_20261103`；`S=vendor/vtr-architecture-src/vpr/src/route`。完整源文件SHA256收录在数据快照。算法文件和实验文件均只读。

| ID | 允许写入论文的主张 | 代码实现或统计入口 | 实验来源 | 覆盖范围 | 限制与禁止延伸 |
| --- | --- | --- | --- | --- | --- |
| C01 | R1以真实有向图可达性约束跨层候选 | `S/h3d_fast_plan.cpp` 构造、feasible_、plan；`S/h3d_crossing.h` | 源码；B内图导入及独立路由审计 | 两层、串行、clustered，当前为edge编码 | 单次跨层walk可行性不等于无拥塞、包围盒内或全局最优；不同编码不能混算 |
| C02 | 共享/拆分DP求解固定层次和候选表下的代理目标 | `S/h3d_partition_dp.h:solve_partition`；`h3d_fast_plan.cpp` 的 pooled table | 源码；历史有限枚举验证，最终验收需绑定其实际版本 | 指定层次分割和候选表 | 不宣称原创DP、全图Steiner最优或H3D原算法；开启成本按层次组计 |
| C03 | 主配置首次规划后static复用，通过软偏好引导详细路由 | `S/h3d_routing.cpp:plan`、`connection_router.tpp`、`route_net.tpp` | B/selected_configs.json；逐运行环境及H3D日志 | 所有正式选中配置 | 软引导保留资源；static早期关键度可能过时；零fallback不证明优化有效 |
| C04 | 双基线共同完整集合上的平均效果有正有负 | 冻结 `execution_scripts/analyze_flatland_evaluation.py` 及其statistics模块 | B/evaluation_analysis/summary.json；快照panels | 每面板14电路×3种子；共同完整只有2–4电路 | SB/P0 −0.6385%；SB/P1 +0.4105%；CB-O均0；Hybrid/P0 +1.3169%、P1 +1.0772%；不得称全套平均 |
| C05 | 最大同样本改善12.9592%（相对匹配2D为10.5379%） | 双基线同样本计算 | small CLSTM/seed23/Hybrid-O/P0的A0、R1和matched2d结果 | 一个明确样本；6.22150 vs 7.14780/6.95434 ns | 不代替平均、不从最大值推显著性、不用不同样本凑括号 |
| C06 | 同架构同布局也会退化 | 同一输入配对及最终STA | large CLSTM/seed23/Hybrid-O/P0；7.07372→7.88347 ns | 一个退化11.4473%的案例；主表另含所有win/tie/loss | 不能删去退化或用更好seed替换；SB/P0 robot_rl更有13.30%退化 |
| C07 | 正式串行计时没有总体加速证据 | B/execution_scripts内串行执行与分析；seccomp线程约束 | B/serial_analysis/summary.json，36次登记重复、180个受审计进程区间；本轮重新核对启动记录和区间 | 12组中10组各3次合法重复；spmv和robot_rl；A0/B2/R1off均保留 | 10组R1/A0及R1/R1off都更慢；对B2仅1组router、2组process更快；范围见comparison_contracts.md；共享主机不独占 |
| C08 | 改善案例发生了最终资源与最差路径变化 | 独立physical_metrics；report_timing.setup.rpt | small CLSTM四类凭据：manifest、pair_check、independent_audit、timing report | SB对53→40、CB源1159→1164；最差路径从乘法器链换为减法器链 | 只有各自最差路径，不能逐边相减或证明某一个crossing的因果作用 |
| C09 | 退化案例不是日志所记录的回退触发所致 | H3D_PLAN、H3D_SCC及最终route audit | large CLSTM对应日志 | no_candidate/fallback/high_fanout均0，规划106.13s，router126.24s | 排除的只是已记录回退；未证明全局根因；可达且合法的引导仍可能更差 |
| C10 | 延迟查询覆盖不足，不能将优势归因于延迟评分 | `S/h3d_delay_plan.cpp`、`h3d_fast_plan.cpp` timed/covered分支 | B/mechanism_attribution_review_20261106.json；快照mechanisms、diagnostics | small 2/530、large 2/1233完全评分；两例808/1778次查询均触顶 | truncated仍可能有有效settled结果；部分源成本能影响fallback项；不是“延迟项没有作用”的证明 |
| C11 | 现有G/D/C/D+C消融比较评分方法，尚未隔离DP贡献 | 同一static模式及DP调用；`h3d_routing.cpp`缓存条件 | B/benchmark_protocol.json、selected_configs.json、evaluation_analysis/summary.json | 固定config0和每变体8配置训练；P1/seed21 | candidates模式同时改变缓存频率并保留top-K，不是独立top-1+同缓存控制 |
| C12 | 布局敏感性与路由收益须分别解释 | 冻结balance runner；独立hypergraph weight audit | B/balance_analysis/summary.json；48布局案例、144路由角色 | 130合法/12失败/2超时；每split仅2电路 | 参数0.03 vs 1.5；不能误写3.0；Hybrid W100路由比改善同时总CPD变差 |
| C13 | 现代LaZagna有受控结果，论文时期结果仍只能作外部参照 | B2固定5abd3aca；A0固定0b912334派生；兼容性桥接 | B的B2结果；历史 `results/three_baselines_20261027/published_reference.json` | B2各面板2–8完整电路；B1表IV作者2D分母 | B2结果是工具差异；B1的0.821/0.819/0.809不能与本地R1/A0相减 |
| C14 | 没有观察到算法引起的严格架构排序反转 | evaluation analyzer architecture_rankings；独立角色表重算 `audit_ranking_seeds.py` | B/evaluation_analysis/role_observations.json及summary.json；[逐seed复核](data/ranking_seed_audit.json) | 共同完整集合只有conv_layer_hls；三seed均值四组合CB-O＜SB＜Hybrid-O；逐seed及A0/R1的84项数值检查通过 | P1 seed21为SB第一、seed25为Hybrid-O第一，排序随seed变化；不能推广最强架构；排序反转不是结束条件 |
| C15 | 失败、超时和重复角色已显式保留 | role_observations、registered jobs与unique-run去重 | B/evaluation_analysis/role_observations.json | 完成评估全部1206角色：581合法/455失败/170超时；1136唯一路由尝试 | 含消融与转移W300，不等于单独主测试；failed可能包括无上游布局；唯一运行不等于独立样本 |
| C16 | 固定布局宽度诊断用于检验条件敏感性 | B/execution_scripts/run_paired_width_diagnostic.py及已登记分析器 | B/paired_width_diagnostic_protocol.json、jobs.json、已完成case凭据 | 24案例/144角色：125合法、13失败、6超时；R1交互19完整/5缺失，5低于1、11等于1、3高于1 | 每split仅两电路单seed；宽度同时改变图和拥塞，不能归因历史差异 |
| C17 | 平均最终连接开关延迟降低可以与CPD恶化并存 | `scripts/check_route.py` 的routed_sink_delay_ns；独立论文解析器analyze_connection_changes.py | 四份原route与audit；data/connection_changes.json | large跨层10863条，均值降低2.6906%，但CPD退化11.4473%；small3902条均值降低1.6510% | 逐连接终端身份已核对；仅零RC开关和、不含局部逻辑；不是DP独立因果或最终guide采用率 |

## 统计口径

同一电路先平均三种子的绝对CPD，再对电路比值取几何均值。双基线括号两项使用同一共同完整电路集合；现代LaZagna单独列集合。表中的种子级win/tie/loss可以覆盖更多合法样本，不能误当均值的分母。资源审计区分SB半节点对、CB输出源和边遍历，不宣称等面积/等via预算。

补充物理核对覆盖10套模型、40图的既有清单；2D平面线资源相对3D的残余差异为−0.1770%至+1.8703%，逻辑容量按登记公式一致。552个合法执行的布局坐标和输入凭据已直接核对。大图与packed文件内容重哈希、完整逐pin出口及层方向统计仍未完成，详见[comparison_contracts.md](comparison_contracts.md)。

## 本稿明确不支持的句子

“总体加速”“普遍优于VTR9/LaZagna”“证明混合架构全面最优”“架构排名反转”“DP独立贡献已被消融证实”“delay模式说明延迟估计导致12.96%收益”“55%的最终连接采用规划资源”均不可使用。最后一个比例来自累计路由事件，不是最终路径匹配。
