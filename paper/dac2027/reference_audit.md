# 关键参考文献核对

核对日期：2026-11-10，北京时间。这里记录对正文关键归属的外部核查，不能代替最终投稿前的逐项文献与匿名性审阅。

| 正文引用或表述 | 直接来源及核对结论 | 边界 |
| --- | --- | --- |
| VTR 9增加3D支持 | [VTR官方变更记录](https://docs.verilogtorouting.org/en/latest/CHANGELOG/)将3D FPGA和RAD列在2024-12-23的v9.0.0新增内容中 | 实验固定的是正文给出的开发提交，并非宣称使用完全未修改的9.0.0发布版 |
| VTR 9和VTR 8的正式工具文献 | [VTR官方引用页面](https://verilogtorouting.org/download/)给出VTR 9论文及DOI 10.1145/3734798；[官方文献页](https://vtr-verilog-to-routing.readthedocs.io/en/latest/zreferences/)列出VTR 8的Murray等人论文 | 正文新增官方推荐的VTR 9论文，并保留变更记录以支持发布版本和3D特性归属 |
| 现代LaZagna的固定port | [固定提交的作者仓库页面](https://github.com/IY2002/vtr-verilog-to-routing/commit/5abd3acaa603e037ec390fa545b04301f13d57e0)能定位引用的VTR 9适配提交；本地源码、补丁与二进制对应见[工具链核查](toolchain_reproduction.md) | 上游提交名称及本地受控运行不等于该工具与官方原生VTR使用相同源码、构建选项或二进制 |
| LaZagna论文时期使用VTR 8.1 | [LaZagna v1实验设置](https://arxiv.org/html/2505.05579v1)明确写明PnR使用VTR 8.1 | 这描述作者原始实验，不能等同于本项目现代port的受控实验 |
| 历史SB基线的0.821、0.819、0.809 | 同一[论文v1表IV](https://arxiv.org/html/2505.05579v1#S4.T4)分别列出100%、66%、33% 3D SB的CPD几何均值，归一化到该论文自己的2D | 使用其Koios子集及分母；不能直接求与本地R1的配对比值 |
| LaZagna论文题名、作者与2025 ICCAD | [ICCAD 2025会议日程](https://confcats-event-sessions.s3.us-east-1.amazonaws.com/iccad25/uploads/ICCAD_2025_Program_v20.pdf)和[作者论文](https://arxiv.org/abs/2505.05579)支持正文参考文献 | [项目文档](https://lazagna.readthedocs.io/en/latest/source/about.html)给出的建议引用题名措辞不同；当前稿以会议日程和论文题名为准 |
| Escaping Flatland题名、作者与DAC 2026 | [DAC会议日程](https://63dac.conference-program.com/session/?sess=sess175)及[作者研究组发表列表](https://vlsicad.ucsd.edu/Publications/Conferences/)支持正文参考文献 | 它研究布局流程；其收益和架构排序不能归到本项目路由算法 |
| H3D面向face-to-face 3D IC全局路由并优化bonding terminal数量和位置 | [作者机构出版记录](https://research.cuhk.edu.hk/en/publications/h3d-heterogeneous-resources-aware-global-router-for-face-to-face-/)与[作者论文](https://www.cse.cuhk.edu.hk/~byu/papers/C297-ICCAD2025-3DRoute.pdf)支持这一概述 | 正文没有把其几何模型或性能数字当成本项目的结果或保证 |
| Boutros等人3D架构探索工作 | [作者论文](https://www.eecg.utoronto.ca/~vaughn/papers/fpt2023_3dfpgas.pdf)及[作者发表列表](https://www.eecg.toronto.edu/~vaughn/vaughn_betz_cv.pdf)核对作者、ICFPT 2023和198–208页 | 不能将其器件模型当作本实验的硅面积或功耗验证 |

H3D论文PDF在本轮网页直接打开时曾超时，但搜索结果返回作者站点论文摘要，机构出版记录可访问；未将本项标记为PDF全文独立复现。以上覆盖当前9项书目主要身份及关键归属；正式投稿前仍须重新检查链接、出版信息和匿名性。
