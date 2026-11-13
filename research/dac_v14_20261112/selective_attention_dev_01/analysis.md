# 独立机制开发集配对结果

Development times only; no ratio to historical timing; formal rotated repeats pending.

每个电路为单seed；无置信区间和盲测外推。合法状态要求FULL和原范围独立审计通过。分母始终包含全部登记电路；未结束/未审计/缺失单列，manifest运行状态需结合实时进程核验。

| 电路 | 臂 | 状态 | CPD(ns) | 迭代 | 规划(s) | 完整进程(s) | SB占用 | CB占用 |
|---|---|---|---:|---:|---:|---:|---:|---:|
| attention_layer | A0 | failed | — | — | — | — | — | — |
| attention_layer | R1 | failed | — | — | — | — | — | — |
| attention_layer | Uref | failed | — | — | — | 678.5944415442646 | — | — |
| attention_layer | A1 | legal | 12.6638 | 37 | — | 78.30619978532195 | 740 | 2307 |
| attention_layer | F1 | legal | 12.6638 | 49 | — | 83.46345590427518 | 727 | 2299 |
| attention_layer | U1 | legal | 12.6638 | 49 | — | 81.86136950552464 | 727 | 2299 |
| attention_layer | A2 | legal | 12.6638 | 31 | — | 75.90444740653038 | 728 | 2329 |
| attention_layer | F2 | legal | 12.6638 | 32 | 1.801634 | 78.66185319423676 | 730 | 2308 |
| attention_layer | U2 | legal | 12.6638 | 37 | 1.955559 | 77.1600465811789 | 710 | 2298 |

R1->A2 (method_or_reproduction): 双方合法 0/1；按电路CPD几何均值改善 None%；最差改善 None%。

A0->A2 (method_or_reproduction): 双方合法 0/1；按电路CPD几何均值改善 None%；最差改善 None%。

R1->F2 (method_or_reproduction): 双方合法 0/1；按电路CPD几何均值改善 None%；最差改善 None%。

A0->F2 (method_or_reproduction): 双方合法 0/1；按电路CPD几何均值改善 None%；最差改善 None%。

R1->U2 (method_or_reproduction): 双方合法 0/1；按电路CPD几何均值改善 None%；最差改善 None%。

A0->U2 (method_or_reproduction): 双方合法 0/1；按电路CPD几何均值改善 None%；最差改善 None%。

A0->A1 (method_or_reproduction): 双方合法 0/1；按电路CPD几何均值改善 None%；最差改善 None%。

A1->F1 (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 0.0%；最差改善 0.0%。

A1->U1 (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 0.0%；最差改善 0.0%。

F1->U1 (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 0.0%；最差改善 0.0%。

Uref->U2 (method_or_reproduction): 双方合法 0/1；按电路CPD几何均值改善 None%；最差改善 None%。

A1->A2 (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 0.0%；最差改善 0.0%。

F1->F2 (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 0.0%；最差改善 0.0%。

U1->U2 (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 0.0%；最差改善 0.0%。

A2->F2 (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 0.0%；最差改善 0.0%。

A2->U2 (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 0.0%；最差改善 0.0%。

候选/成本表诊断（64-bit非密码学fingerprint，用于排查，不替代输入SHA和合法性审计）：

```json
{
  "attention_layer F/H": {
    "reference_count": 0,
    "variant_count": 0,
    "exact_sequence_equal": false,
    "first_mismatch": null
  },
  "attention_layer F/N": {
    "reference_count": 0,
    "variant_count": 0,
    "exact_sequence_equal": false,
    "first_mismatch": null
  }
}
```
