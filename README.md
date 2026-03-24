# LCOS-R: 参考语义驱动的机器人语义重写框架

> **核心 thesis**: 开放环境中的持续扩展，不仅依赖新语义的准入，更依赖新语义进入后对内部表示进行语义保持重写——否则就是规则堆积，而不是结构升级。

## 项目简介

LCOS-R（Local Compiled Open Semantics — Rewrite）是一个最小参考语义驱动的机器人语义编译框架。它从有限可执行测试诱导意义，通过三阶段重写 pass（谓词消除 → 规则折叠 → 对象裁剪）在扩展后自动压缩内部表示，同时保持语义等价。

本仓库包含框架实现、实验代码和两阶段验证实验的完整结果。

## 实验结果摘要

### 一阶段：复杂度抑制

5 域渐进扩展 × 4 组系统 × 30 任务/域：

| 指标 | Expand-Only | Expand+Rewrite | p 值 |
|------|-------------|----------------|------|
| S4 总复杂度 | 125 | 115 | 0.0248 |
| Cohen's d | — | 2.42（极大效应量） | — |
| 可规划率 | 100% | 100% | — |

### 二阶段：跨域可规划性保护

18 个跨域组合任务，利用同义谓词歧义：

| 指标 | Expand-Only | Expand+Rewrite | p 值 |
|------|-------------|----------------|------|
| S4 可规划率 | **0%** | **100%** | 7.63×10⁻⁶ |
| 中位 BFS 节点 | 200,001（全超限） | 40,697 | — |
| 搜索代价节省 | — | 76.5% | — |

## 项目结构

```
lcos-r/
├── tech-note-0v1.md              # 技术文档（术语、claim、形式化、实验）
├── src/
│   ├── core/                     # 核心数据结构与工具
│   │   ├── __init__.py           #   SemanticSignature, Predicate, ActionTemplate
│   │   ├── pddl_generator.py     #   PDDL 生成 + 纯 Python BFS planner
│   │   ├── test_suite.py         #   分层验证测试 (T0/T1/T2)
│   │   └── config.py             #   SystemConfig 数据结构
│   ├── rewrite/                  # 三阶段重写引擎
│   │   ├── engine.py             #   主引擎：3-pass 序列 + 回滚
│   │   ├── pass1_predicate_elimination.py  # Pass 1: 同义谓词消除
│   │   ├── pass2_rule_folding.py           # Pass 2: 同构规则折叠
│   │   └── pass3_object_pruning.py         # Pass 3: 无关类型裁剪
│   └── experiment/               # 实验框架
│       ├── systems.py            #   4 组系统 + 任务模板 + 跨域任务
│       └── metrics.py            #   指标收集（复杂度/规划/验证）
├── scripts/
│   ├── extract_signatures.py     # 从 AgiBot World 提取语义签名
│   ├── build_signatures.py       # 构建 5 域签名 JSON
│   ├── run_experiment.py         # 一阶段实验运行器
│   ├── run_phase2.py             # 二阶段实验运行器
│   ├── analyze_results.py        # 一阶段分析（Fig 1-6 + 统计）
│   ├── analyze_phase2.py         # 二阶段分析（Fig 7-9 + McNemar）
│   └── test_pddl.py             # PDDL 生成与求解验证
├── data/
│   ├── signatures/               # 5 域语义签名（domestic + 4 deltas）
│   ├── pddl_test/                # PDDL 测试用例
│   └── agibot-world/             # AgiBot World 任务数据
└── results/
    ├── analysis.md               # 一阶段分析报告
    ├── phase2_analysis.md        # 二阶段分析报告
    ├── figures/                  # 9 张实验图表 (fig1-fig9)
    ├── raw/                      # 一阶段原始结果
    └── phase2/                   # 二阶段原始结果 + 统计检验
```

## 快速开始

### 环境

- Python 3.10+
- numpy, matplotlib

无需外部 PDDL 求解器，框架内置纯 Python BFS planner。

### 运行实验

```bash
# 一阶段：5 域渐进扩展实验
python3 scripts/run_experiment.py

# 二阶段：跨域组合任务实验
python3 scripts/run_phase2.py

# 生成分析报告与图表
python3 scripts/analyze_results.py
python3 scripts/analyze_phase2.py
```

### 验证 PDDL 生成

```bash
python3 scripts/test_pddl.py
```

## 数据来源

语义签名从 [AgiBot World](https://huggingface.co/agibot-world) Task Catalog 提取，涵盖 5 个领域：

| 领域 | 类型 | 示例对象 |
|------|------|---------|
| domestic（家居） | 基础域 | cup, table, fridge, sponge |
| retail（零售） | +delta | shelf, barcode\_scanner, plastic\_bag |
| industrial（工业） | +delta | conveyor\_belt, memory\_module, target\_box |
| restaurant（餐饮） | +delta | tray, knife, dough, noodle |
| office（办公） | +delta | stamp, shredder, printer, whiteboard |

## 验证边界

当前实验验证了核心 thesis 的**必要条件**，但非充分验证：

- ✅ 纯扩展导致复杂度线性增长（112%），rewrite 显著抑制（p=0.0248）
- ✅ 跨域任务下纯扩展可规划率退化至 0%，rewrite 恢复至 100%（p=7.63×10⁻⁶）
- ✅ 自动 rewrite 与人工优化效果一致
- ⚠️ 跨域任务为反向设计，不代表自然任务分布
- ⚠️ 仅覆盖 Type A 失败模式（同义谓词不可达）
- ⚠️ 5 域 / 125 复杂度规模有限，更大规模可扩展性未知
- ⚠️ 实验在 PDDL 符号层，未涉及物理执行

## 文档

- [tech-note-0v1.md](tech-note-0v1.md) — 技术文档（术语、形式化定义、实验设计）
- [results/analysis.md](results/phase1_analysis.md) — 一阶段实验分析报告
- [results/phase2_analysis.md](results/phase2_analysis.md) — 二阶段实验分析报告
- [ROADMAP-phase1.md](ROADMAP-phase1.md) — 一阶段路线图（已完成）
- [ROADMAP-phase2.md](ROADMAP-phase2.md) — 二阶段路线图（已完成）

## License

Research prototype. Not for production use.
