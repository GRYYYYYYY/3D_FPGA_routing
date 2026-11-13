# 独立机制开发集配对结果

Development times only; no ratio to historical timing; formal rotated repeats pending.

每个电路为单seed；无置信区间和盲测外推。合法状态要求FULL和原范围独立审计通过。分母始终包含全部登记电路；未结束/未审计/缺失单列，manifest运行状态需结合实时进程核验。

| 电路 | 臂 | 状态 | CPD(ns) | 迭代 | 规划(s) | 完整进程(s) | SB占用 | CB占用 |
|---|---|---|---:|---:|---:|---:|---:|---:|
| eltwise_layer | A0 | legal | 9.93208 | 43 | — | — | 127 | 956 |
| eltwise_layer | R1 | legal | 6.96208 | 46 | — | — | 134 | 958 |
| eltwise_layer | F | legal | 6.96208 | 46 | 4.846861 | 31.50833585858345 | 134 | 958 |
| eltwise_layer | H | legal | 8.07101 | 42 | 5.082453 | 32.535021498799324 | 170 | 953 |
| eltwise_layer | N | legal | 7.26027 | 67 | 5.116738 | 35.33877024427056 | 117 | 954 |
| eltwise_layer | G | legal | 7.69053 | 38 | 4.586327 | 32.18530246987939 | 139 | 960 |
| bnn | A0 | legal | 13.6074 | 18 | — | — | 98 | 5067 |
| bnn | R1 | legal | 13.4216 | 35 | — | — | 86 | 5072 |
| bnn | F | legal | 13.4216 | 35 | 261.710976 | 535.1760570183396 | 86 | 5072 |
| bnn | H | legal | 13.5998 | 20 | 260.216915 | 516.9162665233016 | 102 | 5068 |
| bnn | N | legal | 13.4216 | 21 | 261.419396 | 521.1474010199308 | 90 | 5071 |
| bnn | G | legal | 13.4292 | 26 | 259.972214 | 528.9615192189813 | 102 | 5063 |
| attention_layer | A0 | failed | — | — | — | — | — | — |
| attention_layer | R1 | failed | — | — | — | — | — | — |
| attention_layer | F | failed | — | — | 5.677649 | 686.9943988658488 | — | — |
| attention_layer | H | failed | — | — | 5.58097 | 684.9012407958508 | — | — |
| attention_layer | N | failed | — | — | 5.569013 | 673.4415727332234 | — | — |
| attention_layer | G | failed | — | — | 5.22719 | 680.4016527608037 | — | — |
| gemm_layer | A0 | legal | 13.2565 | 23 | — | — | 405 | 9440 |
| gemm_layer | R1 | legal | 13.1564 | 19 | — | — | 414 | 9433 |
| gemm_layer | F | legal | 13.1564 | 19 | 353.043751 | 1583.3431963063776 | 414 | 9433 |
| gemm_layer | H | legal | 13.2393 | 20 | 356.623324 | 1593.4448273293674 | 382 | 9442 |
| gemm_layer | N | legal | 13.1564 | 18 | 354.316415 | 1601.579399973154 | 382 | 9441 |
| gemm_layer | G | legal | 13.1564 | 22 | 349.358344 | 1580.4455163292587 | 393 | 9430 |

R1->F (method_or_reproduction): 双方合法 3/4；按电路CPD几何均值改善 0.0%；最差改善 0.0%。

F->H (method_or_reproduction): 双方合法 3/4；按电路CPD几何均值改善 -5.734087137604438%；最差改善 -15.92814216441063%。

A0->H (method_or_reproduction): 双方合法 3/4；按电路CPD几何均值改善 6.740360730142491%；最差改善 0.05585196290254224%。

F->N (method_or_reproduction): 双方合法 3/4；按电路CPD几何均值改善 -1.4077750567688785%；最差改善 -4.283059085790453%。

A0->N (method_or_reproduction): 双方合法 3/4；按电路CPD几何均值改善 10.556256955760512%；最差改善 0.7551012710745764%。

F->G (method_or_reproduction): 双方合法 3/4；按电路CPD几何均值改善 -3.3921827192782805%；最差改善 -10.463108726127812%。

A0->G (method_or_reproduction): 双方合法 3/4；按电路CPD几何均值改善 8.805968588215219%；最差改善 0.7551012710745764%。

候选/成本表诊断（64-bit非密码学fingerprint，用于排查，不替代输入SHA和合法性审计）：

```json
{
  "eltwise_layer F/H": {
    "reference_count": 87,
    "variant_count": 87,
    "exact_sequence_equal": true,
    "first_mismatch": null
  },
  "eltwise_layer F/N": {
    "reference_count": 87,
    "variant_count": 87,
    "exact_sequence_equal": true,
    "first_mismatch": null
  },
  "bnn F/H": {
    "reference_count": 836,
    "variant_count": 836,
    "exact_sequence_equal": true,
    "first_mismatch": null
  },
  "bnn F/N": {
    "reference_count": 836,
    "variant_count": 836,
    "exact_sequence_equal": true,
    "first_mismatch": null
  },
  "gemm_layer F/H": {
    "reference_count": 183,
    "variant_count": 183,
    "exact_sequence_equal": true,
    "first_mismatch": null
  },
  "gemm_layer F/N": {
    "reference_count": 183,
    "variant_count": 183,
    "exact_sequence_equal": true,
    "first_mismatch": null
  },
  "attention_layer F/H": {
    "reference_count": 54,
    "variant_count": 54,
    "exact_sequence_equal": true,
    "first_mismatch": null
  },
  "attention_layer F/N": {
    "reference_count": 54,
    "variant_count": 54,
    "exact_sequence_equal": true,
    "first_mismatch": null
  }
}
```
