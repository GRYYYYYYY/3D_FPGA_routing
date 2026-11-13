# 独立机制开发集配对结果

Development times only; no ratio to historical timing; formal rotated repeats pending.

每个电路为单seed；无置信区间和盲测外推。合法状态要求FULL和原范围独立审计通过。分母始终包含全部登记电路；未结束/未审计/缺失单列，manifest运行状态需结合实时进程核验。

| 电路 | 臂 | 状态 | CPD(ns) | 迭代 | 规划(s) | 完整进程(s) | SB占用 | CB占用 |
|---|---|---|---:|---:|---:|---:|---:|---:|
| eltwise_layer | A0 | legal | 9.93208 | 43 | — | — | 127 | 956 |
| eltwise_layer | R1 | legal | 6.96208 | 46 | — | — | 134 | 958 |
| eltwise_layer | F | legal | 6.96208 | 46 | 0.922732 | 28.465660385787487 | 134 | 958 |
| eltwise_layer | V | legal | 6.37264 | 34 | 1.331446 | 27.81700187548995 | 84 | 972 |
| eltwise_layer | D | legal | 6.96208 | 46 | 1.465067 | 29.12344966828823 | 134 | 958 |
| eltwise_layer | R | legal | 6.37264 | 34 | 1.365048 | 27.618008200079203 | 84 | 972 |

R1->F (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 0.0%；最差改善 0.0%。

F->V (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 8.466435318180787%；最差改善 8.466435318180787%。

A0->V (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 35.83781040829312%；最差改善 35.83781040829312%。

F->D (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 0.0%；最差改善 0.0%。

A0->D (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 29.903101867886672%；最差改善 29.903101867886672%。

F->R (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 8.466435318180787%；最差改善 8.466435318180787%。

A0->R (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 35.83781040829312%；最差改善 35.83781040829312%。

V->D (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 -9.2495417911572%；最差改善 -9.2495417911572%。

V->R (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 0.0%；最差改善 0.0%。

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
