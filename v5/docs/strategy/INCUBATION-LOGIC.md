# Incubation Logic

> Six-stage lifecycle for creating and managing professional services brands.

---

## Overview

Every brand created by Astrocrest passes through six stages. Movement between stages is gated by explicit entry criteria — not time elapsed. A stage can be skipped only if its criteria are pre-met. Abort decisions are cheaper than rescue operations.

```
Scan → Score → Create → Launch → Monitor → Exit/Scale
```

---

## Stage 1: Scan

**Purpose:** Build a continuously updated map of professional services sub-segments.

**Entry criteria:** Ongoing (no gate — always running).

**Key outputs:**
- Sub-segment identification: named niche + client archetype + annual spend estimate
- Distribution channel candidates (Vibe channel, direct, association)
- Initial AI deliverability estimate
- Flywheel density proxy (conference exists? peer network tight?)

**Decision rule:** Sub-segment passes to Score if estimated AI deliverability > 50% AND a plausible distribution path exists.

**Abort rule:** If no distribution path and no Vibe channel overlap → skip.

---

## Stage 2: Score

**Purpose:** Apply the 5-dimension scoring framework to rank candidates.

**Entry criteria:** Sub-segment identified with plausible distribution path.

**Key outputs:**
- 5D score (weighted total out of 5.0)
- Confidence level (low/medium/high based on data quality)
- Phase 1 recommendation (self-operated / JV / pass)
- Comparable sub-segments for benchmark

**Decision rule:**
- Score ≥ 4.0 → advance to Create
- Score 3.5-3.9 → hold for rescore in 90 days
- Score < 3.5 → pass

**Abort rule:** If AI deliverability score < 0.4 (even with high flywheel density) → pass. We can't deliver.

---

## Stage 3: Create

**Purpose:** Define the brand and build its initial operational structure.

**Entry criteria:** Score ≥ 4.0, human confirmation on self-operated vs. JV.

**Key outputs:**
- Brand definition: name, positioning, client archetype, pricing model
- First role configs (YAML): 3-5 roles minimum to deliver first client
- SOUL config: workspace identity and philosophy
- First client archetype document (who they are, what they need, what success looks like)
- Go-to-market hypothesis: first channel + first message

**Decision rule:** Brand creation is complete when the first role can deliver a full engagement without human intervention on 70%+ of tasks.

**Abort rule:** If SOUL config requires too much human judgment on core tasks → reassess AI deliverability. May need to rescope the offering.

---

## Stage 4: Launch

**Purpose:** Acquire first 3-5 paying clients. Validate flywheel hypothesis.

**Entry criteria:** Brand definition complete, first roles operational.

**Key outputs:**
- First paying client acquired
- First AI-delivered engagement completed
- Client satisfaction score (target: ≥ 4.2/5.0)
- First referral signal (or absence of it)
- Operating cost per engagement

**Decision rule:** Advance to Monitor when 3 clients paying AND at least 1 referral inquiry received.

**M3 kill signals (abort Launch):**
- No paying client by M3
- AI deliverability < 50% in practice (estimated was wrong)
- Referral pipeline = 0 after first 3 clients
- Any two of the above → abort

---

## Stage 5: Monitor

**Purpose:** Measure flywheel velocity and economics at scale (M3-M12).

**Entry criteria:** 3+ paying clients, 1+ referral inquiry.

**Key outputs:**
- Monthly ARR and growth rate
- Flywheel conversion rate (referral inquiries → paying clients)
- AI deliverability (actual vs. estimated)
- Client satisfaction trend
- Operating margin

**Decision rule:** Advance to Scale when ARR > $150K AND flywheel rate > 20% AND margin > 30%.

**Kill signals (exit Monitor):**
- M6: Monthly revenue < $15K OR satisfaction < 4.0 → restructure
- M12: ARR < $150K OR flywheel rate < 20% → wind down

---

## Stage 6: Exit/Scale

**Two paths based on Monitor outcomes:**

**Scale:** ARR > $150K, flywheel confirmed, margin healthy → invest in additional roles, expand to adjacent sub-segments within same brand, consider second Brand creation.

**Exit:** Persistent kill signals → structured wind-down. Preserve role configs and domain playbooks — they teach the OS even when a brand fails.

---

## Data Models

```python
SubSegment:
  - id: str
  - name: str
  - client_archetype: str
  - estimated_annual_spend: float
  - ai_deliverability_estimate: float
  - flywheel_density_score: float
  - distribution_channels: list[str]
  - stage: Literal["scan", "score", "create", "launch", "monitor", "exit", "scale"]

Brand:
  - id: str
  - name: str
  - sub_segment_id: str
  - ownership: Literal["self_operated", "jv"]
  - soul_config_path: str
  - roles: list[str]
  - created_at: datetime
  - stage: Literal["create", "launch", "monitor", "scale", "wound_down"]

Company:  # instance of a Brand serving a client
  - id: str
  - brand_id: str
  - client_id: str
  - arr: float
  - satisfaction_score: float
  - referral_count: int
  - ai_deliverability_actual: float
  - created_at: datetime

FlyWheelMetric:
  - brand_id: str
  - period: str  # "M3", "M6", "M12"
  - referral_inquiries: int
  - referral_conversions: int
  - conversion_rate: float
  - pipeline_referral_pct: float  # % of pipeline from referrals
```
