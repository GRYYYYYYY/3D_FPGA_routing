# 独立机制开发集配对结果

Development times only; no ratio to historical timing; formal rotated repeats pending.

每个电路为单seed；无置信区间和盲测外推。合法状态要求FULL和原范围独立审计通过。

| 电路 | 臂 | 状态 | CPD(ns) | 迭代 | 规划(s) | 完整进程(s) | SB占用 | CB占用 |
|---|---|---|---:|---:|---:|---:|---:|---:|
| spmv | A0 | legal | 7.0347 | 17 | — | — | 0 | 967 |
| spmv | R1 | legal | 7.04599 | 19 | — | — | 1 | 967 |
| spmv | F | legal | 7.04599 | 19 | 3.175152 | 20.202382881194353 | 1 | 967 |
| spmv | H | legal | 7.04234 | 15 | 3.463557 | 20.703287459909916 | 1 | 967 |
| spmv | N | legal | 7.04599 | 15 | 3.214922 | 20.50427581742406 | 0 | 967 |
| spmv | G | legal | 7.04599 | 17 | 2.958201 | 19.95473724603653 | 0 | 967 |
| softmax | A0 | legal | 8.97575 | 13 | — | — | 6 | 713 |
| softmax | R1 | legal | 8.97575 | 13 | — | — | 6 | 713 |
| softmax | F | legal | 8.97575 | 13 | 4.324609 | 42.19947720691562 | 6 | 713 |
| softmax | H | legal | 8.97575 | 13 | 4.149166 | 40.85246507450938 | 6 | 713 |
| softmax | N | legal | 8.97575 | 13 | 4.135004 | 39.24154060333967 | 6 | 713 |
| softmax | G | legal | 8.97575 | 13 | 4.063627 | 40.69442665576935 | 6 | 713 |

R1->F: 双方合法 2/2；按电路CPD几何均值改善 0.0%；最差改善 0.0%。

F->H: 双方合法 2/2；按电路CPD几何均值改善 0.025904612555649464%；最差改善 0.0%。

A0->H: 双方合法 2/2；按电路CPD几何均值改善 -0.05428750891942613%；最差改善 -0.10860448917509036%。

F->N: 双方合法 2/2；按电路CPD几何均值改善 0.0%；最差改善 0.0%。

A0->N: 双方合法 2/2；按电路CPD几何均值改善 -0.08021290031612338%；最差改善 -0.16049014172601073%。

F->G: 双方合法 2/2；按电路CPD几何均值改善 0.0%；最差改善 0.0%。

A0->G: 双方合法 2/2；按电路CPD几何均值改善 -0.08021290031612338%；最差改善 -0.16049014172601073%。

候选/成本表诊断（64-bit非密码学fingerprint，用于排查，不替代输入SHA和合法性审计）：

```json
{
  "softmax F/H": {
    "reference_count": 43,
    "variant_count": 43,
    "exact_sequence_equal": true,
    "first_mismatch": null
  },
  "softmax F/N": {
    "reference_count": 43,
    "variant_count": 43,
    "exact_sequence_equal": true,
    "first_mismatch": null
  },
  "spmv F/H": {
    "reference_count": 88,
    "variant_count": 88,
    "exact_sequence_equal": true,
    "first_mismatch": null
  },
  "spmv F/N": {
    "reference_count": 88,
    "variant_count": 88,
    "exact_sequence_equal": true,
    "first_mismatch": null
  }
}
```
