# 独立机制开发集配对结果

Development times only; no ratio to historical timing; formal rotated repeats pending.

每个电路为单seed；无置信区间和盲测外推。合法状态要求FULL和原范围独立审计通过。分母始终包含全部登记电路；未结束/未审计/缺失单列，manifest运行状态需结合实时进程核验。

| 电路 | 臂 | 状态 | CPD(ns) | 迭代 | 规划(s) | 完整进程(s) | SB占用 | CB占用 |
|---|---|---|---:|---:|---:|---:|---:|---:|
| gemm_layer | A0 | legal | 13.2565 | 23 | — | — | 405 | 9440 |
| gemm_layer | R1 | legal | 13.1564 | 19 | — | — | 414 | 9433 |
| gemm_layer | U | legal | 13.1564 | 20 | — | 1345.3776608668268 | 406 | 9448 |
| gemm_layer | V | legal | 13.1564 | 20 | 27.389007 | 1257.0534515045583 | 406 | 9448 |

R1->V (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 0.0%；最差改善 0.0%。

A0->V (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 0.7551012710745764%；最差改善 0.7551012710745764%。

U->V (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 0.0%；最差改善 0.0%。

候选/成本表诊断（64-bit非密码学fingerprint，用于排查，不替代输入SHA和合法性审计）：

```json
{
  "gemm_layer F/H": {
    "reference_count": 0,
    "variant_count": 0,
    "exact_sequence_equal": false,
    "first_mismatch": null
  },
  "gemm_layer F/N": {
    "reference_count": 0,
    "variant_count": 0,
    "exact_sequence_equal": false,
    "first_mismatch": null
  }
}
```
