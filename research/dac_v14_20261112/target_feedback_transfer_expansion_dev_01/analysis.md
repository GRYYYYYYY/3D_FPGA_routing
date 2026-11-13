# 独立机制开发集配对结果

Development times only; no ratio to historical timing; formal rotated repeats pending.

每个电路为单seed；无置信区间和盲测外推。合法状态要求FULL和原范围独立审计通过。分母始终包含全部登记电路；未结束/未审计/缺失单列，manifest运行状态需结合实时进程核验。

| 电路 | 臂 | 状态 | CPD(ns) | 迭代 | 规划(s) | 完整进程(s) | SB占用 | CB占用 |
|---|---|---|---:|---:|---:|---:|---:|---:|
| robot_rl | A0 | legal | 13.3546 | 22 | — | — | 10 | 653 |
| robot_rl | R1 | legal | 13.7339 | 24 | — | — | 8 | 653 |
| robot_rl | F | legal | 13.7339 | 24 | 1.986425 | 41.99786828830838 | 8 | 653 |
| robot_rl | V | legal | 13.7339 | 24 | 2.00272 | 41.36393415182829 | 8 | 653 |
| robot_rl | Tf | legal | 13.7339 | 24 | 2.002537 | 41.340617425739765 | 8 | 653 |
| robot_rl | A1 | legal | 13.3623 | 17 | — | 38.38634220138192 | 47 | 692 |
| tpu_like.small.os | A0 | legal | 7.87599 | 24 | — | — | 35 | 1561 |
| tpu_like.small.os | R1 | legal | 7.81221 | 18 | — | — | 31 | 1563 |
| tpu_like.small.os | F | legal | 7.81221 | 18 | 3.908024 | 48.10410428792238 | 31 | 1563 |
| tpu_like.small.os | V | legal | 7.81221 | 18 | 7.30974 | 52.37581976503134 | 31 | 1563 |
| tpu_like.small.os | Tf | legal | 7.81221 | 20 | 4.417536 | 50.75725755095482 | 32 | 1562 |
| tpu_like.small.os | A1 | legal | 7.99803 | 17 | — | 45.153284661471844 | 101 | 1625 |

R1->F (method_or_reproduction): 双方合法 2/2；按电路CPD几何均值改善 0.0%；最差改善 0.0%。

F->V (method_or_reproduction): 双方合法 2/2；按电路CPD几何均值改善 0.0%；最差改善 0.0%。

A0->V (method_or_reproduction): 双方合法 2/2；按电路CPD几何均值改善 -0.998721133922964%；最差改善 -2.8402198493403086%。

F->Tf (method_or_reproduction): 双方合法 2/2；按电路CPD几何均值改善 0.0%；最差改善 0.0%。

A0->Tf (method_or_reproduction): 双方合法 2/2；按电路CPD几何均值改善 -0.998721133922964%；最差改善 -2.8402198493403086%。

F->A1 (method_or_reproduction): 双方合法 2/2；按电路CPD几何均值改善 0.19593544591111067%；最差改善 -2.3785842930489576%。

A0->A1 (method_or_reproduction): 双方合法 2/2；按电路CPD几何均值改善 -0.8008288393046792%；最差改善 -1.5495194889785235%。

V->Tf (method_or_reproduction): 双方合法 2/2；按电路CPD几何均值改善 0.0%；最差改善 0.0%。

A1->Tf (method_or_reproduction): 双方合法 2/2；按电路CPD几何均值改善 -0.19632010658736654%；最差改善 -2.7809583679456518%。

候选/成本表诊断（64-bit非密码学fingerprint，用于排查，不替代输入SHA和合法性审计）：

```json
{}
```
