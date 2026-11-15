# 2026-11-15 研究进展快照

本快照延续 `research/dac-snapshot-20261113`，父提交为 `7b2834743007b36ce5890320e15a0ffa7dea1eb3`。研究仍在进行。精确采集时刻、终结回执、PID/start_ticks 身份核对及文件哈希见[发布时机器状态](github_progress_status_20261115.json)。旧日志中的 running 字样不能替代实际回执。

[当前 C221 六页 PDF](../research/dac_v14_20261112/paper_snapshots/current_R1_native_closure_20261115/build/current_repair_main.pdf) · [正文源码](../research/dac_v14_20261112/paper/current_repair_main.tex) · [源码/图/PDF绑定](../research/dac_v14_20261112/R1_native_closure_paper_binding_01.json) · [版面检查](../research/dac_v14_20261112/paper/current_visual_review_C221.json)。正文已整合 R1/Tf 原生菜单闭合，绑定578条观测。其后完成的迁移、两连接与工程对照由本说明及各批次回执单独更新，尚未全部合入六页正文。

最新具名验证档案为[592条合法观测](../research/dac_v14_20261112/multiobjective_partial_owner_01/verification.json)，包含26个成功完整配置、5个成功电路身份和3类垂直架构。该计数只属于此档案；后续独立完成的费用03、组合工程等批次仍有单独报告，不能猜测相加为全局观测数。观测、同根重复和阶段状态不等于独立测试样本。失败、合法拒绝和被支配点均保留。

## 完整 BNN 质量—费用对照

| 实际完整命令 | CPD/ns | wire/SB/CB | 完整秒 |
|---|---:|---:|---:|
| cold native |13.228145690|2059631/82/5062|7933.25|
| cold domain-first |13.228145690|2061417/43/5060|9754.31|
| native 单遍三索引 |13.228145690|2059631/82/5062|7463.17|

[原冷启动配对](../research/dac_v14_20261112/complete_resource_timing_full_flow_01/comparison.json)的初始有序路由和完整端点向量精确相同。domain-first增加1786 wire、1821.07秒，减少39 SB、2 CB；最终 setup 534改善/803退化，无新增hold违例。这是组合策略不同实际工作量的取舍。43 SB/5060 CB达到固定终端总垂直下界5103，不证明wire或CPD最优。

旧导入 native/domain 点为2059627/2061389 wire，比对应冷启动最终态少4/28 wire，但历史完整费用未知；没有给旧质量套新时间。原计时内构建的图载荷与实际使用的旧元数据别名字节精确，旧目录仍是额外静态依赖，见[缓存边界](../research/dac_v14_20261112/BNN_complete_cache_boundary_01/completion.json)。没有导入历史route/candidate/query结果。

[单遍索引完整验证](../research/dac_v14_20261112/complete_BNN_joint_index_flow_01/comparison.json)现已终结：实际7463.174179秒，相对7933.245509秒少470.071330秒，即本次观测5.93%。图载荷及下游所有实际状态、请求、原生协议/工作核验一致，最终质量不变。此处报告实测整条时间，未用此前405.86秒组件时间推算。共享主机、OS页缓存及不同时段执行不受控，只有各版本一次观测，不是统计加速结论。实际PSS约11.06GiB，缺失采样数与GNU进程高水位分别保留在原回执。

## 原生对照闭合与 owner 协调

[原定8个root/control菜单](../research/dac_v14_20261112/closed_seed_transfer_eight_roles_01.json)全部闭合，匹配原始根、CPD/资源帽、K8、seed及排名规则，各分支从自身当前状态重选机会。

| BNN 起点/干预 | CPD/ns | wire/SB/CB | 解释 |
|---|---:|---:|---|
| R1 own-current native |13.421610490|2068956/71/5072|4接受/7scope |
| R1 own-current guided |13.421610490|2070629/33/5071|相对native用1673 wire换38 SB/1 CB |
| R1五连接 owner 联合修复，两域对照 |13.421610490|2070653/32/5071|+24 wire/−1 SB，完整端点向量不变 |
| R1两连接 native/retained-CB 与BFS候选 |13.421610490|2070657/32/5071|三角色均合法；比五连接点多4 wire |
| Tf own-current native |13.421610490|2074388/74/5062|11接受/14scope |
| Tf own-current guided |13.421610490|2076038/43/5060|相对native用1650 wire换31 SB/2 CB |

R1/Tf native恢复段分别为548.22/1707.77秒；历史整条费用未知，不拼接为完整算法时间。恢复复用已完成的检查点/实际worker，未重复原rank0/1搜索或Tf运行，也未制造旧pool终封。R1新两候选实际加入档案，最终检查点按既有记录引用，没有重复增加观察。

[R1局部最小值证书](../research/dac_v14_20261112/R1_single_net_vertical_local_minimum_01/completion.json)说明固定其他网时，8个同层出口全部被其他owner占满，单网重布线不能严格降低当前总5104垂直资源。[五连接实际验证](../research/dac_v14_20261112/multiobjective_R1_joint_owner_escape_01/verification.json)确认RR3507189从owner62707交给目标31767，固定sinks和完整时序向量不变，实际达到总5103下界；新点非支配。自由native和目标CB域得到同一最终树，因此本scope的收益来自扩大owner协调作用域，不能归给额外域约束。

[两连接三角色](../research/dac_v14_20261112/partial_escape_owner_intervention_01/verification.json)均通过各自FULL/freshSTA与完整物理审查，说明更小的两连接scope也足够；三点被已知少4 wire的五连接点质量支配，仍保留。两连接native搜索为2 queries/4 attempts，五连接为5/9，但交易core约13.58/13.69秒对13.40/14.19秒，本次没有减少查询数即更快的证据。共享双臂/三角色事务费用不是每臂或完整算法时间。BFS使用不同构造和LOAD二进制，不能作为单因素域对照。[事前五连接延迟预测](../research/dac_v14_20261112/R1_BFS_native_timing_prediction_01/analysis/completion.json)与该BFS实际native延迟精确一致，模型没有替代FULL/STA或控制原冻结接受规则。

## 新迁移：收益与失败都保留

[四角色固定策略迁移](../research/dac_v14_20261112/complete_serial_additional_circuits_01/comparison.json)已全部终结，2成功/2失败；是两个已知历史电路，不采用旧目录名中的heldout作为本次独立测试标签。

| 电路/角色 | CPD/ns | wire/SB/CB | 完整秒/失败秒 |
|---|---:|---:|---:|
| robot_rl native |13.354624073|251116/9/653|377.71 |
| robot_rl domain-first |13.354624073|251136/9/652|424.45 |
| conv_layer native |—|无合法质量|260.10，初始路由失败 |
| conv_layer domain-first |—|无合法质量|254.57，初始路由失败 |

robot_rl初始route/完整端点向量精确相同，domain以20 wire和46.74秒换1 CB。其首次同源事务具有相同request/cuts/weights/order/binary，[实际网络分析](../research/dac_v14_20261112/robot_domain_first_scope_analysis_02/completion.json)定位CB节省在仍受域限制的net3140；net3454/3438则在搜索失败后各释放一次域，以完成组合。全部domain执行共5次释放/5个native事务，native控制为4事务；后续轨迹机会不同，不作等计算量或纯release归因。

conv_layer两个角色在登记的200次路由迭代内未建立合法初态，因此没有测试后续资源修复；保留失败费用和分母，失败CPD/wire计数不进入合法档案。这不是数学不可路由证明。[迁移档案验证](../research/dac_v14_20261112/multiobjective_additional_circuits_01/verification.json)检查11个实际机器人初态/候选及仅最终态携带自身整条费用。

## 后续已终结的算法及开销对照

- [连接预算64四角色](../research/dac_v14_20261112/connection_budget_resource_dev_02/queue/results.json)：eltwise native/domain为217050/26/968与217183/24/965，CPD6.018101129ns；BNN native为2059591/82/5062，domain为2061423/43/5060，CPD13.607436067ns。BNN domain有16接受，完整导入执行段10568.53秒；比原K8 fixed-seed domain2061377 wire多46 wire，相同CPD/SB/CB。单scope预算减少连接没有保证整条算法更优，原强基线和该负结果均保留；这些不是cold完整费用或同期统计速度对照。
- [direct strict与vector→strict](../research/dac_v14_20261112/vector_then_strict_comparison_04/queue/results.json)：两分支各3次strict接受，均13.228145690ns、45 SB/5060 CB，wire分别2061301/2061293；两阶段点少8 wire。实际新strict阶段进程费用2435.36/2472.68秒；vector前缀带来额外机会，其历史完整总成本未知，不能称等计算量或整条更快。
- [完整费用03](../research/dac_v14_20261112/complete_route_resource_measurements_03/queue/completion.json)：四个eltwise配置均合法，native/domain各自最终质量在建索引/复用索引模式间精确一致。计时内建索引227.95/228.09秒，明确复用图状态160.57/165.71秒，属于不同缓存边界；tiny校验34.43秒单独列出。各模式只有一次共享主机观测。
- [source-snapshot＋lazy完整组合](../research/dac_v14_20261112/complete_serial_lazy_source_snapshot_01/comparison.json)：eltwise198.88秒、softmax256.54秒，相对各自原lazy203.48/271.70秒；所有实际初态/候选/最终向量和有序树、请求、接受/跳过决定与native工作量一致。费用来自本次完整组合命令，没有把两个历史组件时间相减拼接。
- [统一终结选点两模式](../research/dac_v14_20261112/terminal_timing_envelope_policy_01/verification.json)：13个实际闭合菜单×2模式、零新增native/合法观测；5个旧endpoint规则菜单完全复现。固定CPD/hold预算模式在Tf native菜单选择已存在的2074308/74/5062点，比被选终态少80 wire，但setup19改善/4退化；完整端点不退化模式拒绝它。[新增robot两个菜单](../research/dac_v14_20261112/robot_terminal_wire_transfer_01/completion.json)两模式都没有合格替代，不宣称普遍收益。

## 正在运行、排队和开发中的工作

精确身份与阶段以[机器快照](github_progress_status_20261115.json)为准。发布采集时：

1. [显式同流程缓存路径＋现有流式v2完整BNN对照](../research/dac_v14_20261112/complete_BNN_closed_stream_flow_01/plan.json)已开始运行。验证实际缓存消费者都在计时命令内、保持所有原生/FULLSTA/物理/接受门；与已完成单遍索引及原cold基线比较实际完整费用，尚无最终结果。
2. [BNN终态wire替代与时序组合的单候选LOAD](../research/dac_v14_20261112/BNN_wire_timing_native_validation_01/plan.json)排队等待上述工程对照。结构2059607 wire/82 SB/5062 CB及34连接模型不能代替实际FULL/STA，尚不记为合法质量或完整算法结果。
3. [robot单独关闭failure-release的同源消融](../research/dac_v14_20261112/robot_domain_release_ablation_01/plan.json)已登记，在原BNN组合LOAD之后排队；保留首次实际source、23连接/四网请求、权重/顺序、域及二进制，只关闭release标志。它未运行，不预判成功或失败。
4. “资源终结wire选择→当前STA时序”完整新流程已开始实现，driver/verifier/前缀比较代码与真实正/零候选handoff检查保留；**尚无登记的完整实验批次，也没有运行结果**。它不同于上述已登记的一候选结构组合LOAD。

## 复核与公开范围

- [当前论文独立复核脚本](../research/dac_v14_20261112/verify_R1_native_closure_paper_artifacts_v1.py)核对6页、源码/图/PDF、578条正文档案和claim lineage。原始输入和大量FULL/STA/路由证据在服务器，完整验证需要原始环境与对应数据；GitHub快照本身不是脱离原环境即可执行的全量原始数据包。
- [新增两个VPR私有变体导出](../patches/snapshot_20261115_verified/manifest.json)建立在已验证Census源码补丁上，保留实际构建TU/header与二进制哈希。portable crossing-source overlay只规范化一处机器绝对include路径；补丁回放验证通过，没有重编译或声称bitwise复现二进制。
- 发布包含研究实现、协议/配置、选定JSON/CSV证据、失败与恢复记录、源码补丁、当前及历史论文快照。大体积RRG、route/net/place、全量STA导出、图缓存、构建产物和二进制不上传，继续由服务器保存；具体取舍及哈希见本次snapshot manifest。
- 活动批次的文件按各文件稳定读取时刻冻结，不是一次新的算法终封；发布不会重启、终止或修改原实验规则。固定器件资源占用不等于芯片面积/功率收益；当前结果不支持统计速度、任意多层/CHANZ或独立未见电路的普遍结论。
