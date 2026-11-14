# 严格实验工具链与源码复现映射

本记录绑定实际严格实验使用的程序；没有重新构建或运行求解器。完整二进制摘要、源码路径、编译规则及验证范围见[data/toolchain_provenance.json](data/toolchain_provenance.json)。不要用旧manifest中的“计划完成”或版本字符串代替这一映射。

## 必须区分的源码

| 严格实验角色 | 上游固定提交 | 应用的补丁/控制 | 当前二进制SHA256前缀 |
| --- | --- | --- | --- |
| A0：官方VTR派生串行基线 | `0b912334fdd83bb754b302146ac0d1ec9edc9a0e` | 顶层源码无修改；串行构建选项；不是早期开发分支 | `a3fe24c59b8862ec` |
| R1：本文路由器 | 同上 | [architecture_r1.patch](provenance/architecture_r1.patch) | `1441c77e25e6a4f` |
| R1-off | 与R1完全相同程序 | `VPR_H3D_MODE=off`；按登记保持其他统计/编码设置 | 与R1相同 |
| B2：现代LaZagna工具端口 | `5abd3acaa603e037ec390fa545b04301f13d57e0` | [lazagna_b2.patch](provenance/lazagna_b2.patch)，构建可移植性修复 | `0a5b314bcacdc619` |
| P1：Flatland布局及串行分区桥接 | `84ba44acf1bad597bc5a9d1f615415870e178a86` | [placement_p1_serial.patch](provenance/placement_p1_serial.patch)＋[bridge](provenance/run_serial_triton_bridge.py) | `ec0877666894210` |
| 分区程序：OpenROAD/TritonPart | `a008522d88b669ac4c985609533cf5a3d2649222` | [partition.patch](provenance/partition.patch) | `d072d1f1acac9cea` |

历史`patches/snapshot_20261109/native.patch`来自`vendor/vtr`的已有算法开发工作树，**不是严格A0的补丁**。正式R1使用的是`vendor/vtr-architecture-src`及上表architecture_r1补丁；这两个开发树的H3D实现不能混用。

同样，历史快照中的`placement_p1.patch`描述`vendor/beyond-flatland-src`，其桥接路径不是严格实验最终使用的串行bridge。新的`placement_p1_serial.patch`只导出冻结源码的现状，未修改它。P1独立源码副本没有`.git`；在那里执行`git rev-parse HEAD`会向上找到项目根仓库，得到无关提交。P1提交依据应为固定来源、逐blob核对和构建路径，而不是这个错误的HEAD。

LaZagna论文时期B1仍是外部发表结果，使用其作者的2D分母；它不是上表B2二进制，也不提供本地R1/B1直接比值。B2历史版本字符串仍可显示8.1.0-dev，不能凭字符串把它当成原论文时期工具。

## 实际编译配置

四个VPR程序均由GNU C++ 11.4.0构建，实际核心编译规则均为`-O3 -DNDEBUG`，Tatum执行引擎设为serial。B2的CMakeCache中build type为空，但生成规则明确使用Release及`-O3`；不能把空字符串解释成未优化。

| 角色 | C++标准 | IPO/LTO | Cap’n Proto/Interchange | Parmys |
| --- | --- | --- | --- | --- |
| A0 | C++20 | off | ON / ON | ON |
| R1 | C++20 | off | OFF / OFF | OFF |
| B2 | C++17 | off | OFF / OFF | OFF |
| P1 | C++17 | auto，实际规则含`-flto` | OFF / OFF | OFF |

这些程序不是同一发行二进制，也不是完全相同构建。A0/R1仍存在可选前端/Interchange配置差异；因此串行实验保留同一R1程序的关闭算法控制。它说明同程序启用算法的成本，但不能隔离共享DP相对于独立top-1的贡献。P1只提供布局及setup，不用其构建差异推断路由加速。

## 本轮验证了什么

- A0真实Git根和提交一致，顶层tracked源码无差异。已有子模块核查中的初次失败与后续nested澄清均保留，不能删除初次报告或声称所有子模块都是相同构建。
- R1、B2的固定提交、全部登记修改/新增文件、补丁以及程序SHA256一致；OpenROAD四个修改文件和分区补丁一致。登记22项运行依赖的当前摘要匹配。
- P1的`vpr`、`libs`、`CMakeLists.txt`和`cmake`范围内1,688个现存上游tracked文件/符号链接已与Git blob核对。三个文件有登记修改；两个Cap’n Proto的Bazel构建文件未复制，现已作为删除纳入补丁。它们所属功能在P1关闭。两个子模块gitlink保留固定提交，但本轮不声称重新核验其全部内容。
- P1补丁在临时仓库以固定上游blob为输入，实际完成`git apply --check`、应用及逐文件比较：[回执](data/p1_patch_roundtrip.json)。这证明补丁重建范围内的源码一致，**不是干净重建二进制或位级可复现的证明**。

## 重建与搬迁边界

在独立目录取对应上游提交、配置其登记依赖，再应用表中该角色的补丁。保留CMakeCache、生成的编译规则、编译器版本和新的二进制摘要。未验证的精简构建命令不应替代已记录的实际选项。

P1的源码补丁和Python bridge保留原共享工作区的绝对路径。切换账号但继续使用同一路径时，这些文件身份不变；迁到另一目录或机器时，须显式修改桥接路径和依赖目录，并作为新的派生构建登记，不能声称二进制身份与当前严格实验相同。

运行依赖清单覆盖登记的`ldd`解析，不证明所有可能的动态加载已被穷尽观察。完整干净环境重建、所有子模块/生成文件的封装与全量实验原件归档仍属于最终工件工作。当前源码补丁保存在论文独立目录，原实验、二进制、执行脚本和已上传历史快照均未修改。
