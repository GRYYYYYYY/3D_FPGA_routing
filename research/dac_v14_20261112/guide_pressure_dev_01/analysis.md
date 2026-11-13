# 独立机制开发集配对结果

Development times only; no ratio to historical timing; formal rotated repeats pending.

每个电路为单seed；无置信区间和盲测外推。合法状态要求FULL和原范围独立审计通过。分母始终包含全部登记电路；未结束/未审计/缺失单列，manifest运行状态需结合实时进程核验。

| 电路 | 臂 | 状态 | CPD(ns) | 迭代 | 规划(s) | 完整进程(s) | SB占用 | CB占用 |
|---|---|---|---:|---:|---:|---:|---:|---:|
| eltwise_layer | A0 | legal | 9.93208 | 43 | — | — | 127 | 956 |
| eltwise_layer | R1 | legal | 6.96208 | 46 | — | — | 134 | 958 |
| eltwise_layer | A1 | legal | 6.0181 | 22 | — | 26.31660781800747 | 243 | 1144 |
| eltwise_layer | F1 | legal | 6.20393 | 19 | — | 26.896897975355387 | 223 | 1144 |
| eltwise_layer | U1 | legal | 6.20393 | 22 | — | 27.36837073788047 | 206 | 1123 |
| eltwise_layer | Tf1 | legal | 6.70679 | 21 | — | 27.017238598316908 | 253 | 1156 |
| eltwise_layer | W0 | legal | 6.0181 | 22 | 1.076187 | 26.766226090490818 | 243 | 1144 |
| eltwise_layer | W1 | legal | 6.0181 | 21 | 1.09377 | 26.914801474660635 | 194 | 1118 |
| attention_layer | A0 | failed | — | — | — | — | — | — |
| attention_layer | R1 | failed | — | — | — | — | — | — |
| attention_layer | A1 | legal | 12.6638 | 37 | — | 78.30619978532195 | 740 | 2307 |
| attention_layer | F1 | legal | 12.6638 | 49 | — | 83.46345590427518 | 727 | 2299 |
| attention_layer | U1 | legal | 12.6638 | 49 | — | 81.86136950552464 | 727 | 2299 |
| attention_layer | Tf1 | legal | 12.6638 | 49 | — | 83.54972702637315 | 727 | 2299 |
| attention_layer | W0 | legal | 12.6638 | 37 | 1.801065 | 80.80501272156835 | 740 | 2307 |
| attention_layer | W1 | legal | 12.6638 | 49 | 1.899762 | 84.4034906513989 | 727 | 2299 |

R1->W0 (mechanism_diagnostic_not_method_benefit): 双方合法 1/2；按电路CPD几何均值改善 13.558878955714393%；最差改善 13.558878955714393%。

A0->W0 (mechanism_diagnostic_not_method_benefit): 双方合法 1/2；按电路CPD几何均值改善 39.407455437330356%；最差改善 39.407455437330356%。

R1->W1 (method_or_reproduction): 双方合法 1/2；按电路CPD几何均值改善 13.558878955714393%；最差改善 13.558878955714393%。

A0->W1 (method_or_reproduction): 双方合法 1/2；按电路CPD几何均值改善 39.407455437330356%；最差改善 39.407455437330356%。

A0->A1 (method_or_reproduction): 双方合法 1/2；按电路CPD几何均值改善 39.407455437330356%；最差改善 39.407455437330356%。

A1->F1 (method_or_reproduction): 双方合法 2/2；按电路CPD几何均值改善 -1.5321878260928345%；最差改善 -3.08785164752996%。

A1->U1 (method_or_reproduction): 双方合法 2/2；按电路CPD几何均值改善 -1.5321878260928345%；最差改善 -3.08785164752996%。

F1->U1 (method_or_reproduction): 双方合法 2/2；按电路CPD几何均值改善 0.0%；最差改善 0.0%。

U1->Tf1 (method_or_reproduction): 双方合法 2/2；按电路CPD几何均值改善 -3.97379829337976%；最差改善 -8.105507315524196%。

A1->Tf1 (method_or_reproduction): 双方合法 2/2；按电路CPD几何均值改善 -5.566872173157256%；最差改善 -11.443645004237224%。

F1->Tf1 (method_or_reproduction): 双方合法 2/2；按电路CPD几何均值改善 -3.97379829337976%；最差改善 -8.105507315524196%。

A1->W0 (mechanism_diagnostic_not_method_benefit): 双方合法 2/2；按电路CPD几何均值改善 0.0%；最差改善 0.0%。

A1->W1 (method_or_reproduction): 双方合法 2/2；按电路CPD几何均值改善 0.0%；最差改善 0.0%。

Tf1->W1 (method_or_reproduction): 双方合法 2/2；按电路CPD几何均值改善 5.273313548616009%；最差改善 0.0%。

U1->W1 (method_or_reproduction): 双方合法 2/2；按电路CPD几何均值改善 1.5090660990357274%；最差改善 0.0%。

候选/成本表诊断（64-bit非密码学fingerprint，用于排查，不替代输入SHA和合法性审计）：

```json
{}
```
