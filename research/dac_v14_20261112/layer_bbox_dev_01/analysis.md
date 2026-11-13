# 独立机制开发集配对结果

Development times only; no ratio to historical timing; formal rotated repeats pending.

每个电路为单seed；无置信区间和盲测外推。合法状态要求FULL和原范围独立审计通过。分母始终包含全部登记电路；未结束/未审计/缺失单列，manifest运行状态需结合实时进程核验。

| 电路 | 臂 | 状态 | CPD(ns) | 迭代 | 规划(s) | 完整进程(s) | SB占用 | CB占用 |
|---|---|---|---:|---:|---:|---:|---:|---:|
| eltwise_layer | A0 | legal | 9.93208 | 43 | — | — | 127 | 956 |
| eltwise_layer | R1 | legal | 6.96208 | 46 | — | — | 134 | 958 |
| eltwise_layer | F | legal | 6.96208 | 46 | 0.942136 | 27.267735354602337 | 134 | 958 |
| eltwise_layer | A1 | legal | 6.0181 | 22 | — | 26.31660781800747 | 243 | 1144 |
| eltwise_layer | F1 | legal | 6.20393 | 19 | 0.929993 | 26.896897975355387 | 223 | 1144 |
| eltwise_layer | U1 | legal | 6.20393 | 22 | 1.292836 | 27.36837073788047 | 206 | 1123 |
| attention_layer | A0 | failed | — | — | — | — | — | — |
| attention_layer | R1 | failed | — | — | — | — | — | — |
| attention_layer | F | failed | — | — | 1.837216 | 673.6849078014493 | — | — |
| attention_layer | A1 | legal | 12.6638 | 37 | — | 78.30619978532195 | 740 | 2307 |
| attention_layer | F1 | legal | 12.6638 | 49 | 1.84152 | 83.46345590427518 | 727 | 2299 |
| attention_layer | U1 | legal | 12.6638 | 49 | 1.894443 | 81.86136950552464 | 727 | 2299 |

R1->F (method_or_reproduction): 双方合法 1/2；按电路CPD几何均值改善 0.0%；最差改善 0.0%。

F->A1 (method_or_reproduction): 双方合法 1/2；按电路CPD几何均值改善 13.558878955714393%；最差改善 13.558878955714393%。

A0->A1 (method_or_reproduction): 双方合法 1/2；按电路CPD几何均值改善 39.407455437330356%；最差改善 39.407455437330356%。

F->F1 (method_or_reproduction): 双方合法 1/2；按电路CPD几何均值改善 10.889705375405057%；最差改善 10.889705375405057%。

A0->F1 (method_or_reproduction): 双方合法 1/2；按电路CPD几何均值改善 37.53644755177164%；最差改善 37.53644755177164%。

F->U1 (method_or_reproduction): 双方合法 1/2；按电路CPD几何均值改善 10.889705375405057%；最差改善 10.889705375405057%。

A0->U1 (method_or_reproduction): 双方合法 1/2；按电路CPD几何均值改善 37.53644755177164%；最差改善 37.53644755177164%。

A1->F1 (method_or_reproduction): 双方合法 2/2；按电路CPD几何均值改善 -1.5321878260928345%；最差改善 -3.08785164752996%。

A1->U1 (method_or_reproduction): 双方合法 2/2；按电路CPD几何均值改善 -1.5321878260928345%；最差改善 -3.08785164752996%。

F1->U1 (method_or_reproduction): 双方合法 2/2；按电路CPD几何均值改善 0.0%；最差改善 0.0%。

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
