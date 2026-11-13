# 独立机制开发集配对结果

Development times only; no ratio to historical timing; formal rotated repeats pending.

每个电路为单seed；无置信区间和盲测外推。合法状态要求FULL和原范围独立审计通过。分母始终包含全部登记电路；未结束/未审计/缺失单列，manifest运行状态需结合实时进程核验。

| 电路 | 臂 | 状态 | CPD(ns) | 迭代 | 规划(s) | 完整进程(s) | SB占用 | CB占用 |
|---|---|---|---:|---:|---:|---:|---:|---:|
| eltwise_layer | A0 | legal | 9.93208 | 43 | — | — | 127 | 956 |
| eltwise_layer | R1 | legal | 6.96208 | 46 | — | — | 134 | 958 |
| eltwise_layer | P | legal | 6.64602 | 39 | — | 27.41871153563261 | 117 | 965 |
| eltwise_layer | Rq | legal | 8.21844 | 38 | 1.373337 | 28.220271408557892 | 113 | 960 |
| bnn | A0 | legal | 13.6074 | 18 | — | — | 98 | 5067 |
| bnn | R1 | legal | 13.4216 | 35 | — | — | 86 | 5072 |
| bnn | P | legal | 13.6074 | 19 | — | 276.6189729087055 | 107 | 5066 |
| bnn | Rq | legal | 13.4216 | 19 | 12.604908 | 266.54497338086367 | 93 | 5060 |

R1->Rq (method_or_reproduction): 双方合法 2/2；按电路CPD几何均值改善 -8.648863979612752%；最差改善 -18.04575644060393%。

A0->Rq (method_or_reproduction): 双方合法 2/2；按电路CPD几何均值改善 9.658112495995407%；最差改善 1.3654335141173202%。

P->Rq (method_or_reproduction): 双方合法 2/2；按电路CPD几何均值改善 -10.440519935862834%；最差改善 -23.659573699748115%。

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
