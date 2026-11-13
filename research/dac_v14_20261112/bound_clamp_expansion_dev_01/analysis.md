# 独立机制开发集配对结果

Development times only; no ratio to historical timing; formal rotated repeats pending.

每个电路为单seed；无置信区间和盲测外推。合法状态要求FULL和原范围独立审计通过。分母始终包含全部登记电路；未结束/未审计/缺失单列，manifest运行状态需结合实时进程核验。

| 电路 | 臂 | 状态 | CPD(ns) | 迭代 | 规划(s) | 完整进程(s) | SB占用 | CB占用 |
|---|---|---|---:|---:|---:|---:|---:|---:|
| eltwise_layer | A0 | legal | 9.93208 | 43 | — | — | 127 | 956 |
| eltwise_layer | R1 | legal | 6.96208 | 46 | — | — | 134 | 958 |
| eltwise_layer | P | legal | 6.64602 | 39 | — | 27.41871153563261 | 117 | 965 |
| eltwise_layer | L | legal | 6.7028 | 35 | 1.315318 | 26.870461761951447 | 96 | 962 |
| bnn | A0 | legal | 13.6074 | 18 | — | — | 98 | 5067 |
| bnn | R1 | legal | 13.4216 | 35 | — | — | 86 | 5072 |
| bnn | P | legal | 13.6074 | 19 | — | 276.6189729087055 | 107 | 5066 |
| bnn | L | legal | 13.4216 | 19 | 13.38613 | 271.0431540198624 | 110 | 5065 |

R1->L (method_or_reproduction): 双方合法 2/2；按电路CPD几何均值改善 1.87975457871431%；最差改善 0.0%。

A0->L (method_or_reproduction): 双方合法 2/2；按电路CPD几何均值改善 18.41269343250148%；最差改善 1.3654335141173202%。

P->L (method_or_reproduction): 双方合法 2/2；按电路CPD几何均值改善 0.26171904940816004%；最差改善 -0.8543459092810402%。

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
