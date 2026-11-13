# 独立机制开发集配对结果

Development times only; no ratio to historical timing; formal rotated repeats pending.

每个电路为单seed；无置信区间和盲测外推。合法状态要求FULL和原范围独立审计通过。分母始终包含全部登记电路；未结束/未审计/缺失单列，manifest运行状态需结合实时进程核验。

| 电路 | 臂 | 状态 | CPD(ns) | 迭代 | 规划(s) | 完整进程(s) | SB占用 | CB占用 |
|---|---|---|---:|---:|---:|---:|---:|---:|
| spmv | A0 | legal | 7.0347 | 17 | — | — | 0 | 967 |
| spmv | R1 | legal | 7.04599 | 19 | — | — | 1 | 967 |
| spmv | U | legal | 7.04599 | 19 | — | 22.809336494654417 | 1 | 967 |
| spmv | A1 | legal | 7.0347 | 16 | — | 17.14693160355091 | 2 | 969 |
| spmv | F1 | legal | 7.0347 | 16 | — | 19.503885928541422 | 3 | 968 |
| spmv | U1 | legal | 7.0347 | 16 | — | 18.450009513646364 | 3 | 968 |
| spmv | F1c | legal | 7.0347 | 16 | 0.858922 | 18.303581319749355 | 3 | 968 |
| spmv | A3 | legal | 7.04234 | 15 | — | 17.048507675528526 | 2 | 969 |
| spmv | F3 | legal | 7.2843 | 16 | 0.851119 | 18.201476231217384 | 2 | 969 |
| spmv | U3 | legal | 7.2843 | 16 | 0.870732 | 18.353456240147352 | 2 | 969 |
| softmax | A0 | legal | 8.97575 | 13 | — | — | 6 | 713 |
| softmax | R1 | legal | 8.97575 | 13 | — | — | 6 | 713 |
| softmax | U | legal | 8.97575 | 13 | — | 40.39416453242302 | 6 | 713 |
| softmax | A1 | legal | 8.97575 | 12 | — | 36.64830205217004 | 14 | 721 |
| softmax | F1 | legal | 8.97575 | 12 | — | 39.74233487248421 | 14 | 721 |
| softmax | U1 | legal | 8.97575 | 12 | — | 38.48994540423155 | 14 | 721 |
| softmax | F1c | legal | 8.97575 | 12 | 1.757299 | 38.5341061912477 | 14 | 721 |
| softmax | A3 | legal | 8.97575 | 13 | — | 35.472898814827204 | 10 | 717 |
| softmax | F3 | legal | 8.97575 | 13 | 1.775143 | 39.190189607441425 | 9 | 716 |
| softmax | U3 | legal | 8.97575 | 13 | 1.73369 | 37.536448542028666 | 9 | 716 |
| bnn | A0 | legal | 13.6074 | 18 | — | — | 98 | 5067 |
| bnn | R1 | legal | 13.4216 | 35 | — | — | 86 | 5072 |
| bnn | U | legal | 13.4216 | 19 | — | 598.9714375287294 | 94 | 5066 |
| bnn | A1 | legal | 13.6074 | 18 | — | 254.29703213647008 | 257 | 5219 |
| bnn | F1 | legal | 13.5998 | 17 | — | 258.8826586343348 | 276 | 5229 |
| bnn | U1 | legal | 13.5998 | 17 | — | 265.6004801467061 | 268 | 5216 |
| bnn | F1c | legal | 13.5998 | 17 | 9.723219 | 266.7271270044148 | 276 | 5229 |
| bnn | A3 | legal | 13.2434 | 18 | — | 259.3236825019121 | 273 | 5226 |
| bnn | F3 | legal | 13.7856 | 18 | 9.763089 | 267.89385084435344 | 255 | 5231 |
| bnn | U3 | legal | 13.5998 | 17 | 10.437678 | 270.0903090015054 | 271 | 5238 |

R1->F1c (method_or_reproduction): 双方合法 3/3；按电路CPD几何均值改善 -0.3869508068796268%；最差改善 -1.3277105561184888%。

A0->F1c (method_or_reproduction): 双方合法 3/3；按电路CPD几何均值改善 0.018620788089784845%；最差改善 0.0%。

R1->A3 (method_or_reproduction): 双方合法 3/3；按电路CPD几何均值改善 0.46173715836532736%；最差改善 0.0%。

A0->A3 (method_or_reproduction): 双方合法 3/3；按电路CPD几何均值改善 0.8638799836696687%；最差改善 -0.10860448917509036%。

R1->F3 (method_or_reproduction): 双方合法 3/3；按电路CPD几何均值改善 -2.0208789608816335%；最差改善 -3.3822074683614423%。

A0->F3 (method_or_reproduction): 双方合法 3/3；按电路CPD几何均值改善 -1.6087061608536013%；最差改善 -3.5481257196468885%。

R1->U3 (method_or_reproduction): 双方合法 3/3；按电路CPD几何均值改善 -1.5604641721683077%；最差改善 -3.3822074683614423%。

A0->U3 (method_or_reproduction): 双方合法 3/3；按电路CPD几何均值改善 -1.1501514860166928%；最差改善 -3.5481257196468885%。

A0->A1 (method_or_reproduction): 双方合法 3/3；按电路CPD几何均值改善 0.0%；最差改善 0.0%。

A1->F1 (method_or_reproduction): 双方合法 3/3；按电路CPD几何均值改善 0.018620788089784845%；最差改善 0.0%。

A1->U1 (method_or_reproduction): 双方合法 3/3；按电路CPD几何均值改善 0.018620788089784845%；最差改善 0.0%。

F1->U1 (method_or_reproduction): 双方合法 3/3；按电路CPD几何均值改善 0.0%；最差改善 0.0%。

U->U1 (method_or_reproduction): 双方合法 3/3；按电路CPD几何均值改善 -0.3869508068796268%；最差改善 -1.3277105561184888%。

F1->F1c (method_or_reproduction): 双方合法 3/3；按电路CPD几何均值改善 0.0%；最差改善 0.0%。

A1->A3 (method_or_reproduction): 双方合法 3/3；按电路CPD几何均值改善 0.8638799836696687%；最差改善 -0.10860448917509036%。

F1->F3 (method_or_reproduction): 双方合法 3/3；按电路CPD几何均值改善 -1.627630026481519%；最差改善 -3.5481257196468885%。

U1->U3 (method_or_reproduction): 双方合法 3/3；按电路CPD几何均值改善 -1.168989949247723%；最差改善 -3.5481257196468885%。

A3->F3 (method_or_reproduction): 双方合法 3/3；按电路CPD几何均值改善 -2.4941324555731725%；最差改善 -4.0941148043553754%。

A3->U3 (method_or_reproduction): 双方合法 3/3；按电路CPD几何均值改善 -2.0315818990642276%；最差改善 -3.435789808501144%。

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
  "softmax F/H": {
    "reference_count": 0,
    "variant_count": 0,
    "exact_sequence_equal": false,
    "first_mismatch": null
  },
  "softmax F/N": {
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
