# ICP Research: OpenVibe 第一个理想客户画像

> Date: 2026-02-18
> Status: Research Note
> Context: 基于 V2 thesis/strategy + V4 thesis + dogfood-GTM + 8-angle analysis 的综合研判
> Core Question: 到底是10x放大现有硬件生意，还是找到范式转化的新ICP win big？

---

## 0. 先说结论

**两个都不完全对。真正的答案是分阶段、分层次。**

| 阶段 | 策略 | 目的 | ICP |
|------|------|------|-----|
| Phase 0 (现在) | Dogfood at Vibe | 验证thesis, 提取playbook | 自己 |
| Phase 1 (Month 1-6) | 10x Vibe GTM | 证明cognition infrastructure work | Vibe = proof point |
| Phase 2 (Month 6+) | 真正的ICP决策 | 根据dogfood数据做evidence-based decision | 见下方分析 |

**但最关键的洞察是：Phase 2 的 ICP 选择，取决于 Phase 1 dogfood 过程中，哪一层价值被验证了。**

---

## 1. 拆解问题：到底在问什么

用户的问题其实有5层：

### Q1: 红利到底是什么？
> "红利本质上是micro segment of customer journey? 还有其他的吗？"

### Q2: 产品核心是什么？
> "产品上核心是更多的product？"

### Q3: 这些优势牢固吗？
> "但这些真正牢固而不会在未来发生变化吗？"

### Q4: 趋势上哪个靠谱？
> "哪个是真正在趋势上的靠谱策略？"

### Q5: 放大 vs 范式转化？
> "10x放大现有硬件生意 vs 找到范式转化的点win big？"

---

## 2. Q1: 红利到底是什么？

### Micro-segmentation 只是冰山一角

Micro-segmentation of customer journey（微分客户旅程）确实是当前最直接可见的红利。但它只是「认知基础设施化」带来的 **一个应用**，不是红利本身。

**红利的全景图：**

```
Root: 认知变成基础设施
  ↓
红利层1: 认知杠杆 (Cognitive Leverage)
  - 1个人 orchestrate 10个 agent = 10x 产出
  - 例：1个CMO + agents = 10个marketer的产出
  ↓
红利层2: 并行执行 (Parallel Execution)
  - 同时做10件事，而不是串行
  - 例：10个campaign同时跑, 100个micro-segment同时覆盖
  ↓
红利层3: 速度-to-洞察 (Speed to Insight)
  - Agent团队几小时完成人类几周的分析
  - 例：竞品分析、客户研究、market mapping
  ↓
红利层4: 制度记忆 (Institutional Memory)
  - 知识复利，不再 start from zero
  - 例：新人 Day 1 productive，不用6周上手
  ↓
红利层5: 以前不可能的事变可能 (Previously Impossible)
  - 不是10x更快做同样的事，而是做以前做不了的事
  - 例：为每个客户定制proposal，给每个lead个性化nurture sequence
```

**Micro-segmentation 属于红利层2+5：并行覆盖100个segment + 以前不可能的个性化程度。**

### 但哪个红利是真正的 moat？

| 红利 | 是否可复制？ | 持久性 |
|------|-------------|--------|
| 认知杠杆 | **是** — 所有公司都能用agents | 0（不是moat） |
| 并行执行 | **是** — table stakes | 0 |
| 速度-to-洞察 | **是** — 模型对每个人都变好 | 0 |
| 制度记忆 | **部分** — 数据是你自己的 | 12-24个月 |
| Previously Impossible | **取决于** — 在哪个domain做 | 取决于domain |

**关键洞察：所有的执行层红利（层1-3）都不是moat。每个公司都会用agents。这些不构成竞争优势。**

**真正的moat candidates：**
1. **Accumulated organizational intelligence** — 你的数据 + 你的学到的pattern（12-24个月优势）
2. **Proven playbooks with track record** — 不能copy因为需要证明（需要时间建立）
3. **Distribution/Network effects** — Partner网络、数据网络效应（2-5年如果建成）

---

## 3. Q2: 产品核心是什么？

### "更多的product" 是症状，不是核心

用agents build更多产品（5个同时 vs 1个串行），确实是cognition infrastructure带来的能力。但这对每个公司都成立——不是OpenVibe独有的。

### 真正的产品核心应该是什么？

V4 thesis 给出了框架：

```
Layer 1: Foundation Models (40% value capture) — 不是我们
Layer 2: Orchestration Platform (30% value capture) — 这是机会
Layer 3: Domain Playbooks (20% value capture) — 这也是机会
Layer 4: Service Delivery (10% value capture) — 不值得做
```

**OpenVibe 的产品核心 = Layer 2 + Layer 3 = Orchestration Platform + Domain Playbooks**

具体来说：

| 产品 | 描述 | 收入模式 | Moat |
|------|------|----------|------|
| **OpenVibe Platform (OSS)** | Agent orchestration infrastructure | 开源，不直接收费 | Distribution + Trust |
| **Domain Playbooks** | 验证过的transformation配方 | 商业授权，$X/月 | Proven track record |
| **Transformation Services** | 帮客户做transformation | Consulting fee | Relationship + expertise |

**"更多product"不是产品策略。Platform + Playbooks 才是。**

### 为什么 Playbooks 特别重要？

V4 DOGFOOD-GTM.md 的策略其实已经暗示了：

```
Vibe dogfood → Extract playbook → Sell playbook
```

Playbook 的价值不在于「配置文件」本身（可以copy），而在于：
1. **Proven** — "我们自己用了6个月，25x qualified leads"
2. **Refined** — 经过feedback loop打磨的，不是空想的
3. **Complete** — 包含所有edge case处理，不是demo版
4. **Supported** — 有人帮你deploy和customize

---

## 4. Q3: 这些真正牢固吗？

### 诚实的答案：大部分不牢固

| 假设的优势 | 牢固吗？ | 为什么？ |
|-----------|---------|---------|
| Micro-segmentation能力 | **不牢固** | 每个公司都能用agents做 |
| 更多products更快 | **不牢固** | 每个公司都能用agents build |
| Agent output质量 | **不牢固** | 模型对所有人都在变好 |
| Open source | **中等** | Anthropic不会做，但不代表其他人不会做 |
| Multi-model | **中等** | 结构性差异，但如果一个model win big，multi-model变成劣势 |
| Partner network | **中等-高** | 需要2年建设，如果建成则有switching cost |
| Hardware in rooms | **中等** | Anthropic没有，但whiteboard market有限 |
| Accumulated context | **中等** | 12-24个月优势（8-angle analysis确认），不是5年 |
| Proven playbooks | **高** | 需要时间和证据建立，不可shortcut |
| Cross-workspace data | **高（如果达到规模）** | 需要1000+ workspaces才有用，如果有则不可复制 |

### 8-Angle Analysis 的关键发现（V2）

> "Context = 12-24 month advantage (not 5-year moat). Better model (Opus 5) beats context-rich agent on 60-70% of tasks."

这是非常重要的: **Context accumulation 不是5年moat，而是12-24个月。** 模型进步可以在大多数任务上打败accumulated context。

### 什么是真正牢固的？

只有两类东西在长期是牢固的：

**1. Network effects at scale**
- 如果你有10,000+ workspaces的数据网络效应 → 不可复制
- 如果你有200+ certified partners → switching cost high
- **但这需要先达到规模**

**2. Speed + compound execution**
- 不是任何一个时刻的优势
- 而是「持续比别人快」的能力
- 这取决于组织能力，不是产品feature

**诚实结论：在当前阶段（pre-product），几乎没有什么是牢固的。所有优势都是暂时的。关键是选对方向然后跑得足够快。**

---

## 5. Q4: 趋势上哪个靠谱？

### 三个可能的趋势方向

#### 趋势A: AI-enhanced collaboration tools
- Slack AI, Teams Copilot, Anthropic Cowork 都在这里
- 市场大，但竞争激烈
- OpenVibe在这里 = 和巨头正面竞争
- **靠谱程度：低。** 巨头会赢collaboration tool的战争

#### 趋势B: Organizational transformation platform
- V4 thesis 的方向："cognition becomes infrastructure → organizations restructure"
- 帮企业从100人 → 8人+agents
- 不是工具，是transformation
- **靠谱程度：高，但execution risk极高。** 这是real wave，但能不能catch取决于timing和execution

#### 趋势C: Vertical AI solutions
- 不做horizontal platform，做特定行业的全栈AI解决方案
- 例：AI for AEC firms, AI for accounting firms
- 深度 > 广度
- **靠谱程度：中-高。** 更容易defend，但市场小

### 我的判断

**趋势B是the real wave，但需要趋势C的执行方式。**

解释：
- "Cognition becomes infrastructure" 是真正的paradigm shift（V4 thesis is right）
- 但horizontal platform面对巨头竞争是suicide
- 正确的打法：**用趋势B的thesis，以趋势C的方式切入**
- 即：选一个vertical，在那个vertical里做organizational transformation的full stack

**类比：**
- Salesforce 不是"CRM tool"，是"sales transformation platform"
- 但它从一个vertical（sales）开始，然后扩展
- OpenVibe 应该是"organizational transformation platform"
- 但应该从一个vertical开始，然后扩展

---

## 6. Q5: 10x放大 vs 范式转化 — 核心分析

### Option A: 10x放大Vibe硬件生意

**做法：**
- 用OpenVibe agents帮Vibe做GTM
- 产出更多leads → 卖更多boards
- ICP = 现有whiteboard buyers

**优点：**
- 低风险，可预测
- 现有客户base（40K boards）
- 硬件 + 软件 bundling
- 立即可执行

**缺点：**
- Whiteboard market有天花板
- 不riding the wave
- 即使10x，也只是从$30M → $300M（还是whiteboard公司）
- 没有paradigm shift的upside
- Hardware margins low, competitive

**这是local maximum。安全但有限。**

### Option B: 范式转化 — 找新ICP，Win Big

**做法：**
- 用"cognition becomes infrastructure"的thesis
- 找一个行业，做organizational transformation
- ICP = 新市场

**优点：**
- 巨大市场（$13.8B TAM per V2 analysis）
- Riding the wave
- 如果赢了 = $1B+ company
- 真正的paradigm shift

**缺点：**
- 高风险
- V2的partner-led GTM假设未验证
- 和Anthropic Cowork正面竞争
- 需要至少6-12个月才能see signal

**这是global maximum。高upside但高risk。**

### Option C（我的建议）: 两个都不完全是 — 而是分层策略

```
Layer 1: 用A来fund和prove B
  Dogfood at Vibe → 10x GTM → 证明thesis → 增加revenue
  这给你runway和proof point

Layer 2: 用dogfood过程中的数据来决定B的ICP
  不要现在猜ICP
  而是在dogfood过程中观察：
  - 哪个playbook generalize最好？
  - 哪个vertical的partner最excited？
  - 哪个transformation最dramatic？

Layer 3: ICP决策是Month 6的事，不是现在的事
  现在做决定 = 基于假设
  Month 6做决定 = 基于证据
```

---

## 7. 那如果非要现在选ICP呢？

如果必须现在就有一个方向，我的分析如下：

### 评估框架

根据V4 thesis，最佳ICP满足：
1. **认知 = 瓶颈** — 公司的增长被cognitive capacity限制
2. **认知 = 产品** — 公司卖的就是thinking
3. **有硬件交叉点** — Vibe的board在场景中有用（optional but unique）
4. **中等规模** — 50-500人，能做transformation但不bureaucratic
5. **Growth pain** — 正在经历growth cap，愿意尝试新方法
6. **已有关系** — Vibe已经有touchpoint

### 候选ICP排名

| ICP | 认知=瓶颈 | 认知=产品 | 硬件交叉 | 中等规模 | Growth pain | 已有关系 | 总分 |
|-----|----------|----------|---------|---------|------------|---------|------|
| **1. Management Consulting** | ★★★★★ | ★★★★★ | ★★★★ | ★★★★ | ★★★ | ★★★★ | 26 |
| **2. Vibe-like HW+SW companies** | ★★★★ | ★★★ | ★★★★★ | ★★★★ | ★★★★★ | ★★★ | 24 |
| **3. Marketing/Creative Agencies** | ★★★★ | ★★★★★ | ★★★ | ★★★★★ | ★★★★ | ★★ | 23 |
| **4. Accounting Firms** | ★★★★ | ★★★★ | ★★★ | ★★★★ | ★★★ | ★★★ | 21 |
| **5. AEC (Architecture/Eng)** | ★★★ | ★★★ | ★★★★★ | ★★★ | ★★★ | ★★★★ | 21 |
| **6. MSPs** | ★★★ | ★★★ | ★★ | ★★★★ | ★★★★ | ★★★ | 19 |
| **7. SaaS Startups** | ★★★★★ | ★★★★ | ★ | ★★★★★ | ★★★★★ | ★ | 20 |

### 为什么 Management Consulting 仍然排第一

尽管V2的partner-led strategy有问题（太aggressive的数字），consulting作为ICP的本质优势没变：

1. **他们卖的就是thinking** → cognition infrastructure对他们是existential
2. **他们有meeting rooms** → Vibe board有用武之地
3. **他们serve other companies** → B2B2B flywheel
4. **他们是early adopter** → McKinsey已经在用AI
5. **Vibe已经有关系** → 可以fast start

### 但V2的错误在于execution plan，不是ICP选择

V2的问题不是选错了ICP，而是：
- Partner-led distribution的数字太aggressive（120 partners → 11,500 customers in 18 months）
- 没有先dogfood验证
- 从partner-led开始而不是从self-use开始

**V4的dogfood-first修正了这个execution错误。**

### 第二选择：Vibe-like companies（硬件+软件公司）

这是一个有趣的alternative ICP：
- Revenue $10-100M, growth stalled
- 有hardware产品但需要software/AI transformation
- GTM bottlenecked
- 50-200 employees
- CEO understands "need to transform but don't know how"

**优势**：Vibe的故事 = 他们的故事。"We were a $30M hardware company with flat growth. We transformed ourselves with cognition infrastructure. Revenue 3x. Now we help you do the same."

**劣势**：Market smaller than professional services. Less "cognition = product" than consulting.

---

## 8. 我的最终建议

### 短期（Month 1-6）：不要选ICP。先Dogfood。

V4的dogfood-first策略是对的。不要在没有数据的时候选ICP。

但dogfood过程中，**刻意设计实验来回答ICP问题**：

| 实验 | 要回答的问题 | 怎么做 |
|------|------------|--------|
| Dogfood GTM playbook | 这个playbook对consulting firm也适用吗？ | Month 3拿给2-3个consulting firm看reaction |
| Dogfood CS playbook | CS transformation对MSP也适用吗？ | Month 5拿给1-2个MSP看reaction |
| Board + AI integration | 哪个场景board最不可替代？ | 记录所有board interaction，分析which ones are unique |
| Revenue impact | 10x GTM真的能deliver吗？ | Track actual lead/conversion metrics |

### 中期（Month 6+）：Evidence-based ICP decision

Month 6的时候，你应该有数据来回答：
1. Playbook能generalize吗？→ 如果能，ICP = consulting firms（卖playbook + platform）
2. Playbook不能generalize？→ ICP = Vibe-like companies（卖transformation service）
3. Board是unique advantage吗？→ 如果是，ICP must involve meeting rooms
4. 10x真的实现了吗？→ 如果是，proof point强，可以aggressive ICP

### 长期方向判断：趋势的赢家是谁？

**最终的战略判断：**

```
短期（1-2年）: 谁有最好的playbook → wins early customers
中期（2-4年）: 谁有最大的partner network → wins distribution
长期（4+年）: 谁有最多的accumulated intelligence → wins the market
```

OpenVibe的策略应该是：
1. **短期**用dogfood产出最好的playbook（GTM transformation playbook）
2. **中期**用partner-led distribution建network（但比V2保守，从10个partner开始）
3. **长期**accumulated intelligence成为moat

**这不是"10x硬件" vs "范式转化"的二选一。**
**这是"先用硬件生意fund和prove transformation thesis，然后在有证据后决定expansion direction"。**

---

## 9. 反对意见和风险

### 反对意见1: "先dogfood太慢了，window只有6-9个月"

V2 8-angle analysis说Anthropic Cowork会在Q3 2026 ship team features。如果等到Month 6才选ICP，可能太晚。

**回应**：Anthropic的team features和OpenVibe的organizational transformation是不同的product。Cowork is "个人AI assistant + team sharing"。OpenVibe is "organizational restructuring with agents"。这不是同一个market。Window更大，大概18-24个月。

### 反对意见2: "Professional services已经被研究很多了，为什么不直接去"

因为V2的120 partners → 11,500 customers假设没有任何validation。在Vibe自己都没prove cognition transformation works之前，去卖给consulting firms = 卖vapor ware。Dogfood-first是必须的。

### 反对意见3: "为什么不直接做SaaS startup market？他们最pain也最willing to adopt"

因为：
1. SaaS startups不用meeting room boards → 没有hardware交叉
2. SaaS startups太diverse → 很难做standardized playbook
3. Competition最激烈（every AI tool targets startups first）
4. 但可以作为secondary ICP if playbook generalizes well

### 反对意见4: "如果cognition infrastructure is real wave，应该all-in，不要半心半意"

同意wave is real。但all-in在哪里？
- All-in platform? → 和LangChain, CrewAI竞争
- All-in consulting? → 和McKinsey, Accenture竞争
- All-in vertical? → 需要先知道哪个vertical

Dogfood = 用最低风险的方式搞清楚all-in的方向。

---

## 10. Action Items

1. **继续执行V4 dogfood策略** — 这是对的
2. **在dogfood中embed ICP validation实验** — 不要等到Month 6才开始想
3. **Month 3做first external validation** — 拿playbook给2-3个consulting firm看
4. **Track what's unique to Vibe vs generalizable** — 这决定ICP
5. **不要过度依赖V2的partner-led数字** — 那些数字是theoretical，需要validation

---

## 附录：文档交叉引用

| 文档 | 关键洞察 | 与ICP问题的关系 |
|------|---------|----------------|
| V2 THESIS | "AI is a colleague, not a tool" | 方向对，但太focused on workspace UX |
| V2 STRATEGY | Partner-led, $61M ARR, 120 partners | 数字太aggressive，但ICP选择(prof services)是对的 |
| V2 8-ANGLE | Context = 12-24 month moat, not 5 year | 限制了moat的幻想 |
| V2 CUSTOMER-FOUNDATION | Consulting/Accounting/MSP ICP profiles | 详细的buyer persona，可复用 |
| V4 THESIS | "Cognition becomes infrastructure" | 更big picture的thesis，比V2更对 |
| V4 DOGFOOD-GTM | Start with Vibe GTM, extract playbook | Execution plan是对的 |
| V4 ROADMAP | 25 agents across M&S, CS, Product | 具体的transformation blueprint |

---

*This is a research note, not a decision document. The ICP decision should be made at Month 6 with evidence, not now with assumptions.*

---

## 11. Update: "会不会选了一个即将被AI杀死的行业？"

> Date: 2026-02-18 (same day follow-up)

### 核心洞察：Consulting 是危险的 ICP

V4 thesis 说 "认知=瓶颈 AND 认知=产品" 的行业变化最大。但"变化最大"有两种：
- **Transform**: 活下来但面目全非（会计 — CPA牌照保护）
- **Die**: 被替代（中低端咨询 — 卖的就是thinking，没有护城河）

Mid-market consulting 卖的是分析和执行本身 — 这正是 AI 直接替代的。选它当 ICP = 给将死之人卖药。

### 2x2 生死矩阵

```
              认知是产品          认知不是产品
            ┌─────────────────┬─────────────────┐
 有护城河    │ TRANSFORM       │ AUGMENT ← BEST  │
 (监管/物理  │ 会计, 法律,     │ 制造, 医疗,      │
  /信任)     │ 顶级咨询        │ 建筑, 房地产     │
            ├─────────────────┼─────────────────┤
 无护城河    │ DIE ← AVOID     │ LEAN OUT         │
            │ 中低端咨询,      │ 一般行政,        │
            │ 市场调研,        │ 客服外包         │
            │ 内容农场         │                  │
            └─────────────────┴─────────────────┘
```

**最安全的 ICP = AUGMENT 象限：认知不是产品但是瓶颈，且有物理/监管护城河。**

### 更好的 ICP：不选行业，选公司画像

**"GTM-Bottlenecked Scale-Up" archetype:**
- Revenue: $10-100M
- 人数: 50-300
- 增长卡住（leads不够，conversion不够）
- CEO 知道要 transform 但不知道怎么做
- 预算: $50-200K/year
- 行业不限（但最好有物理/监管护城河）

**Vibe 自己就是这个画像** → 完美 proof point。

**为什么比 consulting 更好：**
1. 不会被 AI 杀死（他们用 AI 增长）
2. 不会偷 playbook 竞争（他们不是 AI 公司）
3. Vibe 是 perfect proof point
4. 100,000+ companies cross-industry（远大于 15,000 consulting firms）
5. 购买动力是 "10x growth" 而不是 "我们也该用 AI"

### 修正后的策略

```
Phase 0 (现在): Vibe dogfood → 证明 thesis
Phase 1 (M6): 卖给 "和 Vibe 一样的公司" → GTM-bottlenecked, $10-100M, 有护城河
Phase 2 (M12+): 扩展到更多 archetype → CS-bottlenecked, Product-bottlenecked
```
