# 参考语义驱动的机器人语义重写框架（LCOS-R）

**状态**：草案  
**用途**：内部 tech note，用来定住术语、核心 claim、最小形式化骨架和最小实验  
**定位**：研究命题 + 最小可验证框架，不追求论文级完备性

---

## 1. 问题动机

### 1.1 起点：什么差别对机器人"有意义"

机器人面对的世界充满差别，但并非所有差别都值得关心。搬运机器人不需要区分杯子花纹，却必须区分杯子空还是满。问题是：

> **对一个有具体任务和身体的机器人，什么差别算"有意义的"？**

百科词义回答不了——字典不知道机器人有几个自由度；记住所有差别也不行——状态空间会爆炸。机器人需要一个判定标准：哪些区分会影响行为结果，哪些不会。

### 1.2 判定意义需要背景语义

这个判定标准不会凭空出现。要判定"杯子空/满对我有意义"，机器人至少需要知道自己有哪些动作、动作的前提和效果、观测如何映射到内部状态。这些构成了一个**参考语义**：一组有限的可执行测试，为"有意义"提供操作性定义：

> **意义 = 对机器人可执行测试结果产生差别的那些区分。**

两个状态若在所有可执行测试下表现相同，对该机器人来说意思就是一样的。没有参考语义，"有意义"就无法判定。

### 1.3 开放环境下语义必须从最小出发持续扩展

机器人不可能一开始就拥有完整的参考语义——开放环境中新物体、新任务、新约束随时出现。务实的策略是：

> **从覆盖初始任务的最小测试集出发，遇到新情况时增量引入新概念、新规则、新约束。**

但纯"加法"会带来退化：状态表示膨胀、规则碎片化、推理变慢、新旧知识冲突。

### 1.4 重写是退化问题的自然解

退化的根源是只加不减。而参考语义不仅告诉我们"什么重要"，也告诉我们**"什么不重要"**。不重要的差别就是合法的重写空间。

每次新知识进入后，系统可以在"保持相关测试结果不变"的约束下，对内部表示做重写与重编译——合并冗余、简化表示、消除冲突。

因此，本工作的核心判断是：

> **开放环境中的持续扩展，不只是"加入新语义"的问题，更是"新语义进入后，能否在参考语义约束下触发系统级重写与重编译"的问题。**

- **参考语义**划定语义边界——什么差别算有意义
- **语义重写**在边界内做系统优化——让系统更短、更快、更稳

"意义"不是终点，而是 **rewrite legality 的来源**。

---


---

## 2. 现有工作的简述与本工作的定位

相近的工作大致有四类：

### 2.1 知识表示 / semantic reasoning

这类工作强调机器人需要概念、关系、规则、约束、信念等高层知识，以支撑任务执行和泛化。相关综述明确把 semantic knowledge 看成连接过往经验和新情境的抽象层，并把语义推理系统概括为知识来源、计算框架与世界表示三类核心部件 [1]。

### 2.2 TAMP（task and motion planning）

这类工作强调动作前提、动作效果、逻辑任务规划与几何可行性的联动。它们已经部分回答了"哪些差别对动作和任务真正重要"——"高层语义"若要落地，最终必须转成动作前提、效果、约束、可达性、代价等可执行测试 [2]。

### 2.3 open-world planning / action knowledge augmentation

这类工作强调：开放世界中缺的通常不是"整个宇宙语义"，而是特定任务下的动作知识、前提、效果、约束。代表性做法是增量补充 action knowledge，保留通用核心 primitive 再扩展任务相关约束 [3]。

### 2.4 affordance / world model

这类工作强调：机器人最早、最稳定的"意义"往往不是百科词义，而是 object–action–effect 关系。例如基于本体和规则推理将语义约束注入 planner 的联合架构已在家居抓取等具体任务中落地 [4]。

---

### 2.5 本工作的定位

本工作不和上述方向对立，而是提出一个更小的统一骨架：

> **给机器人一个最小参考语义，然后把内部状态、规则、动作描述、规划问题都统一看成可重写对象；任何优化都必须相对于该参考语义保持意义不变，或至少保持核心测试不变。**

这篇 note 不打算声称：

- “首次把意义数学化”
- “首次提出机器人需要语义”

更合适的表述是：

> **本文提出一个面向机器人的最小参考语义及其上的语义重写框架：意义由有限可执行测试诱导，保义由测试保持来判定，开放扩展通过受控扩展与重编译机制实现。**

---

## 3. 核心 claim

核心 claim 分四层：

### Claim 1：意义不能脱离背景语义讨论

对机器人而言，“意义不同”不能是抽象断言，而必须落到某种内部参考语义上。

### Claim 2：对机器人而言，背景语义必须是局部的、任务相关的、可执行的

我们不追求全局完备语义，只追求局部任务域中的最小参考语义。

### Claim 3：意义可由有限可执行测试诱导

若两个系统配置（或其对外可观察接口）在有限测试集下不可区分，则在当前参考语义中应视为等价。

### Claim 3 → Claim 4 的桥接：测试等价天然定义合法重写空间

Claim 3 建立了测试诱导的等价关系 $\equiv_t$。这一步直接给出的是 legality criterion：任何替换若保持相关测试输出不变，就不会改变系统在这些测试接口下的可观察行为，因此属于合法 rewrite 候选。这意味着：

> 测试诱导的等价关系先回答"什么变换是合法的"；至于是否合法空间里有更优表示，是后续工程问题。

因此，Claim 4 不是 Claim 3 的纯逻辑推论，而是建立在以下附加假设上的工程性 thesis：

- 当前系统表示中确实存在冗余或可压缩结构
- 重写语法足够表达更优代表元
- 搜索/编译过程能够在合法空间内找到这些代表元

Section 6–7 的任务，就是把这个 legality criterion 变成可执行的重写与优化框架。

### Claim 4：持续扩展依赖语义重写带来的系统级优化

开放扩展若只有“加法”而无“重写/重编译”，最终会退化成规则堆积；  
开放扩展若能触发语义保持的重写，则可能转化为结构升级。

---

## 4. 术语与最小定义

---

### 4.1 局部对象域

在时刻 $t$，只考虑当前有限对象集：

$$
D_t = \{e_1,\dots,e_n\}
$$

这里的对象来自当前任务相关的 perception / tracking / scene graph，而不是整个世界。

---

### 4.2 语义签名

定义当前语义签名：

$$
\Sigma_t = (\mathcal S_t,\mathcal R_t^b,\mathcal R_t^g,\mathcal A_t,\mathcal E_t,\mathcal C_\star,\mathcal G_t)
$$

其中：

- $\mathcal S_t$：类型集  

  例如 object / agent / place / container

- $\mathcal R_t^b$：布尔结构谓词  

  例如 on(x,y), in(x,y), holding(a,x), reachable(a,x), blocked(x)

- $\mathcal R_t^g$：渐变谓词  

  例如 hot(x), fragile(x), near(x,y), full(x)

- $\mathcal A_t$：动作模板  

  例如 grasp(x), move(x,p), place(x,p), open(x), ask(q)

- $\mathcal E_t$：效果词汇表  

  例如 can-grasp, will-spill, collision-risk, goal-progress

- $\mathcal C_\star$：核心约束  

  例如类型一致性、安全核、显式禁令、关键任务规则

- $\mathcal G_t$：可重写对象语法  

  形式上，$\mathcal G_t = (\mathcal T_G,\, \mathcal R_G)$，其中：  

  - $\mathcal T_G \subseteq \{\texttt{state},\, \texttt{rule},\, \texttt{act},\, \texttt{plan},\, \texttt{aff}\}$ 标记哪些类型的内部对象允许被 rewrite  
  - $\mathcal R_G$ 是该类型上的合法重写模式集合（例如"允许谓词折叠""允许冗余规则消除""允许无关对象裁剪"）  

  核心约束 $\mathcal C_\star$ 中的对象默认**不可重写**，除非显式声明。$\mathcal G_t$ 由系统设计者初始指定，可随扩展而增长，但增长本身须满足准入准则（见 Section 8）。

---

### 4.3 世界状态与认识状态

真实世界语义状态记为：

$$
\omega_t = (I_t^b, I_t^g)
$$

其中：

$$
I_t^b(R): D_t^k \to \{0,1\}
$$

$$
I_t^g(G): D_t^m \to [0,1]
$$

机器人并不直接访问 $\omega_t$，而维护一个信念分布：

$$
b_t \in \Delta(\Omega_t)
$$

这里必须明确区分两件事：

- **世界中的程度性属性**：由 $I_t^g$ 给出
- **机器人对其认识的不确定性**：由 $b_t$ 给出

这是本框架保持数学清晰的关键前提之一。

#### 观测模型与 belief 更新

传感器输入记为 $o_t$。给定观测模型 $O_t(o_t \mid \omega)$，标准贝叶斯更新为：

$$
b_t'(\omega) \propto O_t(o_t \mid \omega) \, b_t(\omega)
$$

这意味着：视觉模型输出的置信度首先进入**后验更新**，而不是直接赋给逻辑真值。这正是为了避免把"检测器不确定"误当成"世界里部分为真"。

工程上，$b_t$ 可通过以下方式近似：

- 粒子滤波（小规模对象域）
- Top-$k$ 假设集（中等规模）
- 因子图 / learned posterior（大规模连续态）

---

### 4.4 工作语义状态

机器人实际推理与规划不直接在 $b_t$ 上进行，而是投影到一个工作状态：

$$
z_t = \Pi(b_t) = (z_t^{vis}, z_t^{sym}, z_t^{aff})
$$

#### 视觉/几何层 $z_t^{vis}$

包含位姿、接触、遮挡、grasp pose 等连续信息，用于 grounding。

#### 符号层 $z_t^{sym}$

对每个布尔原子 $R(\mathbf d)$，定义后验真概率：

$$
p_{R,\mathbf d} = \Pr_{\omega \sim b_t}[I^b(R,\mathbf d) = 1]
$$

然后用双阈值 $\theta_+, \theta_-$ 投影成三值：

$$
v_t(R,\mathbf d) =
\begin{cases}
\top, & p_{R,\mathbf d} \ge \theta_+ \\
\bot, & p_{R,\mathbf d} \le \theta_- \\
?, & \text{otherwise}
\end{cases}
$$

对渐变原子 $G(\mathbf d)$，保存为：

$$
(\mu_{G,\mathbf d},\, \sigma_{G,\mathbf d}) = \big(\mathbb{E}_{\omega \sim b_t}[I^g(G,\mathbf d)],\; \sqrt{\mathrm{Var}_{\omega \sim b_t}[I^g(G,\mathbf d)]}\big)
$$

即"程度估计 + 不确定性估计"。

#### affordance 层 $z_t^{aff}$

定义对象–动作–效果关系：

$$
\mathrm{Aff}_t(\mathbf d,a,e)
=
\Pr(e \text{ occurs after } a(\mathbf d) \mid b_t)
=
\sum_{\omega,\omega'}
b_t(\omega)\,K_t(\omega' \mid \omega, a(\mathbf d))\,
\mathbf{1}[e(\omega,\omega')]
$$

其中 $K_t$ 是动作转移核。这一层表达的是：在当前信念下，对某对象执行某动作，会产生哪些效果、成功率多大、风险多大。

这一层是机器人最直接可用的"意义中间表示"——对象的意义首先表现为 affordance（如"杯子对 grasp 的 can-grasp 概率高"），而不是百科词义。

---

### 4.5 动作语义

对每个 grounded action $a(\mathbf d)$，定义：

#### 动作前提

$\mathrm{Pre}(a)$ 是关于 $z_t^{sym}$ 和 $z_t^{aff}$ 的公式。例如：

$$
\mathrm{Pre}(\mathrm{grasp}(x)) = \mathrm{reachable}(x) \land \neg\,\mathrm{blocked}(x) \land \mathrm{Aff}(x,\mathrm{grasp},\text{can-grasp}) > \eta
$$

#### 动作效果

通过转移核给出动作后的世界状态分布：

$$
K_t(\omega' \mid \omega, a)
$$

#### 风险约束

只有满足风险阈值的动作才允许执行：

$$
\Pr(\text{violates } \mathcal C_\star \mid b_t, a) \le \delta
$$

这一步把"参考语义"直接连接到 planner：动作前提和风险约束本身就是测试集 $Q_t$ 的核心来源。

---

### 4.6 公式语义

#### 布尔结构部分

采用 **Strong Kleene 三值逻辑**：$\top$（确定真）、$\bot$（确定假）、$?$（信息不足）。

选择三值而非模糊逻辑的原因是：它保留"未知"这一状态，不会把认识不确定误当成世界中的程度性。

#### 渐变部分

不直接用三值吃掉，而是保留 $(\mu, \sigma)$。决策时通过规则投影，例如：

$$
\mathrm{safe\_to\_touch}(x) = \mathbf{1}\big[\mu_{\mathrm{hot}}(x) \le \eta_h \;\land\; \sigma_{\mathrm{hot}}(x) \le \eta_u\big]
$$

这样：程度性概念保留程度值，认识不确定性单独保留，决策层再统一处理。

---

## 5. 意义的最小形式化

---

### 5.1 有限可执行测试集

定义测试集：

$$
Q_t = \{q_1,\dots,q_m\}
$$

其中按重要性分为三层：

$$
Q_\star \subseteq Q_t^{task} \subseteq Q_t
$$

- $Q_\star$：**核心测试集**——涉及安全、核心约束、类型一致性的测试，只增不减
- $Q_t^{task}$：**任务测试集**——当前任务相关的动作前提、效果、可行性测试，随任务切换而变
- $Q_t$：**完整测试集**——包含上述所有测试加上辅助性、诊断性测试

每个测试都必须是**有限、可执行、任务相关**的，例如：

- 动作前提是否满足
- 某动作是否触发风险
- 某效果概率是否超过阈值
- 是否存在可行计划
- 计划代价是多少
- 是否违反核心约束

这里强调“有限可执行测试”，原因是：

1. **测试**：保证“意义”有操作含义  
2. **可执行**：保证系统内部真能调用  
3. **有限**：保证判定、验证、回归测试都可行  

---

### 5.2 系统配置与测试接口

为了统一 rewrite 的合法性定义，我们不把测试直接作用在某个孤立子对象上，而是作用在**系统配置**上。定义：

$$
c_t = (\Sigma_t, b_t, \Pi_t, K_t, \mathsf{Plan}_t)
$$

其中：

- $\Sigma_t$：当前语义签名与规则/约束库
- $b_t$：当前 belief
- $\Pi_t$：从 belief 到工作状态的投影算子，满足 $z_t = \Pi_t(b_t)$
- $K_t$：动作转移核
- $\mathsf{Plan}_t$：当前 planner 接口及其求解配置

对任一可重写子对象 $x \subset c_t$，记：

$$
c_t[x \leftarrow x']
$$

为将 $x$ 替换为 $x'$ 后得到的新系统配置。

每个测试 $q \in Q_t$ 都被视为定义在系统配置上的有限可执行函数：

$$
q : \mathcal C_t \to \mathcal Y_q
$$

其中输出空间 $\mathcal Y_q$ 可以是布尔值、风险值、代价值、规划可行性等有限接口返回值。

---

### 5.3 意义等价

定义两个系统配置 $c,c'$ 的意义等价：

$$
c \equiv_t c'
\iff
\forall q\in Q_t,\ q(c)=q(c')
$$

若测试输出是连续值，则用容差版：

$$
|q(c)-q(c')| \le \varepsilon_q
$$

也就是说，在当前参考语义与测试接口下，两个系统配置若不可区分，则它们在当前意义上等价。这里的“等价”是局部、任务相关、当前测试集下的等价。

---

## 6. Rewrite Layer：把语义变成编译框架

这是整篇 note 的核心部分。

---

### 6.1 可重写对象

定义可重写对象类为系统配置中的可替换子对象：

$$
\mathcal X_t =
\mathcal X_t^{state}
\cup
\mathcal X_t^{rule}
\cup
\mathcal X_t^{act}
\cup
\mathcal X_t^{plan}
\cup
\mathcal X_t^{aff}
$$

分别表示：

- 状态表示对象
- 规则/约束对象
- 动作描述对象
- 规划问题对象
- affordance 摘要对象

因此，rewrite 的基本单位是“配置中的一个子对象”。合法性始终通过它所诱导的新系统配置来判定。

---

### 6.2 重写关系

若 $x \subset c_t$ 且 $x'$ 与 $x$ 同型，定义一次 rewrite 为：

$$
(c_t, x) \rightsquigarrow (c_t[x \leftarrow x'], x')
$$

但它不是纯句法重写，而是**受参考语义约束的配置替换**。后文为了简洁，仍写作 $x \rightsquigarrow x'$。

---

### 6.3 三类合法重写

#### A. Core-Preserving Rewrite

$$
x \rightsquigarrow_s x'
$$
若满足：
$$
\forall q\in Q_\star,\ q(c_t)=q(c_t[x \leftarrow x'])
$$
其中 $Q_\star$ 是核心测试集。

适用于：

- 派生谓词引入
- 规则归一化
- 冗余约束消除
- 定义展开/折叠

这里称其为 **core-preserving**，而不是“完全保义”：它严格保持核心测试，但不自动保证对全部任务测试永久不变。

#### B. Task-Preserving Rewrite

$$
x \rightsquigarrow_\tau x'
$$
若满足：
$$
\forall q\in Q_t^{task},\ q(c_t)=q(c_t[x \leftarrow x'])
$$

适用于：

- 删除与当前任务无关的对象
- 任务相关状态抽象
- 宏动作化
- 目标相关子图裁剪

#### C. Risk-Bounded Approximate Rewrite

$$
x \rightsquigarrow_\epsilon x'
$$
若满足核心测试严格不变，同时非核心测试误差有界：

$$
\forall q \in Q_\star,\; q(c_t) = q(c_t[x \leftarrow x']) \qquad \text{且} \qquad \forall q \in Q_t \setminus Q_\star,\; |q(c_t)-q(c_t[x \leftarrow x'])| \le \varepsilon_q
$$

适用于：

- belief 压缩
- 连续属性粗量化
- 低概率分支剪枝
- affordance 概率摘要

#### 近似重写的多轮误差控制

多轮近似 rewrite 的误差可能累积。为此引入**误差预算机制**：

1. **总误差上界**：为每个测试 $q$ 设定总容许漂移 $E_q$，即无论经过多少轮近似 rewrite，相对于初始配置 $c_0$ 的累积偏差不得超过 $E_q$：

   $$
  |q(c_0) - q(c_n)| \le E_q
   $$

2. **单轮预算分配**：若预计最多执行 $N$ 轮近似 rewrite，则每轮容差为 $\varepsilon_q \le E_q / N$。

3. **回滚条件**：每轮 rewrite 后检查累积偏差。若任一核心测试偏差超出阈值，则回滚到上一合法状态。

4. **周期性锚定**：每隔 $k$ 轮 rewrite，执行一次**完整测试回归**，验证当前状态相对初始状态的总偏差。若偏差在预算内，则将当前状态设为新锚点；否则触发回滚。

这套预算机制只是**工程护栏**，不是一般性的误差传播定理。对于可行性判定、阈值风险约束、三值投影这类不连续测试，必须辅以完整回归，必要时直接禁止 approximate rewrite。

---

### 6.4 Rewrite 与 Dynamics 的区分

这里直接区分 rewrite 和 dynamics：

- 若替换前后的**系统配置**落在同一个意义等价类内，则它是 **rewrite**
- 若执行动作后系统配置跨出了当前等价类，则它是 **dynamics**

换句话说：

> **rewrite = 等价类内优化**  
> **dynamics = 等价类间迁移**

这样“保义重写”和“系统演化”就在同一框架下分开了。

### 等价类随测试集演化的稳定性

等价关系 $\equiv_t$ 依赖于测试集 $Q_t$。当系统扩展导致 $Q_t$ 变为 $Q_{t+1}$ 时，等价类可能发生变化——原先等价的状态可能变为不等价（因为新测试区分了它们），原先合法的 rewrite 可能不再合法。

为此，本框架采取以下约定：

1. **Rewrite 只在 $Q_t$ 固定时执行**：每次扩展先锁定新测试集 $Q_{t+1}$，然后在 $Q_{t+1}$ 下执行 rewrite。不允许在测试集变动的同时执行 rewrite。

2. **核心等价类单调细化**：核心测试集 $Q_\star$ 只增不减，因此核心等价类只会越来越细。这只保证已安装的 core-preserving rewrite 在**核心测试层面**不会失效；它不保证对未来完整任务语义永久不失效。

3. **任务等价类允许重建**：当 $Q_t^{task}$ 改变时，task-preserving rewrite 的合法性需要重新验证。这正是"扩展后重编译"的一部分。

---

### 6.5 具体 Rewrite Pass 示例

下面列 5 个在受控任务域中可立即实现的 rewrite pass：

#### Pass 1：冗余谓词消除（Core-Preserving）

若谓词 $P$ 在当前有限对象域 $D_t$ 上可判定地由其他谓词集合推出，或至少在 $Q_\star$ 所覆盖的全部查询上与 $\phi$ 测试等价，则移除 $P$ 并将所有引用替换为 $\phi$。  
**例**：若 `graspable(x) ≡ reachable(x) ∧ ¬blocked(x)`，则消除 `graspable` 谓词，用右侧展开替换。  
**合法性验证**：检查 $\forall q \in Q_\star,\, q(c_t) = q(c_t[x \leftarrow x'])$。

#### Pass 2：规则折叠（Core-Preserving）

若多条规则在当前对象域和核心测试覆盖下可归并为一条带参数的通用规则，则用通用规则替换。  
**例**：`full(cup) → ¬allow(rotate(cup))` 和 `full(bottle) → ¬allow(rotate(bottle))` 折叠为 `full(x) ∧ container(x) → ¬allow(rotate(x))`。  
**合法性验证**：同 Pass 1。

#### Pass 3：无关对象裁剪（Task-Preserving）

若对象 $e$ 不出现在当前任务测试 $Q_t^{task}$ 的任何输入中，则从工作状态中移除 $e$ 及其关联事实。  
**例**：桌面整理任务中，远处墙角的椅子不影响任何测试，可裁剪。  
**合法性验证**：检查 $\forall q \in Q_t^{task},\, q(c_t) = q(c_t[x \leftarrow x'])$。

#### Pass 4：宏动作化（Task-Preserving）

若动作序列 $(a_1, a_2, \dots, a_k)$ 总是连续执行且中间状态不被任何测试引用，则压缩为宏动作 $a_{macro}$。  
**例**：`open(drawer) → grasp(spoon) → close(drawer)` 在"取勺子"子任务中可压缩为 `fetch(spoon, drawer)`。  
**合法性验证**：前提和效果等价检查。

#### Pass 5：affordance 概率摘要（Risk-Bounded）

将高维 affordance 分布压缩为有限桶：将 $\mathrm{Aff}_t(\mathbf{d}, a, e) \in [0,1]$ 量化为 $\{0, 0.25, 0.5, 0.75, 1.0\}$。  
**例**：$\mathrm{Aff}(cup, grasp, \text{can-grasp}) = 0.87$ 量化为 $1.0$。  
**合法性验证**：核心测试严格不变，非核心测试误差 $\le \varepsilon_q$。

---

## 7. 系统级优化：为什么 rewrite 是持续扩展的关键

---

### 7.1 代价函数

定义系统配置 $c$ 的代价：

$$
\mathrm{Cost}(c)
=
\alpha\,\mathrm{Size}(c)
+\beta\,\mathrm{InferTime}(c)
+\gamma\,\mathrm{PlanTime}(c)
+\delta\,\mathrm{ExecRisk}(c)
+\eta\,\mathrm{Maintenance}(c)
$$

各项操作定义如下：

| 代价项 | 操作定义 | 度量方式 |
| -------- | --------- | --------- |
| $\mathrm{Size}(c)$ | 系统配置的表示长度 | 规则数 + 谓词数 + 约束数（统一计数） |
| $\mathrm{InferTime}(c)$ | 在 $z_t$ 上完成一轮推理所需时间 | 实测 wall-clock time |
| $\mathrm{PlanTime}(c)$ | planner 在给定输入下求解时间 | 实测 wall-clock time |
| $\mathrm{ExecRisk}(c)$ | 核心约束违例的期望频率 | $\mathbb{E}[\text{violations per episode}]$ |
| $\mathrm{Maintenance}(c)$ | 扩展后需人工修复的冲突数 | 规则冲突数 + 失败回归测试数 |

权重 $(\alpha,\beta,\gamma,\delta,\eta)$ 在实验中通过任务域校准确定：先在 Baseline 系统上测量各项的量纲和方差，然后归一化使各项在同一数量级。第一版实验中建议使用等权 $\alpha=\beta=\gamma=\delta=\eta=1$ 作为起点，再根据实验结果调整。

对某个子对象 $x \subset c$ 的 rewrite，真正比较的是替换前后的配置代价。目标是找到合法重写：

$$
c[x \leftarrow x']
$$

使得：

- 意义保持（对所需测试保持不变）
- 系统代价下降

---

### 7.2 核心判断

> **开放环境中的持续扩展，很大一部分取决于：新语义进入后，系统能否通过 rewrite 把旧表示、旧规则、旧规划问题重新组织成更紧凑、更统一、更高效的形式。**

如果没有 rewrite，扩展大概率会退化为：

- patch accumulation
- rule explosion
- maintenance collapse

如果有 rewrite，扩展才可能变成：

- abstraction
- normalization
- recompilation
- structure upgrade

---

### 7.3 扩展 = 加新语义 + 重编译

因此，开放扩展不是单纯“多一个概念”，而是：

1. 发现新差别 / 新约束 / 新属性  
2. 准入到语义系统  
3. 触发旧状态、旧规则、旧 planner 接口的重写  
4. 得到更统一的内部 IR

也就是说：

> **新语义的真正价值，不只是“表达能力增强”，而是“触发系统重编译”。**

这就是本文想抓住的 thesis。

---

## 8. 开放扩展机制

---

### 8.1 扩展模板

扩展只允许来自有限模板库，例如：

- 定义型扩展
- 动作前提扩展
- 动作效果扩展
- 安全约束扩展
- 新属性/新关系扩展

第一版不做无约束概念发现。

---

### 8.2 准入准则

候选扩展 $\Delta$ 只有在同时满足下面两类条件时才允许进入：

#### 核心守恒

核心测试 $Q_\star$ 不得退化。

#### 性能增益

定义评分：

$$
J
=
L_{\mathrm{pred}}
+\lambda_1 L_{\mathrm{plan}}
+\lambda_2 L_{\mathrm{calib}}
+\lambda_3 L_{\mathrm{comp}}
+\lambda_4 L_{\mathrm{safe}}
$$

这里把 $J$ 视为系统总代价 $\mathrm{Cost}$ 的**经验准入代理**：

- $L_{\mathrm{plan}}$ 对应推理与规划开销
- $L_{\mathrm{comp}}$ 对应表示复杂度与维护复杂度
- $L_{\mathrm{safe}}$ 对应执行风险

因此，扩展准入使用 $J$，扩展后的 rewrite/编译过程使用 $\mathrm{Cost}$；二者是“准入代理”与“编译目标”的关系。

只有当：
$$
J_{new} < J_{old} - \epsilon
$$
才接受扩展。

这里的收益不仅来自预测，还包括 rewrite 带来的：

- planner 更快
- 规则更短
- 维护成本更低
- 风险更稳

---

## 9. 最小实验（Kill Test）

这份 note 的实验目标不是验证整个理论，而是验证最核心的 thesis：

> **开放扩展若没有 rewrite，会退化成规则堆积；有 rewrite，才会带来系统级收益。**

---

### 9.1 任务域

选择**桌面整理**作为最小任务域，在仿真中实现（PyBullet 或 Isaac Sim）。

**具体任务**：桌面上有 5–10 个物品（杯子、碗、瓶子、勺子、盘子），机器人需要按类别将物品分组放入 2–3 个指定容器。

**初始语义签名**（第 0 轮）：

- 类型：`object`, `container`, `place`
- 布尔谓词：`on(x,y)`, `in(x,y)`, `reachable(x)`, `holding(a,x)`
- 渐变谓词：无
- 动作：`grasp(x)`, `gentle_grasp(x)`, `place(x,c)`, `move(x,p)`, `rotate(x)`
- 核心约束：类型一致性、一次只抓一个

其中 `gentle_grasp` 与 `rotate` 作为**初始可执行 primitive** 已存在于 planner 动作库中，但第 0 轮尚无额外语义约束去强制或禁止它们。这样后续扩展进入后，会真实改变动作前提、风险约束或动作选择空间。

---

### 9.2 固定扩展序列

实验的关键控制变量是一个**预定义的 5 轮扩展序列**，三组系统接受相同的扩展输入：

| 轮次 | 扩展内容 | 类型 |
| ------ | --------- | ------ |
| 1 | 新增渐变谓词 `fragile(x)` + 规则：`fragile(x) → require(gentle_grasp(x))` | 新属性 + 动作前提 |
| 2 | 新增 `full(x)` + 规则：`full(x) → ¬allow(rotate(x))` | 新属性 + 安全约束 |
| 3 | 新增 `stackable(x,y)` + 3 条放置约束规则 | 新关系 + 规则 |
| 4 | 新增 `heavy(x)` + 重量相关的抓取前提和放置约束 | 新属性 + 动作前提/效果 |
| 5 | 新增 `paired(x,y)` + 配对放置规则 | 新关系 + 任务规则 |

---

### 9.3 三组系统

#### Baseline

固定的初始语义签名 + 手写规则 + PDDL planner，不接受任何扩展。

#### Expand-Only

逐轮接受上述扩展，直接将新谓词/新规则追加到系统中，**不执行任何 rewrite pass**。

#### Expand+Rewrite

接受相同的扩展，但每轮扩展后执行 rewrite pass 序列：

1. 冗余谓词消除（Pass 1）
2. 规则折叠（Pass 2）
3. 无关对象裁剪（Pass 3）

合法性按 pass 类型分层验证：

- Pass 1–2 必须通过 $Q_\star$ 回归测试
- Pass 3 必须通过 $Q_t^{task}$ 回归测试
- 每轮 rewrite 结束后，再执行一次完整的 $Q_t^{task}$ 回归和抽样的 $Q_t$ 诊断测试

---

### 9.4 对比指标

每轮扩展后测量以下四类指标（每条件运行 50 个随机生成的场景）：

#### 1. 表示复杂度

- 活跃规则数、活跃约束数
- planner 输入的 PDDL 行数
- 工作状态 $z_t$ 中的事实数

#### 2. 计算开销

- 单次推理时间（ms）
- 单次规划时间（ms）
- 重规划时间（ms）

#### 3. 任务性能

- 整理成功率（%）
- 平均完成步数
- 失败恢复成功率（%）

#### 4. 稳定性曲线

- 以扩展轮次为横轴，绘制上述指标的变化趋势
- 重点关注 Expand-Only 是否呈线性/超线性增长，Expand+Rewrite 是否被抑制

---

### 9.5 预期结果

如果 thesis 成立，则应出现：

- **Baseline**：第 0 轮性能最优，但无法处理后续轮次引入的新语义场景
- **Expand-Only**：知识越来越多，但规则数和规划时间随轮次快速上升（线性或超线性），规则冲突增加
- **Expand+Rewrite**：在吸收同样新语义的前提下，复杂度增长被显著抑制，规划时间保持亚线性增长

这就是这篇 note 想先验证的核心证据。

---

## 10. 当前判断：数学是否自洽

### 目前成立的部分

1. 世界状态 / 认识状态 / 工作状态分层清楚  
2. 意义等价与 rewrite legality 都定义在系统配置及其测试接口上  
3. rewrite 的合法性由测试保持给出，优化收益则由额外的表示冗余与可搜索性假设支撑  
4. rewrite 与 dynamics 有明确分界  
5. 扩展与 rewrite 区分清楚，但通过“扩展后重编译”联通  

### 目前的边界

1. 只在有限局部域下自洽，不是全局完备语义  
2. 只有定义型扩展可做严格保守；学习型扩展只能经验保守  
3. approximate rewrite 的多轮误差预算只是工程护栏，不构成一般性理论保证；预算参数和回归频率都需要经验校准  
4. 等价类随 $Q_t$ 演化的稳定性已有约定（见 Section 6.4），但实际系统中测试集的增量设计仍依赖领域知识  

#### 当前结论

> 在“有限对象域 + 有限测试集 + 有限扩展模板 + 有限 rewrite 类”的前提下，这个骨架已经能形成一个类型一致、可操作、但仍然受限的形式化框架。

---

## 11. 当前判断：工程是否可落地

### 与现有系统栈的接口

本框架不是"另起炉灶"，而是可以直接挂到现有机器人栈上：

| 模块 | 现有技术 | 对接方式 |
| ------ | --------- | --------- |
| 感知侧 | detector / tracker / scene graph parser | 提供 $D_t$ 和观测分布 $O_t$ |
| 关系推理 | 概率关系估计 / GNN | 输出进入三值符号层 $z_t^{sym}$ |
| planner | PDDL / HTN / TAMP | $Q_t$ 本质就是 TAMP 风格的可执行测试壳 |
| 约束注入 | ontology + rule reasoning | 推出的约束直接喂给 planner（已有先例） |
| 开放扩展 | action knowledge augmentation | 增量补动作前提/效果/约束，与本框架扩展模板一致 |
| rewrite | 标准程序变换 / term rewriting | 每个 pass 是独立工程模块 |

### 系统运行流程

每轮按以下 10 步运行：

1. 感知模块更新局部对象域 $D_t$
2. 观测模型更新 belief $b_t$
3. 投影得到工作状态 $z_t = (z^{vis}, z^{sym}, z^{aff})$
4. 在 $Q_t$ 上执行测试：可执行性、风险、可达性、代价
5. planner 在通过测试的动作子集上规划
6. 执行动作并回收新观测
7. 记录预测残差、计划失败和安全边缘事件
8. 若残差长期稳定，则触发候选扩展 $\Delta$
9. 在 shadow mode / 离线验证上评估 $\Delta$
10. 若通过守恒与增益准则，安装到 $\Sigma_{t+1}$ 并执行 rewrite pass

### 第一版落地参数建议

| 参数 | 建议上限 |
| ------ | --------- |
| 对象数 $\lvert D_t \rvert$ | $\le 20$ |
| 类型数 $\lvert \mathcal S_t \rvert$ | $\le 4$ |
| 布尔谓词 $\lvert \mathcal R_t^b \rvert$ | $\le 12$ |
| 渐变谓词 $\lvert \mathcal R_t^g \rvert$ | $\le 6$ |
| 动作模板 $\lvert \mathcal A_t \rvert$ | $\le 6$ |
| 核心测试 $\lvert Q_\star \rvert$ | $\le 20$ |
| 扩展模板 | A/B/C/D/E 五类 |

数据结构上建议直接用**概率动态 scene graph** 承载：节点为对象/位置/容器/主体，边为支撑/容纳/接触/遮挡，节点属性承载渐变值，action/effect 表承载 affordance 层。

### 当前可落地部分

1. perception 可提供对象、关系候选和概率  
2. belief 可用粒子 / top-k 假设 / 因子图近似  
3. 符号层可实现为三值 scene graph  
4. affordance 层可由 learned model + 规则 + 统计混合构成  
5. planner 侧天然可接 TAMP / PDDL / HTN 风格测试  
6. rewrite pass 本身就是工程可写的模块

### 主要风险与缓解策略

| 风险 | 缓解策略 |
| ------ | --------- |
| 状态空间爆炸 | 严格限制 $\lvert D_t \rvert$ 和谓词数；无关对象裁剪 |
| rewrite 合法性验证成本高 | 分层验证：先跑廉价测试淘汰，再跑昂贵测试确认；增量验证：只验证受变化影响的测试子集 |
| 扩展噪声导致错误重编译 | shadow mode 预验证 + 回滚机制 |
| 测试集设计不当导致等价失真 | 从 TAMP benchmark 的标准测试出发，逐步补充 |

### 当前工程结论

> 这套框架在受控局部任务域里可落地；  
> 不适合直接宣称为通用开放世界机器人总语义。

---

## 12. 当前版本最该守住的贡献表述

后面如果需要对外表述，建议统一成下面这版：

> 本文提出一个最小参考语义驱动的机器人语义编译框架。  
> 在该框架中，意义由有限可执行测试诱导，保义由测试保持定义，开放扩展通过受控扩展与重编译机制实现。  
> 核心 thesis 是：开放环境中的持续扩展，不仅依赖新语义的准入，更依赖新语义进入后对内部表示、规则、动作描述与规划问题进行语义保持重写，从而获得系统级优化。

---

## 13. 下一步

最小任务域、rewrite pass 和实验框架已经定了。后续优先级：

1. 实现仿真环境（PyBullet / Isaac Sim）中的桌面整理任务
2. 实现 $Q_\star$ 和 $Q_t^{task}$ 的具体测试接口
3. 实现 5 个 rewrite pass（Section 6.5）并验证合法性检查
4. 运行 5 轮扩展对比实验，收集 Section 9.4 中的四类指标
5. 根据实验结果校准代价函数权重和误差预算参数
6. 只验证最核心 thesis，不要同时验证所有宏大叙事

---

## 14. 一句话收束

> **这项工作的核心，不是“机器人有语义”，而是“机器人一旦有了最小参考语义，就能把内部系统当作可编译 IR，并通过语义保持重写把开放扩展变成结构升级，而不是规则堆积”。**
---

## 参考文献

1. W. Liu, A. Daruna, M. Patel, K. Ramachandruni, S. Chernova. *A survey of Semantic Reasoning frameworks for robotic systems*. Robotics and Autonomous Systems, 159, 2023. [链接](https://www.sciencedirect.com/science/article/abs/pii/S092188902200183X)
2. Y. Zhao et al. *A Survey of Optimization-based Task and Motion Planning: From Classical To Learning Approaches*. arXiv:2404.02817, 2024. [链接](https://arxiv.org/abs/2404.02817)
3. Y. Ding, X. Zhang, S. Amiri, N. Cao, H. Yang, A. Kaminski, C. Esselink, S. Zhang. *Integrating Action Knowledge and LLMs for Task Planning and Situation Handling in Open Worlds*. Autonomous Robots, 47(8), 2023. [链接](https://arxiv.org/abs/2305.17590)
4. C. Li, G. Tian, M. Zhang. *A semantic knowledge-based method for home service robot to grasp an object*. Knowledge-Based Systems, 297, 2024. [链接](https://www.sciencedirect.com/science/article/abs/pii/S0950705124005811)
