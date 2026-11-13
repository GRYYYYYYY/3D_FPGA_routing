# 独立机制开发集配对结果

Development times only; no ratio to historical timing; formal rotated repeats pending.

每个电路为单seed；无置信区间和盲测外推。合法状态要求FULL和原范围独立审计通过。分母始终包含全部登记电路；未结束/未审计/缺失单列，manifest运行状态需结合实时进程核验。

| 电路 | 臂 | 状态 | CPD(ns) | 迭代 | 规划(s) | 完整进程(s) | SB占用 | CB占用 |
|---|---|---|---:|---:|---:|---:|---:|---:|
| eltwise_layer | A0 | legal | 9.93208 | 43 | — | — | 127 | 956 |
| eltwise_layer | R1 | legal | 6.96208 | 46 | — | — | 134 | 958 |
| eltwise_layer | F | legal | 6.96208 | 46 | 4.905537 | 32.42923976480961 | 134 | 958 |
| eltwise_layer | U | legal | 6.37264 | 34 | 8.698463 | 34.98167923092842 | 84 | 972 |
| attention_layer | A0 | failed | — | — | — | — | — | — |
| attention_layer | R1 | failed | — | — | — | — | — | — |
| attention_layer | F | failed | — | — | 5.674537 | 686.8742800280452 | — | — |
| attention_layer | U | failed | — | — | 7.49485 | 678.5944415442646 | — | — |

R1->F (method_or_reproduction): 双方合法 1/2；按电路CPD几何均值改善 0.0%；最差改善 0.0%。

F->U (method_or_reproduction): 双方合法 1/2；按电路CPD几何均值改善 8.466435318180787%；最差改善 8.466435318180787%。

A0->U (method_or_reproduction): 双方合法 1/2；按电路CPD几何均值改善 35.83781040829312%；最差改善 35.83781040829312%。

候选/成本表诊断（64-bit非密码学fingerprint，用于排查，不替代输入SHA和合法性审计）：

```json
{
  "eltwise_layer F/H": {
    "reference_count": 87,
    "variant_count": 0,
    "exact_sequence_equal": false,
    "first_mismatch": null
  },
  "eltwise_layer F/N": {
    "reference_count": 87,
    "variant_count": 0,
    "exact_sequence_equal": false,
    "first_mismatch": null
  },
  "attention_layer F/H": {
    "reference_count": 54,
    "variant_count": 0,
    "exact_sequence_equal": false,
    "first_mismatch": null
  },
  "attention_layer F/N": {
    "reference_count": 54,
    "variant_count": 0,
    "exact_sequence_equal": false,
    "first_mismatch": null
  }
}
```
