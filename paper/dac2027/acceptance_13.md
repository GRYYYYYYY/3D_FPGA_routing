# 原13项要求的收尾核查

唯一原始范围：`results/architecture_flow_20261027/requirements.json` 的13个 acceptance 键。以下是2026-11-10北京时间收尾时的逐项证据评估，**不等于13项全部无条件通过**。原文件的旧进度字段不用于判定完成，也不在论文工作中修改。B为严格重执行目录，A为其上级 `results/architecture_flow_20261027`。

新增只读复核已匹配11,061份小文件/执行文件摘要，核对1,136个独立evaluation运行的分类和已记录线程凭据，并确认594次训练分母及选参先于heldout执行。此前延期的3,183份大文件已全部重算摘要，0份失败；两者合计14,244个独立inode，但范围仅为已登记的七份旧阶段绑定清单，不包含宽度阶段，不等于全仓库或语义审计。详细范围见[evidence_audit.md](evidence_audit.md)。

进一步的[比较口径核验](comparison_contracts.md)完成987项检查：10套模型/40图的既有物理清单、552个合法运行的配对输入凭据、180个串行计时进程的记录和区间。该核验发现原物理审计没有完整逐pin出口/层方向统计；此项仍明确标为部分满足，不以其他检查通过替代。

宽度诊断另完成[144个角色的配对凭据复核](data/width_pair_audit.json)：每个角色的私有、共享及已封存输入摘要一致，125完成、13失败、6超时；此检查不重读全部宽度图文件或重跑语义验证。

| 原要求 | 已存在的直接证据 | 当前判定 | 尚需完成或明确保留的限制 |
| --- | --- | --- | --- |
| provenance | B/execution_contract.json、runtime_dependency_binding.json、preparation_registration.json；本轮toolchain_provenance及实际P1补丁回执 | 已核对实际源码角色/补丁/编译规则、程序及已登记文件摘要；可复现性部分满足 | 不宣称干净环境位级重建；A0子模块差异、P1无.git/缺两个关闭功能构建文件、bridge绝对路径及动态加载范围均披露；上游普查无本轮线程trace |
| physical_audit | A/benchmark_models各模型manifest、B/capacity_selection.json、所绑定graph_audits_v2 | 40图既有容量/资源/时延清单已复核，登记旧阶段大文件摘要匹配；部分满足 | 缺完整逐pin出口与层方向统计；共同平面不证明等面积/功耗/via预算 |
| compatibility | B/evaluation_analysis/input_bindings.json；各合法run pair_check及独立审计；原graph schema比较回执 | 552个合法执行及144宽度角色的配对输入凭据已核对；登记旧阶段大文件摘要匹配 | 不是本轮重跑完整checker；宽度阶段采用原输入封存和配对摘要凭据；不以verify_file_digests=off代替证明 |
| dual_baseline | B/evaluation_analysis/summary.json的routing_dual；已有matched2d run | 计算已完成，引用范围明确 | 只有2–4/14电路进入各完整双基线均值；2D失败不能用CPD；禁止全套均值措辞 |
| placement_routing | 168主案例结果、evaluation_jobs及role_observations，P0/P1×A0/R1/B2 | 登记主测试已终结，含失败 | 保持路由内配对；分开P1/P0效应与组合效应；P1 repack成本不同 |
| hyperparameters | 594次训练登记、training_analysis、selected_configs及时间戳 | 已核对594次分母、冻结先于heldout以及登记旧阶段文件摘要 | 6/14电路和11/21,23,25种子分离；历史已见电路与受ptrace影响的tie-break须披露 |
| ablations | evaluation_analysis中fixed/tuned G/D/C/D+C及失败覆盖 | 原评分消融已完成；DP独立归因未满足 | 四组均含DP；本轮只交付同缓存top-1对照设计，不自动新增实验；限制写入正文 |
| architecture_ranking | 全局共同完整集合、absolute CPD/common2d、by_seed、reversal记录；[逐seed角色表独立重算](data/ranking_seed_audit.json) | 14电路中共同完整仅conv_layer_hls；84项逐seed与汇总值复核通过；允许无反转 | P1 seed21的SB和seed25的Hybrid-O分别第一；两者在A0/R1均相同；排序不稳定，不能推广架构最优或反转 |
| external_baselines | B2正式结果、固定port提交；原LaZagna表IV与作者2D分母；A0固定native提交 | 三基线已区分，直接B1比值不可建立 | B/published_reference_analysis是Flatland作者CSV再分析，**不是原LaZagna表IV**；不得混淆；论文B1用A之外three_baselines目录来源 |
| timing | B/serial_analysis/summary.json、36重复及180进程区间无study重叠审计 | 已直接重核180个进程的guard/启动记录、跨重复布局及无登记study重叠 | 10有效组相对A0和R1-off都更慢；B2有局部更快；2组缺失；共享主机不独占 |
| validation | 每合法route的FULL与independent_audit、thread_syscalls/guard证据 | 1,136次执行分类/已有线程凭据与登记旧阶段文件摘要已复核；语义范围部分满足 | 独立审计范围不是完整端点/非配置闭包证明；本轮两例逐连接终端配对不替代全量 |
| closure | 历史/中断/失败记录、阶段注册、分析绑定均保留；本轮独立paper数据快照 | 登记队列及宽度分析终态、收尾报告已同步；证据归档18,884份成员读回核验通过 | 大型原件保留共享盘，归档非完整原始数据副本；不把物理审计、因果消融等缺口标成通过 |
| partition_balance_sensitivity | B/balance_analysis/summary.json；48个balance_audit、144路由角色 | 已执行并有独立平衡审计，登记旧阶段文件摘要已复核 | 0.03臂18/24满足其字面界限，1.5臂24/24；130合法/12失败/2超时；每split仅2电路 |

## paired_width完成后的执行顺序

第1–5步已于2026-11-10完成；宽度分析和输入封存由原协调器执行。归档读回复核回执见 `data/final_archive_verification.json`。第6步按以下范围和残余限制判断，不要求正收益。

1. 确认原协调器和阶段进程终态，核对24个结果与144个登记角色，包括失败/超时/缺失上游。若观测超时而进程仍在，继续复用原handle，不能重启。
2. 等待原协调器运行 `analyze_paired_width_diagnostic.py`，读取其真实输出、输入绑定和配对覆盖，核实同一布局坐标与packed输入跨宽度复用。不要与协调器并行运行分析器或重复提交案例。
3. 只更新独立论文数据快照中的宽度结果和正文对应小节；主测试、串行计时、平衡数据保持其各自来源与集合。完整width interaction缺失就保持缺失。
4. 重新核验全部13项的直接内容与范围。必须使用实际文件摘要、FULL/独立audit、角色映射和线程凭据；不能仅看文件存在或summary写着complete。
5. 在协调器无写入后，以新版本收尾报告/清单同步宽度结果、科学解释、所有未满足项和原因。保留当前预最终report，不覆盖历史封存。归档source/patch/config、登记attempt、失败日志、统计源码和验收记录。
6. 所有登记执行已到终态、分析与证据绑定完成、残余科学问题透明披露且交付物可复核后结束本轮；不以取得正收益、排名反转或“填满”某个比值为条件。

DP独立贡献、最终逐连接guide采用率、校准的硅面积/功耗不是已经测得的事实。若投稿前不补做相应实验，最终验收将保留这些未满足的扩大主张，论文必须维持现有窄范围。本文稿本身已经完整，宽度待更新不使其余章节成为大纲。
