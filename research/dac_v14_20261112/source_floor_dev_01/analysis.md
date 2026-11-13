# 独立机制开发集配对结果

Development times only; no ratio to historical timing; formal rotated repeats pending.

每个电路为单seed；无置信区间和盲测外推。合法状态要求FULL和原范围独立审计通过。分母始终包含全部登记电路；未结束/未审计/缺失单列，manifest运行状态需结合实时进程核验。

| 电路 | 臂 | 状态 | CPD(ns) | 迭代 | 规划(s) | 完整进程(s) | SB占用 | CB占用 |
|---|---|---|---:|---:|---:|---:|---:|---:|
| spmv | A0 | legal | 7.0347 | 17 | — | — | 0 | 967 |
| spmv | R1 | legal | 7.04599 | 19 | — | — | 1 | 967 |
| spmv | P | legal | 7.04234 | 17 | 1.103074 | 18.5513075850904 | 0 | 967 |
| spmv | Sf | legal | 7.04599 | 18 | 1.134816 | 18.45027805119753 | 0 | 967 |
| eltwise_layer | A0 | legal | 9.93208 | 43 | — | — | 127 | 956 |
| eltwise_layer | R1 | legal | 6.96208 | 46 | — | — | 134 | 958 |
| eltwise_layer | P | legal | 6.64602 | 39 | 1.312561 | 26.970011211931705 | 117 | 965 |
| eltwise_layer | Sf | legal | 7.47203 | 70 | 1.418285 | 30.023695059120655 | 136 | 960 |

R1->P (method_or_reproduction): 双方合法 2/2；按电路CPD几何均值改善 2.32154079283311%；最差改善 0.051802514621779316%。

A0->P (method_or_reproduction): 双方合法 2/2；按电路CPD几何均值改善 18.15419565505949%；最差改善 -0.10860448917509036%。

R1->Sf (method_or_reproduction): 双方合法 2/2；按电路CPD几何均值改善 -3.597624891506812%；最差改善 -7.32467883161354%。

A0->Sf (method_or_reproduction): 双方合法 2/2；按电路CPD几何均值改善 13.194464713171062%；最差改善 -0.16049014172601073%。

P->Sf (method_or_reproduction): 双方合法 2/2；按电路CPD几何均值改善 -6.0598475164170384%；最差改善 -12.428641502733973%。

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
  }
}
```
