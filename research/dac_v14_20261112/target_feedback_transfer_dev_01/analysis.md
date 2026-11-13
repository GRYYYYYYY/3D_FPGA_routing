# 独立机制开发集配对结果

Development times only; no ratio to historical timing; formal rotated repeats pending.

每个电路为单seed；无置信区间和盲测外推。合法状态要求FULL和原范围独立审计通过。分母始终包含全部登记电路；未结束/未审计/缺失单列，manifest运行状态需结合实时进程核验。

| 电路 | 臂 | 状态 | CPD(ns) | 迭代 | 规划(s) | 完整进程(s) | SB占用 | CB占用 |
|---|---|---|---:|---:|---:|---:|---:|---:|
| clstm_like.small | A0 | legal | 6.96198 | 32 | — | — | 9 | 915 |
| clstm_like.small | R1 | legal | 6.85706 | 35 | — | — | 5 | 916 |
| clstm_like.small | F | failed | — | — | — | 34.0267866961658 | — | — |
| clstm_like.small | V | missing | — | — | — | None | — | — |
| clstm_like.small | Tf | missing | — | — | — | None | — | — |
| clstm_like.small | A1 | missing | — | — | — | None | — | — |
| conv_layer | A0 | missing | — | — | — | None | — | — |
| conv_layer | R1 | missing | — | — | — | None | — | — |
| conv_layer | F | missing | — | — | — | None | — | — |
| conv_layer | V | missing | — | — | — | None | — | — |
| conv_layer | Tf | missing | — | — | — | None | — | — |
| conv_layer | A1 | missing | — | — | — | None | — | — |

R1->F (method_or_reproduction): 双方合法 0/2；按电路CPD几何均值改善 None%；最差改善 None%。

F->V (method_or_reproduction): 双方合法 0/2；按电路CPD几何均值改善 None%；最差改善 None%。

A0->V (method_or_reproduction): 双方合法 0/2；按电路CPD几何均值改善 None%；最差改善 None%。

F->Tf (method_or_reproduction): 双方合法 0/2；按电路CPD几何均值改善 None%；最差改善 None%。

A0->Tf (method_or_reproduction): 双方合法 0/2；按电路CPD几何均值改善 None%；最差改善 None%。

F->A1 (method_or_reproduction): 双方合法 0/2；按电路CPD几何均值改善 None%；最差改善 None%。

A0->A1 (method_or_reproduction): 双方合法 0/2；按电路CPD几何均值改善 None%；最差改善 None%。

V->Tf (method_or_reproduction): 双方合法 0/2；按电路CPD几何均值改善 None%；最差改善 None%。

A1->Tf (method_or_reproduction): 双方合法 0/2；按电路CPD几何均值改善 None%；最差改善 None%。

候选/成本表诊断（64-bit非密码学fingerprint，用于排查，不替代输入SHA和合法性审计）：

```json
{}
```
