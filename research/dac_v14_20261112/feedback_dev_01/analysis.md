# 独立机制开发集配对结果

Development times only; no ratio to historical timing; formal rotated repeats pending.

每个电路为单seed；无置信区间和盲测外推。合法状态要求FULL和原范围独立审计通过。分母始终包含全部登记电路；未结束/未审计/缺失单列，manifest运行状态需结合实时进程核验。

| 电路 | 臂 | 状态 | CPD(ns) | 迭代 | 规划(s) | 完整进程(s) | SB占用 | CB占用 |
|---|---|---|---:|---:|---:|---:|---:|---:|
| spmv | A0 | legal | 7.0347 | 17 | — | — | 0 | 967 |
| spmv | R1 | legal | 7.04599 | 19 | — | — | 1 | 967 |
| spmv | F | legal | 7.04599 | 19 | 3.279815 | 21.50534227862954 | 1 | 967 |
| spmv | U | legal | 7.04599 | 19 | 5.562126 | 22.809336494654417 | 1 | 967 |
| spmv | X | legal | 7.0347 | 17 | 3.963454 | 21.256069526076317 | 0 | 967 |
| softmax | A0 | legal | 8.97575 | 13 | — | — | 6 | 713 |
| softmax | R1 | legal | 8.97575 | 13 | — | — | 6 | 713 |
| softmax | F | legal | 8.97575 | 13 | 4.176559 | 42.75079130753875 | 6 | 713 |
| softmax | U | legal | 8.97575 | 13 | 4.154928 | 40.39416453242302 | 6 | 713 |
| softmax | X | legal | 8.97575 | 13 | 4.764088 | 41.94862434267998 | 7 | 712 |

R1->F (method_or_reproduction): 双方合法 2/2；按电路CPD几何均值改善 0.0%；最差改善 0.0%。

F->U (method_or_reproduction): 双方合法 2/2；按电路CPD几何均值改善 0.0%；最差改善 0.0%。

A0->U (method_or_reproduction): 双方合法 2/2；按电路CPD几何均值改善 -0.08021290031612338%；最差改善 -0.16049014172601073%。

F->X (transaction_diagnostic_not_method_benefit): 双方合法 2/2；按电路CPD几何均值改善 0.08014861079084223%；最差改善 0.0%。

A0->X (transaction_diagnostic_not_method_benefit): 双方合法 2/2；按电路CPD几何均值改善 0.0%；最差改善 0.0%。

候选/成本表诊断（64-bit非密码学fingerprint，用于排查，不替代输入SHA和合法性审计）：

```json
{
  "spmv F/H": {
    "reference_count": 88,
    "variant_count": 0,
    "exact_sequence_equal": false,
    "first_mismatch": null
  },
  "spmv F/N": {
    "reference_count": 88,
    "variant_count": 0,
    "exact_sequence_equal": false,
    "first_mismatch": null
  },
  "softmax F/H": {
    "reference_count": 43,
    "variant_count": 0,
    "exact_sequence_equal": false,
    "first_mismatch": null
  },
  "softmax F/N": {
    "reference_count": 43,
    "variant_count": 0,
    "exact_sequence_equal": false,
    "first_mismatch": null
  }
}
```
