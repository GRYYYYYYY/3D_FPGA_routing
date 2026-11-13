# 独立机制开发集配对结果

Development times only; no ratio to historical timing; formal rotated repeats pending.

每个电路为单seed；无置信区间和盲测外推。合法状态要求FULL和原范围独立审计通过。分母始终包含全部登记电路；未结束/未审计/缺失单列，manifest运行状态需结合实时进程核验。

| 电路 | 臂 | 状态 | CPD(ns) | 迭代 | 规划(s) | 完整进程(s) | SB占用 | CB占用 |
|---|---|---|---:|---:|---:|---:|---:|---:|
| spmv | A0 | legal | 7.0347 | 17 | — | — | 0 | 967 |
| spmv | R1 | legal | 7.04599 | 19 | — | — | 1 | 967 |
| spmv | P | legal | 7.04234 | 17 | 1.28489 | 19.903103545308113 | 0 | 967 |
| spmv | Bq | legal | 7.04234 | 17 | 1.284693 | 20.704000312834978 | 0 | 967 |
| softmax | A0 | legal | 8.97575 | 13 | — | — | 6 | 713 |
| softmax | R1 | legal | 8.97575 | 13 | — | — | 6 | 713 |
| softmax | P | legal | 8.97575 | 13 | 1.983379 | 39.689766101539135 | 6 | 713 |
| softmax | Bq | legal | 8.97575 | 13 | 1.970107 | 39.69244917109609 | 6 | 713 |

R1->P (method_or_reproduction): 双方合法 2/2；按电路CPD几何均值改善 0.025904612555649464%；最差改善 0.0%。

A0->P (method_or_reproduction): 双方合法 2/2；按电路CPD几何均值改善 -0.05428750891942613%；最差改善 -0.10860448917509036%。

R1->Bq (method_or_reproduction): 双方合法 2/2；按电路CPD几何均值改善 0.025904612555649464%；最差改善 0.0%。

A0->Bq (method_or_reproduction): 双方合法 2/2；按电路CPD几何均值改善 -0.05428750891942613%；最差改善 -0.10860448917509036%。

P->Bq (method_or_reproduction): 双方合法 2/2；按电路CPD几何均值改善 0.0%；最差改善 0.0%。

候选/成本表诊断（64-bit非密码学fingerprint，用于排查，不替代输入SHA和合法性审计）：

```json
{
  "spmv F/H": {
    "reference_count": 0,
    "variant_count": 0,
    "exact_sequence_equal": false,
    "first_mismatch": null
  },
  "spmv F/N": {
    "reference_count": 0,
    "variant_count": 0,
    "exact_sequence_equal": false,
    "first_mismatch": null
  },
  "softmax F/H": {
    "reference_count": 0,
    "variant_count": 0,
    "exact_sequence_equal": false,
    "first_mismatch": null
  },
  "softmax F/N": {
    "reference_count": 0,
    "variant_count": 0,
    "exact_sequence_equal": false,
    "first_mismatch": null
  }
}
```
