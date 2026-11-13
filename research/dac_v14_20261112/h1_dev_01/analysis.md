# H1 开发集配对结果

Development times only; no ratio to historical timing; formal rotated repeats pending.

每个电路为单seed；无置信区间和盲测外推。合法状态要求FULL和原范围独立审计通过。

| 电路 | 臂 | 状态 | CPD(ns) | 迭代 | 规划(s) | 完整进程(s) | SB占用 | CB占用 |
|---|---|---|---:|---:|---:|---:|---:|---:|
| spmv | A0 | legal | 7.0347 | 17 | — | — | 0 | 967 |
| spmv | R1 | legal | 7.04599 | 19 | — | — | 1 | 967 |
| spmv | F | thread_constraint_violated | — | — | 3.219334 | 20.65748757123947 | — | — |
| spmv | M | thread_constraint_violated | — | — | 3.098105 | 20.60557647794485 | — | — |
| softmax | A0 | legal | 8.97575 | 13 | — | — | 6 | 713 |
| softmax | R1 | legal | 8.97575 | 13 | — | — | 6 | 713 |
| softmax | F | thread_constraint_violated | — | — | 4.276121 | 40.74021386355162 | — | — |
| softmax | M | thread_constraint_violated | — | — | 4.272902 | 40.34014644101262 | — | — |

R1->F: 双方合法 0/2；按电路CPD几何均值改善 None%；最差改善 None%。

R1->M: 双方合法 0/2；按电路CPD几何均值改善 None%；最差改善 None%。

A0->M: 双方合法 0/2；按电路CPD几何均值改善 None%；最差改善 None%。
