# 独立机制开发集配对结果

Development times only; no ratio to historical timing; formal rotated repeats pending.

每个电路为单seed；无置信区间和盲测外推。合法状态要求FULL和原范围独立审计通过。分母始终包含全部登记电路；未结束/未审计/缺失单列，manifest运行状态需结合实时进程核验。

| 电路 | 臂 | 状态 | CPD(ns) | 迭代 | 规划(s) | 完整进程(s) | SB占用 | CB占用 |
|---|---|---|---:|---:|---:|---:|---:|---:|
| eltwise_layer | A0 | legal | 9.93208 | 43 | — | — | 127 | 956 |
| eltwise_layer | R1 | legal | 6.96208 | 46 | — | — | 134 | 958 |
| eltwise_layer | Uref | legal | 6.37264 | 34 | — | 34.98167923092842 | 84 | 972 |
| eltwise_layer | A1 | legal | 6.0181 | 22 | — | 26.31660781800747 | 243 | 1144 |
| eltwise_layer | F1 | legal | 6.20393 | 19 | — | 26.896897975355387 | 223 | 1144 |
| eltwise_layer | U1 | legal | 6.20393 | 22 | — | 27.36837073788047 | 206 | 1123 |
| eltwise_layer | F | legal | 6.96208 | 46 | 0.964267 | 27.968380570411682 | 134 | 958 |
| eltwise_layer | A | legal | 9.93208 | 43 | — | 25.514181710779667 | 127 | 956 |
| eltwise_layer | U | legal | 6.37264 | 34 | 1.598748 | 27.269336502999067 | 84 | 972 |
| eltwise_layer | A2 | legal | 6.22942 | 20 | — | 26.367527469992638 | 254 | 1150 |
| eltwise_layer | F2 | legal | 5.84702 | 19 | 0.933898 | 26.816532906144857 | 221 | 1139 |
| eltwise_layer | U2 | legal | 6.0181 | 20 | 1.546664 | 27.819186221808195 | 232 | 1128 |
| eltwise_layer | X2 | legal | 6.10047 | 20 | 1.299002 | 27.47108691930771 | 229 | 1131 |

R1->F (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 0.0%；最差改善 0.0%。

F->A (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 -42.65966492772273%；最差改善 -42.65966492772273%。

A0->A (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 0.0%；最差改善 0.0%。

F->U (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 8.466435318180787%；最差改善 8.466435318180787%。

A0->U (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 35.83781040829312%；最差改善 35.83781040829312%。

F->A2 (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 10.523579160250963%；最差改善 10.523579160250963%。

A0->A2 (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 37.2798044317001%；最差改善 37.2798044317001%。

F->F2 (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 16.016190563739585%；最差改善 16.016190563739585%。

A0->F2 (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 41.12995465199636%；最差改善 41.12995465199636%。

F->U2 (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 13.558878955714393%；最差改善 13.558878955714393%。

A0->U2 (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 39.407455437330356%；最差改善 39.407455437330356%。

F->X2 (transaction_diagnostic_not_method_benefit): 双方合法 1/1；按电路CPD几何均值改善 12.37575552133846%；最差改善 12.37575552133846%。

A0->X2 (transaction_diagnostic_not_method_benefit): 双方合法 1/1；按电路CPD几何均值改善 38.57812260875869%；最差改善 38.57812260875869%。

A0->A1 (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 39.407455437330356%；最差改善 39.407455437330356%。

F->F1 (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 10.889705375405057%；最差改善 10.889705375405057%。

A1->F1 (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 -3.08785164752996%；最差改善 -3.08785164752996%。

A1->U1 (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 -3.08785164752996%；最差改善 -3.08785164752996%。

F1->U1 (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 0.0%；最差改善 0.0%。

U->U1 (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 2.6474114338798316%；最差改善 2.6474114338798316%。

A->A2 (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 37.2798044317001%；最差改善 37.2798044317001%。

U->U2 (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 5.56347133997841%；最差改善 5.56347133997841%。

Uref->U2 (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 5.56347133997841%；最差改善 5.56347133997841%。

A1->A2 (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 -3.511407254781429%；最差改善 -3.511407254781429%。

F1->F2 (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 5.752966264932069%；最差改善 5.752966264932069%。

U1->U2 (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 2.9953593931588585%；最差改善 2.9953593931588585%。

A2->F2 (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 6.1386132256293635%；最差改善 6.1386132256293635%。

A2->U2 (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 3.3922901329497823%；最差改善 3.3922901329497823%。

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
  }
}
```
