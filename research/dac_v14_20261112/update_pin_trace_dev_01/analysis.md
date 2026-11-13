# 独立机制开发集配对结果

Development times only; no ratio to historical timing; formal rotated repeats pending.

每个电路为单seed；无置信区间和盲测外推。合法状态要求FULL和原范围独立审计通过。分母始终包含全部登记电路；未结束/未审计/缺失单列，manifest运行状态需结合实时进程核验。

| 电路 | 臂 | 状态 | CPD(ns) | 迭代 | 规划(s) | 完整进程(s) | SB占用 | CB占用 |
|---|---|---|---:|---:|---:|---:|---:|---:|
| eltwise_layer | A0 | legal | 9.93208 | 43 | — | — | 127 | 956 |
| eltwise_layer | R1 | legal | 6.96208 | 46 | — | — | 134 | 958 |
| eltwise_layer | U | legal | 6.37264 | 34 | — | 34.98167923092842 | 84 | 972 |
| eltwise_layer | V | failed | — | — | 0.929213 | 16.64798705652356 | — | — |
| eltwise_layer | Xp | missing | — | — | — | None | — | — |

R1->V (mechanism_diagnostic_not_method_benefit): 双方合法 0/1；按电路CPD几何均值改善 None%；最差改善 None%。

A0->V (mechanism_diagnostic_not_method_benefit): 双方合法 0/1；按电路CPD几何均值改善 None%；最差改善 None%。

R1->Xp (method_or_reproduction): 双方合法 0/1；按电路CPD几何均值改善 None%；最差改善 None%。

A0->Xp (method_or_reproduction): 双方合法 0/1；按电路CPD几何均值改善 None%；最差改善 None%。

U->V (mechanism_diagnostic_not_method_benefit): 双方合法 0/1；按电路CPD几何均值改善 None%；最差改善 None%。

U->Xp (method_or_reproduction): 双方合法 0/1；按电路CPD几何均值改善 None%；最差改善 None%。

V->Xp (method_or_reproduction): 双方合法 0/1；按电路CPD几何均值改善 None%；最差改善 None%。

候选/成本表诊断（64-bit非密码学fingerprint，用于排查，不替代输入SHA和合法性审计）：

```json
{}
```
