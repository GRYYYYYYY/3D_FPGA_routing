# 完整 BNN terminal-wire 配置已核验，历史匹配比较待完成

记录时间：2026-11-16T03:01:39.674612+00:00。公开证据基点仍为 `9734eee`，研究继续；本次不冻结统一确认版，也不恢复日期、总调用数或矩阵停止条件。

## 已完成的完整配置

从登记架构、RRG、BLIF、packed netlist 和 placement 开始，本次命令内重新路由、生成图索引，完成资源修复、独立终结选点、当前 STA 时序修复。完整配置验证通过，资源阶段8个实际事务中接受5步，终结选点采用1次，时序阶段3个候选全部接受；最终在当前菜单中没有可接受候选后正常结束。

| 同一次执行的指标 | 实际结果 |
|---|---:|
| CPD/ns | 13.228145690 |
| 线长 | 2059607 |
| SB / CB | 82 / 5062 |
| 端到端观察者时间/s | 7351.260476 |
| 采样进程树 PSS 峰值/GiB | 11.063048 |
| 内存缺失观察次数 | 24 |

[完整配置验证](../research/dac_v14_20261112/complete_BNN_terminal_wire_flow_01/bnn_native_terminal_wire/completion.json)、[完整流程终结](../research/dac_v14_20261112/complete_BNN_terminal_wire_flow_01/bnn_native_terminal_wire/flow/completion.json)、[同次测量](../research/dac_v14_20261112/complete_BNN_terminal_wire_flow_01/bnn_native_terminal_wire/measurement/completion.json)、[原 GNU-time](../research/dac_v14_20261112/complete_BNN_terminal_wire_flow_01/bnn_native_terminal_wire/measurement/gnu_time.txt)绑定同一输出。命令退出码为0、没有残留子进程。采样可能漏掉瞬态峰值，24次内存缺失不补造；页面缓存和共享主机环境未受控。本次单次描述性时间不能作为统计加速结论。图生成输入、packing/placement生成与源码编译属于上游，不计入所定义的路由命令时间。

## 机制证据及比较边界

独立终结选点从资源阶段已验证候选中选出更短线长状态：2059591→2059567，SB/CB不变，setup 2项改善、0项退化；新 FULL/STA 交接通过，之后重新执行完整时序阶段。三个时序步骤相对各自前态的 setup 改善/退化分别为10/17、11/0、1/1，均无新增 hold 违例；这些逐步计数不能相加当作最终基线比较。

第三步为原生臂的 owner 交换候选，CPD 13.413972155→13.228145690 ns、线长+4。这不是域限制收益。第二步包含两个连接局部延迟增加，但整体 setup 11项改善、0项退化，说明需要按完整合法事务进行 STA 验收，不能要求每个中间连接单独改善。

当前最终标量与先前固定三网络组合验证的工作点一致，但不能据此推断路线、完整端点向量或共同前缀完全等价。[已登记的限定比较器](../research/dac_v14_20261112/BNN_terminal_wire_qualified_comparison_02/plan.json)等待串行空位，负责核对共同资源前缀、最终完整端点和 GNU-time 同口径费用。该比较尚未完成，本次不报告相对基线的最终端点收益、额外时间比例或单改动因果收益。旧 native 观察者丢失、PSS 缺口及短暂并发限定仍保留。

本次是同一历史 BNN 物理输入上的完整 terminal-wire 原生配置，不是新增独立输入，也不是完整统一 dev03 的确认结果。原 BNN native/domain 对照仍分别报告 SB减少47.56%、SB+CB总数减少约0.797%、完整时间增加约22.95%；本次不同配置不替换这些原匹配结论。

## 接续与论文

恢复队列已正常终结，未重复 BNN固定组合、robot无释放消融或已完成 native 批次。原 attention/robot-SDC 配对已自动接续；独立可执行版本检查、clstm、robot owner范围对照、robot p1配对和缺失domain工程臂沿原登记顺序推进。已完成结果和普通负结果继续保留。原生流程测量期间不并行执行重型只读比较。

统一方法仍是当前STA选组→共享域→按网络失败释放→容量与余量驱动的owner协调→固定根约束下完整事务接受→独立终结选点→完整时序修复。dev03实际整流程检查、冻结确认和跨输入证据仍待完成。

[六页正文](../research/dac_v14_20261112/paper_snapshots/current_native_ablation_20261116/build/current_repair_main.pdf)仍为已核验的版本06：22个完整流程条目与2个明确范围的组合/消融条目。本次完整结果先单独公开；待匹配比较回执齐备后再整合主表及主张，历史逐步轨迹留在补充材料。现有671条历史档案与34个完整质量配置的计数尚未因本次结果重建，不混作独立样本数。
