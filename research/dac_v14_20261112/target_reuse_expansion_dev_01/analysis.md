# 独立机制开发集配对结果

Development times only; no ratio to historical timing; formal rotated repeats pending.

每个电路为单seed；无置信区间和盲测外推。合法状态要求FULL和原范围独立审计通过。分母始终包含全部登记电路；未结束/未审计/缺失单列，manifest运行状态需结合实时进程核验。

| 电路 | 臂 | 状态 | CPD(ns) | 迭代 | 规划(s) | 完整进程(s) | SB占用 | CB占用 |
|---|---|---|---:|---:|---:|---:|---:|---:|
| eltwise_layer | A0 | legal | 9.93208 | 43 | — | — | 127 | 956 |
| eltwise_layer | R1 | legal | 6.96208 | 46 | — | — | 134 | 958 |
| eltwise_layer | Q | legal | 6.78852 | 59 | 5.335775 | 34.12774909287691 | 119 | 952 |
| eltwise_layer | E | legal | 6.5642 | 58 | 5.369 | 33.78048477321863 | 110 | 956 |
| bnn | A0 | legal | 13.6074 | 18 | — | — | 98 | 5067 |
| bnn | R1 | legal | 13.4216 | 35 | — | — | 86 | 5072 |
| bnn | Q | legal | 13.5998 | 19 | 265.757342 | 524.4025833830237 | 106 | 5065 |
| bnn | E | legal | 13.5998 | 33 | 266.076356 | 544.3281172960997 | 91 | 5066 |

R1->Q (method_or_reproduction): 双方合法 2/2；按电路CPD几何均值改善 0.6009665674959752%；最差改善 -1.3277105561184888%。

A0->Q (method_or_reproduction): 双方合法 2/2；按电路CPD几何均值改善 17.349376998078057%；最差改善 0.05585196290254224%。

R1->E (method_or_reproduction): 双方合法 2/2；按电路CPD几何均值改善 2.2570341673716077%；最差改善 -1.3277105561184888%。

A0->E (method_or_reproduction): 双方合法 2/2；按电路CPD几何均值改善 18.72640265050518%；最差改善 0.05585196290254224%。

Q->E (method_or_reproduction): 双方合法 2/2；按电路CPD几何均值改善 1.6660801847737994%；最差改善 0.0%。

候选/成本表诊断（64-bit非密码学fingerprint，用于排查，不替代输入SHA和合法性审计）：

```json
{
  "eltwise_layer F/H": {
    "reference_count": 0,
    "variant_count": 0,
    "exact_sequence_equal": false,
    "first_mismatch": null
  },
  "eltwise_layer F/N": {
    "reference_count": 0,
    "variant_count": 0,
    "exact_sequence_equal": false,
    "first_mismatch": null
  },
  "bnn F/H": {
    "reference_count": 0,
    "variant_count": 0,
    "exact_sequence_equal": false,
    "first_mismatch": null
  },
  "bnn F/N": {
    "reference_count": 0,
    "variant_count": 0,
    "exact_sequence_equal": false,
    "first_mismatch": null
  }
}
```
