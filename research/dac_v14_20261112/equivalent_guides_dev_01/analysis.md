# 独立机制开发集配对结果

Development times only; no ratio to historical timing; formal rotated repeats pending.

每个电路为单seed；无置信区间和盲测外推。合法状态要求FULL和原范围独立审计通过。分母始终包含全部登记电路；未结束/未审计/缺失单列，manifest运行状态需结合实时进程核验。

| 电路 | 臂 | 状态 | CPD(ns) | 迭代 | 规划(s) | 完整进程(s) | SB占用 | CB占用 |
|---|---|---|---:|---:|---:|---:|---:|---:|
| spmv | A0 | legal | 7.0347 | 17 | — | — | 0 | 967 |
| spmv | R1 | legal | 7.04599 | 19 | — | — | 1 | 967 |
| spmv | P | legal | 7.04234 | 17 | 1.130337 | 18.913791816681623 | 0 | 967 |
| spmv | Eq | legal | 7.04234 | 17 | 1.289199 | 19.608378585428 | 0 | 967 |
| eltwise_layer | A0 | legal | 9.93208 | 43 | — | — | 127 | 956 |
| eltwise_layer | R1 | legal | 6.96208 | 46 | — | — | 134 | 958 |
| eltwise_layer | P | legal | 6.64602 | 39 | 1.318704 | 27.15369475260377 | 117 | 965 |
| eltwise_layer | Eq | legal | 6.64602 | 39 | 1.343702 | 27.81970664858818 | 117 | 965 |

R1->P (method_or_reproduction): 双方合法 2/2；按电路CPD几何均值改善 2.32154079283311%；最差改善 0.051802514621779316%。

A0->P (method_or_reproduction): 双方合法 2/2；按电路CPD几何均值改善 18.15419565505949%；最差改善 -0.10860448917509036%。

R1->Eq (method_or_reproduction): 双方合法 2/2；按电路CPD几何均值改善 2.32154079283311%；最差改善 0.051802514621779316%。

A0->Eq (method_or_reproduction): 双方合法 2/2；按电路CPD几何均值改善 18.15419565505949%；最差改善 -0.10860448917509036%。

P->Eq (method_or_reproduction): 双方合法 2/2；按电路CPD几何均值改善 0.0%；最差改善 0.0%。

候选/成本表诊断（64-bit非密码学fingerprint，用于排查，不替代输入SHA和合法性审计）：

```json
{}
```
