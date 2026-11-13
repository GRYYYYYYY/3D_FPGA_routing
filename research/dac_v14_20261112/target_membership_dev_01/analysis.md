# 独立机制开发集配对结果

Development times only; no ratio to historical timing; formal rotated repeats pending.

每个电路为单seed；无置信区间和盲测外推。合法状态要求FULL和原范围独立审计通过。分母始终包含全部登记电路；未结束/未审计/缺失单列，manifest运行状态需结合实时进程核验。

| 电路 | 臂 | 状态 | CPD(ns) | 迭代 | 规划(s) | 完整进程(s) | SB占用 | CB占用 |
|---|---|---|---:|---:|---:|---:|---:|---:|
| spmv | A0 | legal | 7.0347 | 17 | — | — | 0 | 967 |
| spmv | R1 | legal | 7.04599 | 19 | — | — | 1 | 967 |
| spmv | U | legal | 7.04599 | 19 | — | 22.809336494654417 | 1 | 967 |
| spmv | Tf | legal | 7.04599 | 19 | — | 18.101729404181242 | 1 | 967 |
| spmv | O | missing | — | — | — | None | — | — |
| softmax | A0 | missing | — | — | — | None | — | — |
| softmax | R1 | missing | — | — | — | None | — | — |
| softmax | U | missing | — | — | — | None | — | — |
| softmax | Tf | missing | — | — | — | None | — | — |
| softmax | O | missing | — | — | — | None | — | — |
| eltwise_layer | A0 | missing | — | — | — | None | — | — |
| eltwise_layer | R1 | missing | — | — | — | None | — | — |
| eltwise_layer | U | missing | — | — | — | None | — | — |
| eltwise_layer | Tf | missing | — | — | — | None | — | — |
| eltwise_layer | O | missing | — | — | — | None | — | — |
| bnn | A0 | missing | — | — | — | None | — | — |
| bnn | R1 | missing | — | — | — | None | — | — |
| bnn | U | missing | — | — | — | None | — | — |
| bnn | Tf | missing | — | — | — | None | — | — |
| bnn | O | missing | — | — | — | None | — | — |

R1->O (method_or_reproduction): 双方合法 0/4；按电路CPD几何均值改善 None%；最差改善 None%。

A0->O (method_or_reproduction): 双方合法 0/4；按电路CPD几何均值改善 None%；最差改善 None%。

U->O (method_or_reproduction): 双方合法 0/4；按电路CPD几何均值改善 None%；最差改善 None%。

U->Tf (method_or_reproduction): 双方合法 1/4；按电路CPD几何均值改善 0.0%；最差改善 0.0%。

Tf->O (method_or_reproduction): 双方合法 0/4；按电路CPD几何均值改善 None%；最差改善 None%。

候选/成本表诊断（64-bit非密码学fingerprint，用于排查，不替代输入SHA和合法性审计）：

```json
{}
```
