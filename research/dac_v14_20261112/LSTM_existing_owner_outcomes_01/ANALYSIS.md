# LSTM 已执行 owner 候选：容量见证与预算结果

两臂在各自不同中间状态均有 5 个受支持容量切口、40 个通过余量筛选的 owner 组；原计划各执行前三组，三组均被资源策略拒绝。它们不是同一起点的 owner 因果配对，也不能推出其余37组无效。

| 臂 | rank | 相对自身事务前线长/SB/CB | 原资源策略 | 原因 |
|---|---:|---|---|---|
| native | 0 | 0/1/1 | 拒绝 | Fixed registered resource budget exceeded |
| native | 1 | -40/0/0 | 拒绝 | No resource Pareto improvement within fixed CPD budget |
| native | 2 | 12/0/0 | 拒绝 | No resource Pareto improvement within fixed CPD budget |
| domain | 0 | -8/1/1 | 拒绝 | Fixed registered resource budget exceeded |
| domain | 1 | -36/0/0 | 拒绝 | No resource Pareto improvement within fixed CPD budget |
| domain | 2 | 12/0/0 | 拒绝 | No resource Pareto improvement within fixed CPD budget |

rank 1 已有原始 FULL、STA、物理、请求及端点只读证明，满足已登记绝对资源和 CPD 上限；原控制器因 SB/CB 无改善而拒绝。对比各自已准入最终终点：
- native：候选 2388043/492/8316，最终 2388083/492/8316；CPD 相同，setup 相对最终改善 0、退化 1，新增 hold 违例 0。
- domain：候选 2390246/422/8316，最终 2390270/422/8316；CPD 相同，setup 相对最终改善 0、退化 2，新增 hold 违例 0。

这些候选是已拒绝的局部替代工作点，不是完整控制器选出结果，也不改写原判定；短线长与端点退化共同保留。此分析不执行新 native、STA 或路由查询，不拼接完整费用，不改变已冻结的确认规则或论文收益。
