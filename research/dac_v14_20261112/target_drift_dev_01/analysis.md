# 独立机制开发集配对结果

Development times only; no ratio to historical timing; formal rotated repeats pending.

每个电路为单seed；无置信区间和盲测外推。合法状态要求FULL和原范围独立审计通过。分母始终包含全部登记电路；未结束/未审计/缺失单列，manifest运行状态需结合实时进程核验。

| 电路 | 臂 | 状态 | CPD(ns) | 迭代 | 规划(s) | 完整进程(s) | SB占用 | CB占用 |
|---|---|---|---:|---:|---:|---:|---:|---:|
| eltwise_layer | A0 | legal | 9.93208 | 43 | — | — | 127 | 956 |
| eltwise_layer | R1 | legal | 6.96208 | 46 | — | — | 134 | 958 |
| eltwise_layer | U | legal | 6.37264 | 34 | — | 34.98167923092842 | 84 | 972 |
| eltwise_layer | C | legal | 6.20812 | 42 | 1.092664 | 27.77031410485506 | 118 | 955 |
| eltwise_layer | Df | legal | 6.20812 | 42 | 1.116394 | 27.872052267193794 | 118 | 955 |

R1->C (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 10.829522211752806%；最差改善 10.829522211752806%。

A0->C (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 37.494261020853635%；最差改善 37.494261020853635%。

R1->Df (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 10.829522211752806%；最差改善 10.829522211752806%。

A0->Df (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 37.494261020853635%；最差改善 37.494261020853635%。

U->C (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 2.581661603354335%；最差改善 2.581661603354335%。

C->Df (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 0.0%；最差改善 0.0%。

候选/成本表诊断（64-bit非密码学fingerprint，用于排查，不替代输入SHA和合法性审计）：

```json
{}
```
