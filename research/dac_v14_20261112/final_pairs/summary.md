# 配对结果复算

来源：Server v13 final frozen evaluation, audited in paper/dac2027; read-only post-registration reanalysis

本报告是已有 CSV 的算术复核，未重新审计原始路由。

| 架构/布局 | 预定配对 | 左侧合法 | 右侧合法 | 双方合法 | 改善 | 持平 | 退化 |
|---|---:|---:|---:|---:|---:|---:|---:|
| cb_o/p0 | 42 | 11 | 11 | 11 | 0 | 11 | 0 |
| cb_o/p1 | 42 | 12 | 12 | 12 | 0 | 12 | 0 |
| hybrid_o/p0 | 42 | 24 | 23 | 23 | 7 | 9 | 7 |
| hybrid_o/p1 | 42 | 24 | 24 | 24 | 11 | 9 | 4 |
| sb/p0 | 42 | 23 | 23 | 23 | 9 | 4 | 10 |
| sb/p1 | 42 | 24 | 24 | 24 | 7 | 6 | 11 |

总体：`{"declared_pairs": 252, "left_legal": 118, "right_legal": 117, "both_legal": 117, "improved": 34, "tie": 51, "degraded": 32, "status_pairs_left_then_right": {"failed|failed": 92, "failed|timeout": 3, "legal|failed": 1, "legal|legal": 117, "timeout|timeout": 39}}`

总体配对数不能作为独立样本数。任何合法配对收益均应与完整状态表同时报告。
