# DAC2027 论文初稿交付

本目录是独立论文工作区。完整稿、证据表及收尾记录在此编写；运行中的实验、冻结源码和执行脚本均不修改。

## 本轮交付

- [论文PDF](build/main.pdf)：IEEE双栏10pt，正文6页、参考文献1页，包含实际正文、公式、主结果/失败覆盖表、机制案例和严格计时图。
- [LaTeX源码](main.tex) 与 [99词英文摘要](abstract.txt)。题目为 **Reachability-Constrained Shared-Crossing Planning for 3D FPGA Routing**。
- [主张—证据表](claims_evidence.md)：17项主张，逐项定位实现、实验来源、覆盖及限制。
- [机制分析与受控消融设计](mechanisms_and_ablation.md)：一改善一退化；同候选表/同static缓存下的top-1与DP对照，12小时小规模预算，未启动。
- [原13项要求核查](acceptance_13.md)：已完成证据与剩余最终验收明确区分。
- [架构排序逐seed复核](data/ranking_seed_audit.json)：从角色记录独立重算共同完整集合和84项数值比较，展示种子敏感性。
- [关键参考文献核对](reference_audit.md)：VTR版本、LaZagna原始基线、Flatland与H3D归属及其适用范围。
- [证据归档](build/dac2027-evidence-20261110.tar.gz)及[逐文件读回复核](data/final_archive_verification.json)：18,884份归档成员与嵌入摘要清单全部一致；大型图、packed网表、route及逐net审计仍在共享盘原路径。
- [注册信息与投稿判断](submission_checklist.md)：官方日期换算、内部里程碑、匿名/作者信息缺口，以及当前较高投稿风险。
- [当前队列与条件ETA](queue_eta.md)：唯一协调器和当前角色的只读凭据、历史依据及剩余时间场景。
- [数据快照](data/evidence_snapshot.json)、[主结果CSV](data/main_results.csv)、[完整主测试覆盖CSV](data/coverage.csv)、[核验回执](build/verification.json)。
- [证据核验范围](evidence_audit.md)：11,061份小文件/执行文件与3,183份大文件摘要均已核对，1,136次运行记录已核对；另附两例逐连接延迟分析。大文件清单不含宽度阶段。
- [比较口径补充核验](comparison_contracts.md)：40图的既有物理清单、552个合法执行的配对输入、180个串行进程；新增R1-off/B2计时对照及2D线资源残余差异。
- [实际工具链复现映射](toolchain_reproduction.md)：A0/R1/B2/P1源码、补丁和构建选项；附实际P1串行补丁及验证回执，避免误用旧native或placement快照。

固定布局宽度诊断已接入最终登记分析，完整分母与缺失结果见[宽度诊断结果](paired_width_results.md)。其余章节使用已完成的严格主测试、串行计时和平衡敏感性。逐项收尾结果及尚未满足的要求见[收尾报告](final_report.md)；本文尚未上传投稿系统。

## 构建与复核

在本目录执行 `bash build.sh`。已有标准TeX环境时使用pdflatex两遍；当前环境用独立下载的Tectonic 0.17.0构建成功。IEEEtran.cls保留CTAN原始许可，版本以文件头为准。依赖为IEEEtran、fontenc、amsmath、amssymb、graphicx、url，所有引用在正文的thebibliography内，无BibTeX依赖。

本机Tectonic位于 `tools/tectonic`；该下载文件和临时PDF检查工具排除出Git，未修改研究环境或实验二进制。换环境可直接安装常规TeX发行版或单独提供Tectonic。编译保留少量Underfull排版警告，不存在Overfull越栏、缺失引用或字体替代；字体嵌入及页数由核验脚本检查。

在项目根目录执行：

```sh
python3 paper/dac2027/extract_evidence.py
python3 paper/dac2027/analyze_connection_changes.py
.venv-lazagna/bin/python paper/dac2027/render_runtime.py
bash paper/dac2027/build.sh
.venv-lazagna/bin/python paper/dac2027/verify_draft.py
```

提取器仅读取已结束证据，写入本目录；运行它会刷新本目录的数据快照。该脚本不调用VPR、不修改冻结配置、不启动新的实验。绘图用已有matplotlib，验证用已有pypdf。校验重算均值/串行中位数比、核对93份主来源摘要及补充机制来源、四份机制配对检查、PDF结构和字体，不代替全量RRG/route最终验收。

元数据核验回执已随稿保存，无需每次构建重新读取1.21 GiB原件。确需刷新时执行 `ionice -c 3 nice -n 19 python3 paper/dac2027/audit_closed_metadata.py`；正常构建只核对回执绑定。逐连接分析排除逻辑内部延迟，不是最终guide采用率统计。

比较口径回执由 `ionice -c 3 nice -n 19 python3 paper/dac2027/audit_comparison_contracts.py` 产生，仅读模型清单、布局坐标和运行记录，不解析大图。文稿验证覆盖A0、B2、R1-off三类串行比值，并核对该回执的直接来源。

工具链回执由 `ionice -c 3 nice -n 19 python3 paper/dac2027/audit_toolchain_provenance.py` 产生，不构建或运行VPR。`provenance/`中的补丁是冻结源码的导出，不能应用到当前实验工作树；搬迁重建边界见对应说明。

核验通过后，用 `python3 paper/dac2027/package_draft.py --version YYYYMMDD-vN` 生成新的版本包、清单和SHA256SUMS。已存在的同名包不会覆盖；包内包含可编译源码、图、证据快照与PDF，不打包编译器或实验原件。当前包路径记录在[delivery_manifest.json](delivery_manifest.json)。

[独立解包构建回执](data/packaged_build_check.json)：v12论文包在临时目录中使用本机独立提供的Tectonic编译成功，7页的提取文本与包内PDF一致。测试依赖当前用户已有TeX缓存，并不证明隔离网络环境或二进制逐位复现；较新交付包含同一论文源码和图，以及额外的本回执和测试脚本。

## 当前研究判断

已观察到条件性时序收益，也观察到明显退化与运行成本。完整双基线各面板仅覆盖2–4个电路；10个有效串行组都比A0慢；架构共同完整集合仅一个电路，无严格排名反转。当前最强表述是“有限共享跨层规划方法及其受控评估”，不能包装为普遍性能优势。

未解决的关键缺口：完整逐pin出口与层方向物理审计、干净环境位级重建、DP独立因果消融、最终逐连接guide匹配；作者/COI及相关稿件信息。科学扩展若不执行，要保留限制，不以继续追求正收益替代停止条件。归档状态以 `data/final_archive_receipt.json` 及 `data/final_archive_verification.json` 为准；大型原件仍保留在共享盘。
