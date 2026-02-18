# OpenVibe OS Strategy Redesign

> Date: 2026-02-18
> Status: Working Document
> Source: Strategic brainstorming session — critical review of GRAND-STRATEGY.md

---

## 1. 核心命题（不变）

**专业服务是最后一个未被工厂化的行业。AI 是那个工厂。**

原策略的命题方向正确，但路径需要重新设计。

---

## 2. 模型重定义：从 Berkshire 到 OS

| | 旧模型：AI-native Berkshire | 新模型：专业服务 OS |
|--|--|--|
| 核心资产 | 持有的公司 | OS 本身（创建和运营能力）|
| 竞争壁垒 | 各 domain 的数据积累 | 进入任何 sub-segment 的速度 |
| 人的角色 | domain expert × 15-20 | meta-judgment（进哪里、退哪里）|
| 复利来源 | 各公司自己的数据 | OS 学会"如何进入新市场"本身 |

**OpenVibe 的核心定义是 OS，不是持有公司的集团。**

---

## 3. 三层架构

```
Layer 1：Brand 层（5-20 个，对外可见）
  例：EduReach / BuildFlow / CareGrowth
  作用：信任容器，行业归属，客户认知
  原则：brand 是 domain-specific 的，每个 brand 下可以有多个 sub-segment

Layer 2：Sub-segment 运营层（最终 1000 个，对外不可见）
  例：Catholic K-12 small / Jewish day schools / Commercial GC small
  作用：实际服务交付单元，飞轮运转的基本粒子

Layer 3：OS 层（1 个，永远不卖）
  作用：扫描市场 → 识别最优 sub-segment → 创建运营单元
       → 监控质量 → 退出低分市场
```

**Brand 与 sub-segment 是 1:N 关系。**
EduReach 下可以同时跑 Catholic K-12、Jewish day schools、Boarding schools 等多个独立飞轮，共享品牌信任，互不干扰。

---

## 4. Sub-segment 选择框架

用 5 维度加权评分模型选择进入顺序：

| 维度 | 权重 | 说明 |
|------|------|------|
| 飞轮密度 | 30% | 社群紧密度，口碑传播速度 |
| AI 可交付率 | 25% | AI 能完成的核心工作比例 |
| 痛点紧迫度 | 20% | 需求急迫 + 预算存在 |
| 竞争空白度 | 15% | AI-native 对手缺失程度 |
| 可达性 | 10% | 通过 Vibe 关系或公开渠道触达难易度 |

工具：`v4/docs/strategy/tools/market_ranker.py`

**当前 top sub-segment（默认权重）：**
1. Catholic K-12, small（综合分 4.62）— Vibe 渠道直达，AI 可交付率最高
2. Jewish day schools, small（4.58）— 飞轮密度最高（PRIZMAH 网络）
3. Private high schools 9-12（4.48）— 招生竞争最激烈，痛点最急迫

**结论：第一个 Brand 是 EduReach，私立学校营销运营。**

---

## 5. 自营 vs 联营

### 自营（OS 直接运营）
适用：AI 可交付率高（>70%）、监管少的 sub-segment
经济：100% 利润归 OpenVibe
例：私立学校营销、建筑商投标运营

### 联营（OS + 外部 domain expert）
适用：监管壁垒域（律所、CPA、医疗）或 OS 尚未成熟的 domain
结构：OpenVibe 30-49% 股权 + domain expert 51-70%
**不是平台收费，是真实股权（Venture Studio 模式，非 PE）**

**联营的真实战略价值：帮 OS 加速学习，不是增长工具。**

```
判断力消长曲线：

  早期：human domain expert judgment > OS judgment  → 联营有优势
  中期：OS 服务 500 家，expert 服务 50 家 → 数据开始倒转
  长期：OS judgment ≥ expert judgment → 自营全面胜出
```

**联营合同必须包含 buyout clause**（OS 到达交叉点时触发），expert 拿流动性，OS 拿全控。联营是过渡结构，不是终态。

---

## 6. Vibe 业务的角色

Vibe 不是独立的业务线，是 OS 的分发 + 数据采集网络。

| Vibe 资产 | 在新框架的战略价值 |
|----------|-----------------|
| 硬件（bot/boards） | 物理占领客户空间，AI 的分发入口 |
| Workspace | 40K 客户的使用习惯 + OS 第一层训练数据 |
| 40K 客户 | Studio 公司（EduReach 等）的预热 pipeline |

**Vibe 业务的演进方向：**
- 现在：卖硬件 + Workspace 订阅
- 未来：硬件是入口，Workspace 是留存，EduReach/BuildFlow 是利润

潜在增量（不需要新客户）：
4,282 家有 boards 的公司 × 30% 触发阈值 = 1,284 家
× $3,000/月 = **$46M ARR Studio upsell 潜力**

---

## 7. 平台架构（三角飞轮）

```
        ┌─────────────────────────────────┐
        │         OS ENGINE               │
        │   (judgment 持续积累)            │
        └──────────┬──────────┬───────────┘
                   ↑ 训练      ↑ 训练
                   │            │
    ┌──────────────┴──┐    ┌───┴──────────────────┐
    │  VIBE WORKSPACE │    │  STUDIO 公司           │
    │  (分发 + 采集)   │    │  EduReach / BuildFlow  │
    │                 │    │                        │
    │  Vibe clients   │──▶ │  portfolio clients     │
    │  宽数据，低质量  │ upsell  高质量，深数据          │
    └─────────────────┘    └────────────────────────┘
```

**四层产品架构：**

- **Layer 1 硬件**：物理分发，占领客户空间
- **Layer 2 Workspace**：DIY + 结构化数据采集（公开产品，Vibe 品牌）
- **Layer 3 触发层**：自动识别 upsell 信号（关键缺失层）
- **Layer 4 Studio 公司**：专业交付，独立 domain 品牌

**触发层设计：**
```
信号：用户每周 >6 小时用于某类专业任务
    + AI 输出修改率 >40%
    + 对应业务指标未改善
→ 动作：推送 Studio 服务（$X/月，释放你的时间）
```

### Workspace vs Studio 的产品定位（不冲突）

| | Workspace（Vibe 品牌） | Studio 公司（domain 品牌）|
|--|--|--|
| 用户心理 | 我来做，给我工具 | 帮我做，我要结果 |
| 定价 | $200/月 | $2,000-5,000/月 |
| 成功指标 | 学会用 AI | 业务数字改善 |
| AI 可见性 | 可见（用户操作 AI）| 不可见（只看到交付物）|

Studio 公司的 AI 对客户完全不可见。客户看到的是"EduReach 帮我做的招生材料"，不是"AI 生成的"。

---

## 8. 术语规范

| 层级 | 内部叫法 | 外部叫法 |
|------|---------|---------|
| EduReach 等的客户 | portfolio client | EduReach client |
| Workspace 的用户 | workspace user | Vibe user / Vibe client |
| OS 架构层 | Studio（内部） | 不对外暴露 |

---

## 9. 执行路径

```
Phase 0（现在）：
  OpenVibe engine 成熟（SDK → Platform → HTTP layer）
  Vibe bot 出货，扩大分发网络

Phase 1（M3-6）：
  启动 EduReach（第一个 Brand）
  目标 sub-segment：Catholic K-12 small，直接用 Vibe K-12 渠道
  目标：前 20 个付费客户，验证飞轮（口碑转介绍率）

Phase 2（M6-12）：
  EduReach 扩展到 2-3 个 sub-segment（Jewish day schools、Private high schools）
  建立触发层，Workspace → EduReach 自动 upsell 流程
  启动第二个 Brand（BuildFlow，AEC）

Phase 3（M12-24）：
  3-5 个 Brand，每个 Brand 下 2-4 个 sub-segment
  联营结构启动（监管域，如 CPA、法律）
  OS judgment 开始超越早期联营 expert
```

---

## 10. Kill Signals（不变，从原策略保留）

- M3：AI 交付质量被客户评为"不如自己做" → 引擎前提不成立
- M6：EduReach 无法通过口碑获得第二批客户 → 飞轮前提不成立
- M12：第二个 Brand 无法在 3 个月内获得第一个付费客户 → 跨 domain 迁移失败

---

*The endgame is an OS that can enter any professional services sub-segment faster than any competitor. Phase 0 proves the engine. EduReach proves the flywheel. Everything else follows.*
