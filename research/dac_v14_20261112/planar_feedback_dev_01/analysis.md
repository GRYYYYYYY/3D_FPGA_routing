# 独立机制开发集配对结果

Development times only; no ratio to historical timing; formal rotated repeats pending.

每个电路为单seed；无置信区间和盲测外推。合法状态要求FULL和原范围独立审计通过。分母始终包含全部登记电路；未结束/未审计/缺失单列，manifest运行状态需结合实时进程核验。

| 电路 | 臂 | 状态 | CPD(ns) | 迭代 | 规划(s) | 完整进程(s) | SB占用 | CB占用 |
|---|---|---|---:|---:|---:|---:|---:|---:|
| eltwise_layer | A0 | legal | 9.93208 | 43 | — | — | 127 | 956 |
| eltwise_layer | R1 | legal | 6.96208 | 46 | — | — | 134 | 958 |
| eltwise_layer | U | legal | 6.37264 | 34 | — | 34.98167923092842 | 84 | 972 |
| eltwise_layer | V | legal | 6.37264 | 34 | 1.355448 | 28.26736830919981 | 84 | 972 |
| eltwise_layer | Pl | legal | 6.37264 | 34 | 1.369503 | 27.468230199068785 | 84 | 972 |
| eltwise_layer | X | legal | 7.65785 | 82 | 1.327162 | 31.57855186238885 | 112 | 956 |

R1->V (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 8.466435318180787%；最差改善 8.466435318180787%。

A0->V (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 35.83781040829312%；最差改善 35.83781040829312%。

R1->Pl (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 8.466435318180787%；最差改善 8.466435318180787%。

A0->Pl (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 35.83781040829312%；最差改善 35.83781040829312%。

R1->X (transaction_diagnostic_not_method_benefit): 双方合法 1/1；按电路CPD几何均值改善 -9.993708776687416%；最差改善 -9.993708776687416%。

A0->X (transaction_diagnostic_not_method_benefit): 双方合法 1/1；按电路CPD几何均值改善 22.897822007072033%；最差改善 22.897822007072033%。

U->V (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 0.0%；最差改善 0.0%。

U->Pl (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 0.0%；最差改善 0.0%。

V->Pl (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 0.0%；最差改善 0.0%。

候选/成本表诊断（64-bit非密码学fingerprint，用于排查，不替代输入SHA和合法性审计）：

```json
{}
```
