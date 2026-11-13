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
| eltwise_layer | A2 | legal | 6.22942 | 20 | — | 26.367527469992638 | 254 | 1150 |
| eltwise_layer | F2 | legal | 5.84702 | 19 | — | 26.816532906144857 | 221 | 1139 |
| eltwise_layer | U2 | legal | 6.0181 | 20 | — | 27.819186221808195 | 232 | 1128 |
| eltwise_layer | S | legal | 5.84702 | 19 | 0.954261 | 27.71975789964199 | 221 | 1139 |
| eltwise_layer | A3 | legal | 6.22942 | 20 | — | 26.318387147039175 | 254 | 1150 |
| eltwise_layer | F3 | legal | 5.84702 | 19 | 0.960312 | 27.316903062164783 | 221 | 1139 |
| eltwise_layer | U3 | legal | 6.0181 | 20 | 1.288192 | 27.168173782527447 | 232 | 1128 |

R1->S (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 16.016190563739585%；最差改善 16.016190563739585%。

A0->S (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 41.12995465199636%；最差改善 41.12995465199636%。

R1->A3 (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 10.523579160250963%；最差改善 10.523579160250963%。

A0->A3 (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 37.2798044317001%；最差改善 37.2798044317001%。

R1->F3 (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 16.016190563739585%；最差改善 16.016190563739585%。

A0->F3 (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 41.12995465199636%；最差改善 41.12995465199636%。

R1->U3 (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 13.558878955714393%；最差改善 13.558878955714393%。

A0->U3 (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 39.407455437330356%；最差改善 39.407455437330356%。

A0->A1 (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 39.407455437330356%；最差改善 39.407455437330356%。

A1->F1 (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 -3.08785164752996%；最差改善 -3.08785164752996%。

A1->U1 (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 -3.08785164752996%；最差改善 -3.08785164752996%。

F1->U1 (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 0.0%；最差改善 0.0%。

Uref->U2 (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 5.56347133997841%；最差改善 5.56347133997841%。

A1->A2 (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 -3.511407254781429%；最差改善 -3.511407254781429%。

F1->F2 (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 5.752966264932069%；最差改善 5.752966264932069%。

U1->U2 (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 2.9953593931588585%；最差改善 2.9953593931588585%。

A2->F2 (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 6.1386132256293635%；最差改善 6.1386132256293635%。

A2->U2 (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 3.3922901329497823%；最差改善 3.3922901329497823%。

F2->S (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 0.0%；最差改善 0.0%。

A2->A3 (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 0.0%；最差改善 0.0%。

F2->F3 (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 0.0%；最差改善 0.0%。

U2->U3 (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 0.0%；最差改善 0.0%。

A1->A3 (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 -3.511407254781429%；最差改善 -3.511407254781429%。

F1->F3 (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 5.752966264932069%；最差改善 5.752966264932069%。

U1->U3 (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 2.9953593931588585%；最差改善 2.9953593931588585%。

A3->F3 (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 6.1386132256293635%；最差改善 6.1386132256293635%。

A3->U3 (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 3.3922901329497823%；最差改善 3.3922901329497823%。

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
  }
}
```
