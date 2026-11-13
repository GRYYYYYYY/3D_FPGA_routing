# 独立机制开发集配对结果

Development times only; no ratio to historical timing; formal rotated repeats pending.

每个电路为单seed；无置信区间和盲测外推。合法状态要求FULL和原范围独立审计通过。分母始终包含全部登记电路；未结束/未审计/缺失单列，manifest运行状态需结合实时进程核验。

| 电路 | 臂 | 状态 | CPD(ns) | 迭代 | 规划(s) | 完整进程(s) | SB占用 | CB占用 |
|---|---|---|---:|---:|---:|---:|---:|---:|
| eltwise_layer | A0 | legal | 9.93208 | 43 | — | — | 127 | 956 |
| eltwise_layer | R1 | legal | 6.96208 | 46 | — | — | 134 | 958 |
| eltwise_layer | F | legal | 6.96208 | 46 | 0.935743 | 28.26767434924841 | 134 | 958 |
| eltwise_layer | V | legal | 6.37264 | 34 | 1.42299 | 27.31737295165658 | 84 | 972 |
| eltwise_layer | N | legal | 7.88356 | 35 | 1.38159 | 28.170646585524082 | 138 | 955 |
| eltwise_layer | G | legal | 7.67462 | 37 | 0.973518 | 28.209823563694954 | 106 | 961 |
| eltwise_layer | Z | legal | 9.93208 | 43 | 1.371633 | 29.07274391502142 | 127 | 956 |

R1->F (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 0.0%；最差改善 0.0%。

F->V (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 8.466435318180787%；最差改善 8.466435318180787%。

A0->V (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 35.83781040829312%；最差改善 35.83781040829312%。

F->N (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 -13.235699675958902%；最差改善 -13.235699675958902%。

A0->N (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 20.62528694895731%；最差改善 20.62528694895731%。

F->G (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 -10.234585066531832%；最差改善 -10.234585066531832%。

A0->G (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 22.728975199555368%；最差改善 22.728975199555368%。

F->Z (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 -42.65966492772273%；最差改善 -42.65966492772273%。

A0->Z (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 0.0%；最差改善 0.0%。

V->N (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 -23.70948303999598%；最差改善 -23.70948303999598%。

V->G (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 -20.43077908056945%；最差改善 -20.43077908056945%。

V->Z (method_or_reproduction): 双方合法 1/1；按电路CPD几何均值改善 -55.855030254337294%；最差改善 -55.855030254337294%。

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
    "variant_count": 227,
    "exact_sequence_equal": false,
    "first_mismatch": null
  }
}
```
