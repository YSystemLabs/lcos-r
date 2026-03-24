# LCOS-R 一阶段实验审计路线图（重审版）

**目的**：不是重复描述“理想中的实现应该是什么”，而是按可审计顺序核对当前仓库是否真的完成了一阶段实验，并判断哪些结论成立、哪些结论需要降级。

**使用方式**：
- 每一步都同时检查 3 件事：代码、输出、验收。
- 只有当该步的证据闭环成立，才打勾。
- 如果某步发现设计不合理，不继续“硬验收”，而是先改写该步目标与通过条件。

## 审计后修复状态（本轮已完成）

- [x] Pass 3 现在按任务级验证执行：`run_task_pruning()` 已从仅跑 `Q_star` 改为跑任务级 `Q_task` 变体，并在失败时回滚。
- [x] `Q_star` 核心测试数已补足到 10：新增“动作引用的谓词必须已声明”检查。
- [x] ManualOpt 已文件化：`data/manual_opt/stage_1.json` 到 `stage_4.json` 已成为真实输入，而不是源码硬编码。
- [x] 一阶段已基于修复后的代码重新运行：`results/raw/summary.json` 现记录 `q_star_total = 10`、`q_task_total = 41`。
- [x] Pass 3 逐任务验证已真实通过：`Expand+Rewrite` 在 S1-S4 的 `pass3_verified_rate = 100%`。
- [x] 一阶段报告出口已统一：仓库现只保留 `results/phase1_analysis.md` 作为唯一一阶段报告。

---

## 为什么重做路线图

旧版路线图不再适合作为验收依据，主要有 4 个问题：

1. 把“计划中的理想结构”和“仓库当前事实”混在一起，导致许多已完成标记无法直接追溯到证据。
2. 一些产物命名和实际仓库不一致，例如分析报告文件名、ManualOpt 配置位置、测试目录。
3. 一些验收条件写得过强，但当前实现是研究原型级，不应按完整系统口径验收。
4. 路线图默认“实现完成”，但当前更需要的是“逐步审计”，确认哪些 claim 真被代码和结果支撑。

因此，Phase 1 从现在开始采用下面这份**审计版路线图**。

---

## 审计总原则

每一步都回答 3 个问题：

1. **代码是否存在且行为与设计一致**
2. **输出是否真实生成且可复现**
3. **验收标准是否合理且有客观证据**

每一步的结论只允许是下面三种之一：

- `通过`：代码、输出、验收三者一致
- `部分通过`：核心目标达成，但存在口径漂移或证据不足
- `不通过`：代码或输出无法支撑该步 claim

---

## 步骤 0：路线图重构与审计基线

- [x] 完成

**目标**：把旧版“建设路线图”改写为“审计路线图”，后续所有勾选都基于仓库事实而不是预期描述。

**通过条件**：
- 路线图明确区分“设计目标”和“当前仓库事实”
- 后续步骤都能对应到真实文件、真实脚本、真实结果
- 不再使用“已完成”作为先验结论，而是通过审计逐步打勾

**当前结论**：通过。

---

## 步骤 1：Phase 1 研究问题与实验设计是否合理

- [x] 完成

**要检查什么**：
- 一阶段是否真的在验证 tech note 的核心 thesis，而不是验证别的问题
- 实验变量、对照组和指标是否足够支撑“一阶段应验证的最小结论”
- 一阶段中哪些内容本来就不该要求验证，例如跨域泛化保护

**需要核对的对象**：
- `tech-note-0v1.md` 中 §7、§9.1–§9.6
- `README.md` 中实验摘要
- 一阶段脚本与结果文件

**通过条件**：
- 能把一阶段目标明确收敛为：
  - 验证扩展导致复杂度增长
  - 验证 rewrite 抑制复杂度增长
  - 不把“跨域可规划性保护”算作一阶段必须完成的内容
- 若原设计过强，必须给出降级后的合理目标

**交付物**：
- 一段书面结论，说明一阶段“该验证什么、不该验证什么”

**当前结论**：通过，但需要降级表述。

- 一阶段的**合理目标**应当限定为：
  - 验证多域扩展是否带来表示复杂度增长
  - 验证 rewrite 是否显著抑制这种复杂度增长
  - 验证 Baseline 不扩展时会失去新域覆盖能力
- 一阶段**不应承担**的目标：
  - 证明 Expand-Only 的可规划率会在自然任务上普遍下降
  - 证明 rewrite 已经保护了跨域可规划性
  - 证明开放扩展的一般性退化规律
- 原因很直接：当前一阶段任务基本是单域、1-2 步模板任务，它们适合测“表示是否膨胀”，不适合测“跨域规划是否退化”。这与 tech note 在 §9.7 对二阶段补实验的动机是一致的。
- 因此，后续所有一阶段审计都按下面这个**最小充分 claim**执行：

> Phase 1 只验证“rewrite 对复杂度抑制”的必要证据，不验证“rewrite 对跨域可规划性保护”的充分证据。

---

## 步骤 2：输入数据与语义签名构建是否闭环

- [x] 完成

**要检查什么**：
- 原始 AgiBot World 提取文件是否存在
- 五域签名和四个 delta 是否真的由脚本生成并能被加载
- 路线图中的输入输出命名是否和仓库一致

**需要核对的对象**：
- `data/agibot-world/`
- `data/signatures/`
- `scripts/extract_signatures.py`
- `scripts/build_signatures.py`
- `src/core/__init__.py`

**通过条件**：
- 输入文件存在
- 构建脚本可运行或现有结果可被重新加载
- `Sigma_0` 与各 `Delta_k` 的最小统计信息可核对

**交付物**：
- 一张“输入 → 脚本 → 签名文件”的审计表

**当前结论**：通过。

**审计结果**：

| 环节 | 证据 | 结论 |
|------|------|------|
| 原始提取输入 | `data/agibot-world/task_info/`, `signature_extraction.json`, `extraction_report.txt` 存在 | 通过 |
| 构建脚本 | `scripts/build_signatures.py` 存在，逻辑明确区分 `Sigma_0` 与 `Delta_k` | 通过 |
| 签名产物 | `data/signatures/` 下 5 个 JSON 文件存在 | 通过 |
| 可加载性 | 当前 `SemanticSignature.load()` 可成功加载全部 5 个签名文件 | 通过 |

**加载核对结果**：

- `domestic.json`: complexity = 59
- `retail_delta.json`: complexity = 14
- `industrial_delta.json`: complexity = 15
- `restaurant_delta.json`: complexity = 19
- `office_delta.json`: complexity = 18

**保留说明**：

- 这一层证明的是“数据输入到签名文件的工程闭环存在”。
- 它**不证明**签名对 Task Catalog 的逐项语义映射是完备保真的。
- 尤其旧路线图中类似“覆盖家居领域全部 69 种技能”的说法，当前仓库并没有按那种逐项技能计数方式实现；当前签名更接近研究抽象版 IR，而不是任务目录的逐字段镜像。

---

## 步骤 3：核心数据结构与 PDDL/Planner 实现是否匹配设计

- [x] 完成

**要检查什么**：
- `SemanticSignature`、动作、约束、统计方法是否存在
- PDDL 生成是否可用
- planner 实现究竟是什么，是否与文档口径一致

**需要核对的对象**：
- `src/core/__init__.py`
- `src/core/config.py`
- `src/core/pddl_generator.py`
- `scripts/test_pddl.py`
- `data/pddl_test/`

**通过条件**：
- 核心数据结构可序列化、可加载、可统计
- PDDL 生成脚本可运行
- planner 的真实实现被准确记录
- 若与路线图不一致，必须记录“设计口径”和“实现口径”的差异

**交付物**：
- 一段实现偏差说明

**当前结论**：部分通过。

**通过的部分**：

- `SemanticSignature`、`Predicate`、`ActionTemplate`、`Constraint` 等核心对象存在，且支持序列化、反序列化、统计与 merge。
- `scripts/test_pddl.py` 可端到端运行，`Sigma_0` 能生成 domain/problem，并在 10 个家居任务上得到 100% 可规划结果。
- `data/pddl_test/pddl_test_results.json` 已记录最小闭环输出。

**偏差与降级说明**：

1. `SystemConfig` 只是简化版配置容器，未实现 tech note 中更完整的 belief / projection / transition / planner / grammar 分量。
2. planner 的真实实现不是旧路线图中偏向外部 planner 的口径，而是 `src/core/pddl_generator.py` 中的**自写 BFS planner**。
3. 文件头注释写“使用 pyperplan”，但代码实际没有调用 pyperplan；这里应视为文档口径漂移，而不是功能错误。
4. 因为当前 planner 是研究原型级 BFS，所以后续关于“可规划率”的结论必须理解为“在当前 planner 下的可规划率”，不能自动上升为对一般 planner 的结论。

**审计结论**：

- 若问题是“核心实现是否能自洽运行”，答案是是。
- 若问题是“是否完整实现了 tech note 的系统配置抽象和 planner 设想”，答案是否。
- 后续一阶段审计统一按“原型实现闭环”口径继续，而不是按“完整系统实现”口径继续。

---

## 步骤 4：测试框架与 Rewrite 合法性验证是否真的成立

- [x] 完成

**要检查什么**：
- `Q_star / Q_task / Q_t` 是否真的实现
- T0/T1/T2 是否只是命名，还是实际参与了 pass 验证
- Pass 1/2/3 的合法性验证是否符合各自设计目标

**需要核对的对象**：
- `src/core/test_suite.py`
- `src/rewrite/engine.py`
- `src/rewrite/pass1_predicate_elimination.py`
- `src/rewrite/pass2_rule_folding.py`
- `src/rewrite/pass3_object_pruning.py`

**通过条件**：
- 能明确写出每个 pass 实际跑了什么验证
- 能识别并记录所有“设计上要求、实现里没做到”的地方
- 至少区分 core-preserving 与 task-preserving 两类验证是否被真的执行

**交付物**：
- 一张“设计要求 / 实际实现 / 审计结论”对照表

**当前结论**：部分通过。

| 设计要求 | 实际实现 | 审计结论 |
|------|------|------|
| 存在 `Q_star / Q_task / Q_t` 三层测试集 | `src/core/test_suite.py` 中均已实现 | 通过 |
| T0/T1/T2 都进入测试框架 | 已实现对应测试函数 | 通过 |
| Pass 1/2 以 `Q_star` 验证 core-preserving | `run_global_rewrite()` 确实这么做 | 通过 |
| Pass 3 以 `Q_task` 验证 task-preserving | `run_task_pruning()` 现已改为按单任务 `Q_task` 变体验证，并在失败时回滚 | 通过 |
| rewrite 采用真正的分层验证策略 | 目前更接近“调用一个聚合测试函数”，不是严格的分层淘汰流程 | 部分通过 |

**关键结论**：

1. 测试框架本身不是空壳，`Q_star`、`Q_task`、`Q_t` 都存在。
2. Pass 1/2 的 core-preserving 验证成立，Pass 3 的 task-preserving 验证现在也已接入单任务 `Q_task`。
3. 当前仍不能称为“严格分层验证流水线”，因为实现方式依旧是聚合测试函数，而不是 T0→T1→T2 的逐层淘汰执行器。
4. 因此，Phase 1 现在可以把 Pass 3 写成“已做任务级验证并通过”，但不能把整个 rewrite 引擎写成“完整实现了 tech note 中理想化的分层验证机制”。

---

## 步骤 5：四组系统与 ManualOpt 对照是否可审计

- [x] 完成

**要检查什么**：
- 四组系统是否都存在、行为是否符合定义
- ManualOpt 是否真正可配置、可复现，还是源码硬编码
- Stage 0–4 的构造逻辑是否一致

**需要核对的对象**：
- `src/experiment/systems.py`
- `data/manual_opt/`
- 一阶段和二阶段运行脚本

**通过条件**：
- 四组系统行为可解释
- ManualOpt 的真实实现方式被写清楚
- 若不满足“可配置且可复现”，该步只能判定为部分通过

**交付物**：
- 四组系统审计摘要

**当前结论**：通过。

**审计结果**：

- `Baseline`、`Expand-Only`、`Expand+Rewrite`、`Expand+ManualOpt` 四组系统都已实现，且一阶段运行脚本确实按这四组收集结果。
- `Expand+Rewrite` 的行为与设计基本一致：全局先做 Pass 1/2，再在 task 级执行 Pass 3。
- `Expand+ManualOpt` 也真实存在，且当前已改为从 `data/manual_opt/stage_1.json` 到 `stage_4.json` 读取文件化配置。
- `data/manual_opt/` 目录现已成为真实输入，因此“ManualOpt 可配置且可复现”这一条已满足。

**结论拆分**：

1. 若问题是“四组对照系统是否真实存在并参与实验”，答案是是。
2. 若问题是“ManualOpt 是否按路线图要求实现为独立人工配置产物”，答案也是是。

**后续口径约束**：

- 可以说：仓库中存在一个可运行且已文件化的 ManualOpt 基线。
- 仍不应夸大为“已对人工优化规则正确性做独立外部审计”，因为当前只是实现了文件化与复现性，不是额外的人审流程。

---

## 步骤 6：一阶段原始结果是否可复现

- [x] 完成

**要检查什么**：
- 一阶段实验脚本是否能端到端运行
- `results/raw/` 与 `results/pilot/` 是否由当前代码重跑得到
- 关键主结果是否稳定：59→125、59→115、p=0.0248

**需要核对的对象**：
- `scripts/run_experiment.py`
- `scripts/analyze_results.py`
- `results/raw/summary.json`
- `results/raw/full_results.json`
- `results/pilot/`

**通过条件**：
- 脚本可运行
- 关键结构性结果可复现
- timing 波动允许存在，但不影响主结论

**交付物**：
- 一阶段复算结论

**当前结论**：通过。

**复算结果**：

- `scripts/run_experiment.py` 可端到端运行并刷新 `results/raw/`。
- `results/pilot/summary.json` 存在，说明 pilot 版本结果也有产物。
- 一阶段关键主结果可复现：
  - `Baseline`: S4 complexity = 59
  - `Expand-Only`: S4 complexity = 125
  - `Expand+Rewrite`: S4 complexity = 115
  - `Expand+ManualOpt`: S4 complexity = 114
- 关键趋势稳定：
  - `Expand-Only` 复杂度随阶段增长
  - `Expand+Rewrite` 与 `ManualOpt` 都压低了复杂度
  - `Baseline` 在新领域上失去覆盖能力

**复现边界**：

- `planning_ms`、`setup_ms` 等 timing 字段会有自然波动，不应要求逐值一致。
- 但复杂度、可规划率、统计检验用到的主序列是稳定的，因此足以支持“结果可复现”的判断。

---

## 步骤 7：一阶段输出物与验收标准是否一致

- [x] 完成

**要检查什么**：
- 路线图中声明的产物是否都存在
- 结果报告命名是否一致
- 验收标准是否真的被满足，例如 `Q_star >= 10`、测试目录、analysis 文件命名

**需要核对的对象**：
- `README.md`
- `results/`
- `ROADMAP-phase1.md`
- 仓库实际目录结构

**通过条件**：
- 产物命名一致，或明确标注不一致项
- 每条验收标准都有证据
- 未满足项必须转入问题清单，而不是继续打勾

**交付物**：
- 一阶段验收清单

**当前结论**：部分通过。

**产物核对**：

| 项目 | 仓库现状 | 结论 |
|------|------|------|
| 原始结果目录 | `results/raw/` 存在 | 通过 |
| pilot 结果目录 | `results/pilot/` 存在 | 通过 |
| 一阶段分析报告 | 现仅保留 `results/phase1_analysis.md` | 通过 |
| 图表目录 | `results/figures/` 存在 | 通过 |
| 单元测试目录 | `tests/` 不存在 | 不通过 |

**验收标准核对**：

1. 旧路线图要求 `Q_star` 至少 10 条核心测试，当前结果文件里稳定记录的是 `q_star_total = 10`，因此该条**通过**。
2. 旧路线图要求 ManualOpt 配置文件化交付，当前 `data/manual_opt/` 已存在阶段配置文件，因此该条**通过**。
3. 旧路线图要求 `tech-note-0v2.md`，当前仓库没有该文件，因此该条**不通过**。
4. README 与一阶段报告命名目前已统一到 `results/phase1_analysis.md`，该条**通过**。

**审计判断**：

- 一阶段产物层面的命名漂移已基本修正，但仍存在少数原路线图承诺未兑现项。
- 因此目前仍不能直接写成“已按原路线图全部验收”。
- 更准确的说法是：
  - 审计步骤已完成
  - 核心实验产物已生成
  - 但原路线图中的个别交付与验收条目仍未严格满足

---

## 步骤 8：一阶段结论是否可靠，以及应如何表述

- [x] 完成

**要检查什么**：
- 当前结果最多能支撑到什么强度的 claim
- 哪些结论可以保留
- 哪些结论必须降级为“必要条件验证”或“研究原型结果”

**需要核对的对象**：
- `tech-note-0v1.md`
- `README.md`
- 一阶段分析报告与原始结果

**通过条件**：
- 给出一版收敛后的 Phase 1 结论
- 明确列出可信边界和未验证部分

**交付物**：
- 一段可直接回写到 tech note 的结论文本

**当前结论**：通过，但必须使用收敛后的表述。

**建议采用的一阶段结论文本**：

> Phase 1 证明了在当前五域渐进扩展设置下，纯扩展会带来表示复杂度持续增长，而 rewrite 能显著抑制这种增长；同时，不扩展的 Baseline 无法覆盖新域任务。基于当前实现，Phase 1 可被视为“rewrite 对复杂度抑制”的必要证据。它还不能单独证明 rewrite 一般性地保护了跨域可规划性，也不能单独证明开放扩展若不 rewrite 就会在自然任务分布上普遍退化。

**允许保留的结论**：

1. `Expand-Only` 的复杂度随阶段增长。
2. `Expand+Rewrite` 显著抑制了这种增长。
3. `Expand+ManualOpt` 与 `Expand+Rewrite` 接近，说明自动 rewrite 具备工程价值。
4. `Baseline` 不扩展时无法覆盖新域任务。

**必须降级或移除的结论**：

1. “Phase 1 已证明 rewrite 保护跨域可规划性”
2. “Phase 1 已证明 Expand-Only 会导致规划退化”
3. “Phase 1 已完整实现 tech note 设想的严格分层验证流水线”
4. “Phase 1 已按原路线图全部验收完成”

**可信边界**：

- 这是一个研究原型级、一阶段 kill test 级的结果。
- 它足以支撑内部 tech note 和较保守的研究表述。
- 它不应被包装成对开放世界扩展的一般性充分验证。

---

## 当前执行顺序

1. 步骤 1：重审一阶段研究问题与实验设计
2. 步骤 2：核对输入数据与签名构建
3. 步骤 3：核对核心数据结构与 PDDL/Planner
4. 步骤 4：核对测试框架与 rewrite 合法性
5. 步骤 5：核对四组系统与 ManualOpt
6. 步骤 6：复算一阶段结果
7. 步骤 7：核对输出物与验收标准
8. 步骤 8：重写一阶段结论

当前版本中，步骤 0–8 已完成审计并逐步打勾。后续如果要继续推进，应进入“修正清单”阶段，而不是继续沿用旧版完成态口径。