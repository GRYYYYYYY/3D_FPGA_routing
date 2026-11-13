# 独立机制开发集配对结果

Development times only; no ratio to historical timing; formal rotated repeats pending.

每个电路为单seed；无置信区间和盲测外推。合法状态要求FULL和原范围独立审计通过。分母始终包含全部登记电路；未结束/未审计/缺失单列，manifest运行状态需结合实时进程核验。

| 电路 | 臂 | 状态 | CPD(ns) | 迭代 | 规划(s) | 完整进程(s) | SB占用 | CB占用 |
|---|---|---|---:|---:|---:|---:|---:|---:|
| spmv | A0 | legal | 7.0347 | 17 | — | — | 0 | 967 |
| spmv | R1 | legal | 7.04599 | 19 | — | — | 1 | 967 |
| spmv | P | legal | 7.04234 | 17 | — | 18.5513075850904 | 0 | 967 |
| spmv | Ed | legal | 7.0347 | 20 | 18.398655 | 37.785662554204464 | 0 | 967 |
| eltwise_layer | A0 | legal | 9.93208 | 43 | — | — | 127 | 956 |
| eltwise_layer | R1 | legal | 6.96208 | 46 | — | — | 134 | 958 |
| eltwise_layer | P | legal | 6.64602 | 39 | — | 26.970011211931705 | 117 | 965 |
| eltwise_layer | Ed | legal | 7.47203 | 70 | 26.09711 | 56.81838286295533 | 136 | 960 |

R1->Ed (accuracy_or_assignment_diagnostic): 双方合法 2/2；按电路CPD几何均值改善 -3.514592834343966%；最差改善 -7.32467883161354%。

A0->Ed (accuracy_or_assignment_diagnostic): 双方合法 2/2；按电路CPD几何均值改善 13.26403814379301%；最差改善 0.0%。

P->Ed (accuracy_or_assignment_diagnostic): 双方合法 2/2；按电路CPD几何均值改善 -5.974842022025739%；最差改善 -12.428641502733973%。

候选/成本表诊断（64-bit非密码学fingerprint，用于排查，不替代输入SHA和合法性审计）：

```json
{}
```
