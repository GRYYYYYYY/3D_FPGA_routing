# 独立机制开发集配对结果

Development times only; no ratio to historical timing; formal rotated repeats pending.

每个电路为单seed；无置信区间和盲测外推。合法状态要求FULL和原范围独立审计通过。分母始终包含全部登记电路；未结束/未审计/缺失单列，manifest运行状态需结合实时进程核验。

| 电路 | 臂 | 状态 | CPD(ns) | 迭代 | 规划(s) | 完整进程(s) | SB占用 | CB占用 |
|---|---|---|---:|---:|---:|---:|---:|---:|
| clstm_like.small | A0 | legal | 6.96198 | 32 | — | — | 9 | 915 |
| clstm_like.small | R1 | legal | 6.85706 | 35 | — | — | 5 | 916 |
| clstm_like.small | F | legal | 6.85706 | 35 | 2.543947 | 46.30027477070689 | 5 | 916 |
| clstm_like.small | V | legal | 6.85706 | 35 | 2.788529 | 47.704433120787144 | 5 | 916 |
| clstm_like.small | Tf | legal | 6.85706 | 35 | 2.64195 | 47.85196082666516 | 5 | 916 |
| clstm_like.small | A1 | legal | 6.85706 | 20 | — | 41.24386329948902 | 68 | 976 |
| conv_layer | A0 | failed | — | — | — | — | — | — |
| conv_layer | R1 | failed | — | — | — | — | — | — |
| conv_layer | F | failed | — | — | 1.864686 | 108.66396439447999 | — | — |
| conv_layer | V | failed | — | — | 3.330681 | 122.99501158669591 | — | — |
| conv_layer | Tf | failed | — | — | 2.459156 | 116.02957136183977 | — | — |
| conv_layer | A1 | failed | — | — | — | 109.41743316501379 | — | — |

R1->F (method_or_reproduction): 双方合法 1/2；按电路CPD几何均值改善 0.0%；最差改善 0.0%。

F->V (method_or_reproduction): 双方合法 1/2；按电路CPD几何均值改善 0.0%；最差改善 0.0%。

A0->V (method_or_reproduction): 双方合法 1/2；按电路CPD几何均值改善 1.5070425367496032%；最差改善 1.5070425367496032%。

F->Tf (method_or_reproduction): 双方合法 1/2；按电路CPD几何均值改善 0.0%；最差改善 0.0%。

A0->Tf (method_or_reproduction): 双方合法 1/2；按电路CPD几何均值改善 1.5070425367496032%；最差改善 1.5070425367496032%。

F->A1 (method_or_reproduction): 双方合法 1/2；按电路CPD几何均值改善 0.0%；最差改善 0.0%。

A0->A1 (method_or_reproduction): 双方合法 1/2；按电路CPD几何均值改善 1.5070425367496032%；最差改善 1.5070425367496032%。

V->Tf (method_or_reproduction): 双方合法 1/2；按电路CPD几何均值改善 0.0%；最差改善 0.0%。

A1->Tf (method_or_reproduction): 双方合法 1/2；按电路CPD几何均值改善 0.0%；最差改善 0.0%。

候选/成本表诊断（64-bit非密码学fingerprint，用于排查，不替代输入SHA和合法性审计）：

```json
{}
```
