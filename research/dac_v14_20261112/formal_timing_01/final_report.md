# Sealed formal timing: A0 / old R1 / full-feedback closure-view U

Five seen, mutually legal circuits; Hybrid-O/P0/W100, seed 11, three rotated orders. All 45 roles legal; no gated cases. Each complete route and quality record passed the registered reference-reuse gate. Inputs were sealed after execution. Shared host; study heavy jobs excluded; fixed CPU 0; uniform input prewarming. This is neither a blind cohort nor a success-rate experiment.

| Circuit | A0 process s | R1 process s | U process s | U/A0 | U/R1 | R1 planning s | U planning s |
|---|---:|---:|---:|---:|---:|---:|---:|
| spmv | 17.752558 | 21.210177 | 19.107116 | 1.076302 | 0.900847 | 3.300668 | 1.048257 |
| softmax | 37.082038 | 41.737287 | 39.632508 | 1.068779 | 0.949571 | 4.312108 | 1.830258 |
| eltwise_layer | 26.464123 | 32.279620 | 27.868817 | 1.053079 | 0.863356 | 4.990209 | 1.374478 |
| bnn | 263.017871 | 549.419369 | 283.604823 | 1.078272 | 0.516190 | 268.753776 | 11.019850 |
| gemm_layer | 1278.617352 | 1642.931148 | 1325.215228 | 1.036444 | 0.806616 | 363.256998 | 28.515443 |

Circuit-geometric U/R1 process-time reduction: 21.010567%; U/A0 overhead: 6.245726%. Every circuit is faster than old R1 and slower than A0. These ratios include guide-feedback differences as well as reuse and do not isolate the cache contribution.

CSV retains legal CPD, iterations, actual SB/CB occupancy, process median/max, planning/router components and peak RSS median/max. All raw repetitions, GNU time counters and paired ratios remain in analysis.json. RSS is GNU time peak resident set size in Linux KiB, not a simultaneous process-tree sum. Component times are never added to full-process wall. Attention remains failed in the separate six-circuit quality denominator. Tf, pressure and retained-prefix variants are outside this timing claim.
