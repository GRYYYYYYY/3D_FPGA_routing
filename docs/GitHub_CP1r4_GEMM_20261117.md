# 实际slack故障核验、CP1r4冻结与GEMM匹配确认启动

## 已闭合的真实诊断

两臂SB-layout原TypeError的实际donor2274/pin1都为字符串"+inf"，cutoff为−6.1216711699785264e−9秒。在原实际donor集合上，原表达式重现str>float TypeError；按浮点数解释后原严格比较成立。并非推测token，也未扩大时序容差。

隔离数值修复的两个完整规划器回放均通过，非规划器输入及其实际字节摘要与原失败阶段逐项相同。两臂都形成5连接提案，当前路径代理最小增益0.185825799ns；未执行这些连接的原生事务，没有候选合法性、最终CPD或完整方法收益。完整诊断实测8.218278秒，内部8.113672秒与逐臂4.071645/4.031256秒嵌套。首次诊断因新增观测钩子误进入生成器作用域而失败，10.608246秒及原失败均保留；测量进程结束不等于核验通过。[实际token与回放](../research/dac_v14_20261112/planner_numeric_slack_replay_02/STATUS.md)。

## 新版本固定及独立重建

CP1r4是独立后继，父CP1r3及原确认失败不改。运行代码只改planner的slack数值比较/排序；artifact manifest同步更新。物理Tdel、原生搜索/顺序、固定根预算、共享域、failure-release、owner、整组接受、终结规则及阶段保护保持。不加入跨层代价或空查询探索补丁。

新manifest e299054278a4f624f531f7e250f358ee3d04dd0a67a1166944bcfd780c0c06ce。冻结实测5.043296秒，内部4.941523秒嵌套。362734字节source tar和两项固定wheel独立恢复1295项绑定文件；实际保护程序、NumPy2.2.6/lxml6.1.3导入及迁移GEMM配置checker通过。外部物理输入及原生二进制仍须显式提供/绑定；源包恢复不等于新的路由结果。[冻结与重建记录](../research/dac_v14_20261112/confirmation_release_cp1r4_01/STATUS.md) · [源包](../research/dac_v14_20261112/confirmation_release_cp1r4_01/current_sta_cp1r4_source.tar.gz) · [恢复器](../research/dac_v14_20261112/restore_confirmation_cp1r4_dependencies.py)。

## GEMM一输入两角色实际启动

沿用已登记候选GEMM-p0：与此前矩阵/CP1r3不同电路的已知历史训练来源，同两层edge-encoded Hybrid-O架构族。五项原输入约13.22GiB实际字节/38567-block坐标预检17.272952秒通过；新私有输入复制、复核与checker56.263702秒另记。固定packing/placement，seed11与constant-merge off取自实际来源；不导入历史route。两臂是一个物理输入，不计两个独立样本，不称未见输入/新架构，没有应用SDC主张。

配置激活及源包恢复内部5.261965秒；之后native真实启动，domain按固定登记顺序随后执行。单臂完整计时覆盖准入、索引、新鲜路由、资源/owner/终结/时序、拒绝、恢复和检查；输入准备、依赖重建及独立研究核验费用单列，不能拼接成完整算法时间。当前发布快照仍处native初始路由/资源流程，尚无完整方法质量或正式配对比例；实际过程证据见[运行观察](../research/dac_v14_20261112/cp1r4_gemm_pair_01/running_observation_01/checkpoint.json)、[固定计划](../research/dac_v14_20261112/cp1r4_gemm_pair_01/plan.json)及[当前状态](../research/dac_v14_20261112/CURRENT_STATUS.md)。

当前登记剩余2角色，已完成输入准备56.26秒；GEMM暂无同电路完整执行样本，不能用BNN耗时或1800秒阶段保护估算整臂ETA。若初始失败/超时，保留实际费用而不填QoR；若通过，后续时长取决于真实候选、容量阻塞和接受。只有来源、实际字节、完整请求、FULL、STA、整向量/端点及物理审计通过的完整配对才进入论文收益。所有无切口、无收益、退化和失败均保留，不按结果替换或扩矩阵。

## 论文与历史证据边界

[六页投稿05](../research/dac_v14_20261112/submission_narrative_05/build/main.pdf)和其方法、prior-art、BNN完整+24.91%费用、表I负结果及四档代价表III均不变。此次只补软件故障解释、可独立执行版本及后续输入来源；CP1r3仍无新增完整准入配对。05稿原影响清单是当时冻结快照，本记录更新其中“实际token/完整planner未回放”一项为已完成诊断，不追认原失败或生成算法收益。GEMM完整通过后只更新对应主表/适用性及必要摘要/结论。

CLSTM23连接来源审计、原四臂及robot-p1历史恢复保留；尚缺候选物理/domain/STA或完整配对的阶段继续按单项缺口处理，不作为本稿统一前置条件。9734eee和279bdb4公开祖先、本地更新与原冻结规则保留；Goal不因推送、队列、普通负结果或日期/次数结束。
