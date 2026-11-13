# 独立机制开发集配对结果

Development times only; no ratio to historical timing; formal rotated repeats pending.

每个电路为单seed；无置信区间和盲测外推。合法状态要求FULL和原范围独立审计通过。分母始终包含全部登记电路；未结束/未审计/缺失单列，manifest运行状态需结合实时进程核验。

| 电路 | 臂 | 状态 | CPD(ns) | 迭代 | 规划(s) | 完整进程(s) | SB占用 | CB占用 |
|---|---|---|---:|---:|---:|---:|---:|---:|
| spmv | A0 | legal | 7.0347 | 17 | — | — | 0 | 967 |
| spmv | R1 | legal | 7.04599 | 19 | — | — | 1 | 967 |
| spmv | F | legal | 7.04599 | 19 | 3.444383 | 21.11095529794693 | 1 | 967 |
| spmv | M | legal | 7.26887 | 19 | 3.186387 | 20.357236102223396 | 0 | 967 |
| spmv | T | legal | 7.04599 | 21 | 3.577416 | 21.173137437552214 | 0 | 967 |
| spmv | Q | legal | 7.04599 | 17 | 3.557659 | 20.612256456166506 | 0 | 967 |
| softmax | A0 | legal | 8.97575 | 13 | — | — | 6 | 713 |
| softmax | R1 | legal | 8.97575 | 13 | — | — | 6 | 713 |
| softmax | F | legal | 8.97575 | 13 | 4.195111 | 40.59374302253127 | 6 | 713 |
| softmax | M | legal | 8.97575 | 13 | 4.163842 | 39.79247970506549 | 6 | 713 |
| softmax | T | legal | 8.97575 | 13 | 4.382207 | 40.34392820298672 | 6 | 713 |
| softmax | Q | legal | 8.97575 | 13 | 4.41008 | 40.193367410451174 | 6 | 713 |

R1->F (method_or_reproduction): 双方合法 2/2；按电路CPD几何均值改善 0.0%；最差改善 0.0%。

F->M (method_or_reproduction): 双方合法 2/2；按电路CPD几何均值改善 -1.5692953898834405%；最差改善 -3.1632176599739603%。

A0->M (method_or_reproduction): 双方合法 2/2；按电路CPD几何均值改善 -1.6507670675462993%；最差改善 -3.328784454205569%。

F->T (method_or_reproduction): 双方合法 2/2；按电路CPD几何均值改善 0.0%；最差改善 0.0%。

A0->T (method_or_reproduction): 双方合法 2/2；按电路CPD几何均值改善 -0.08021290031612338%；最差改善 -0.16049014172601073%。

F->Q (method_or_reproduction): 双方合法 2/2；按电路CPD几何均值改善 0.0%；最差改善 0.0%。

A0->Q (method_or_reproduction): 双方合法 2/2；按电路CPD几何均值改善 -0.08021290031612338%；最差改善 -0.16049014172601073%。

M->T (method_or_reproduction): 双方合法 2/2；按电路CPD几何均值改善 1.5450490070444522%；最差改善 0.0%。

T->Q (method_or_reproduction): 双方合法 2/2；按电路CPD几何均值改善 0.0%；最差改善 0.0%。

候选/成本表诊断（64-bit非密码学fingerprint，用于排查，不替代输入SHA和合法性审计）：

```json
{
  "spmv F/H": {
    "reference_count": 88,
    "variant_count": 0,
    "exact_sequence_equal": false,
    "first_mismatch": null
  },
  "spmv F/N": {
    "reference_count": 88,
    "variant_count": 0,
    "exact_sequence_equal": false,
    "first_mismatch": null
  },
  "softmax F/H": {
    "reference_count": 43,
    "variant_count": 0,
    "exact_sequence_equal": false,
    "first_mismatch": null
  },
  "softmax F/N": {
    "reference_count": 43,
    "variant_count": 0,
    "exact_sequence_equal": false,
    "first_mismatch": null
  }
}
```
