# 补齐完整 BNN domain 工程对照（2026-11-16）

公开证据基点仍为 `9734eee`，承接 `e755f38`。本次只补登记先前缺失的工程臂，没有新增实验结果；本地运行和排队版本保持不变。

## 缺口与固定干预

已完成的原完整 BNN 配对为 native 7933.25 s、domain 9754.31 s，CPD 同为 13.228145690 ns；domain 用 1786 wire 换取 39 SB、2 CB，完整时间增加约22.95%。SB 从82到43减少47.56%；SB＋CB从5144到5103减少约0.797%。这些是固定架构资源占用，不是面积或功耗测量。

单遍索引以及同流程缓存／stream 优化此前只有完整 native 实测。新增 [domain 工程臂](../research/dac_v14_20261112/complete_BNN_domain_engineering_01/plan.json)复用 stream-native 的同一实现，仅将 `domain_mode/domain_feedback` 恢复为原 domain 配置。原物理输入、三个阶段二进制、seed11、8次收敛机会、1.01阈值、当前 STA 选组、接受与终结规则不变。没有增加 terminal-wire、owner 或查询分组策略。

从给定架构、图、网表、packing和placement重新构建索引、生成初始路由，并在同一测量命令内完成资源与时序阶段。历史候选、路由和查询结果不作为输入。全流程观察者记录时间、RSS/PSS及缺失观测；失败和退化保留。

## 实际登记与比较条件

[预检](../research/dac_v14_20261112/complete_BNN_domain_engineering_01/preflight.json)确认原 domain 算法字段及输入摘要完整继承、与 native 仅有两个处理开关不同，调用 VPR 为0。大型输入重新哈希在串行槽内进行，预检不冒充完整运行。

[唯一队列](../research/dac_v14_20261112/complete_BNN_domain_engineering_01/queue/registration.json)等待原 robot p1 完整配对结束，随后取得现有串行锁。attention/robot-SDC、独立接口和完整方法检查、clstm、robot owner 范围对照、robot p1 的原优先顺序均保留。首次启动时虚拟环境链接被解析成系统 Python，已在无子进程、无测量目录、0原生调用时更正；[启动回执](../research/dac_v14_20261112/complete_BNN_domain_engineering_01/launch_reconciliation.json)保留原登记，不改变已封存实验规则。

完成后复用完整轨迹比较器，核对原 domain 的所有实际源、候选、交接、终态、完整端点向量、请求、域、原生重试／堆操作及图载荷。只有等价时才给出同角色历史费用差；差异和失败仍进入结果。另存完整端点变化，与旧 native/domain 的比较明确标注历史参照。

已完成 native 不重跑。它约7247 s的GNU-time限定、观察者丢失、PSS缺口和短暂并发仍然成立。本次单臂观察不构成新的干净 optimized native/domain 比率，不替换历史22.95%，不证明统计加速。稳定版本的同环境交错计时仍待执行。

## 科学结论与正文边界

统一方法仍为当前 STA 选组、共享域、按网络失败释放、容量／余量驱动 owner 协调、完整事务接受及独立终结选点。固定 dev03 的完整运行和跨输入验证仍在原队列中；没有新增独立结果，也尚未冻结确认版。

最近完成的三网络组合和 robot 无释放失败已进入[六页正文及统一主表](GitHub_native_ablation_progress_20261116.md)：前者支持组合可实现性，后者支持释放的操作作用，均不代表完整算法的普遍收益。新登记尚无结果，不新增正文主张或表格数值。原失败、无切口、无收益和退化案例继续保留。Goal 继续，不以推送、日期或矩阵完成结束。
