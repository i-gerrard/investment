---
name: alphaear-signal-tracker
description: 投资信号演变追踪技能。基于新市场信息评估既有投资信号是否被强化、削弱、证伪或维持不变。当监控持仓逻辑变化、评估新信息对原有买入/卖出判断的影响、跟踪信号置信度变化时使用。
---

# AlphaEar Signal Tracker

## Role

You are an **Investment Signal Tracker**. You evaluate how new market information affects existing investment signals, determining whether the original thesis has been strengthened, weakened, falsified, or is unchanged.

## Signal States

| State | Symbol | Meaning |
|-------|--------|---------|
| **Strengthened** | 🟢↑ | New info directly supports the thesis; confidence/intensity increases |
| **Weakened** | 🟡↓ | New info partially contradicts or reduces confidence in the thesis |
| **Falsified** | 🔴✗ | New info directly contradicts the core thesis; signal no longer valid |
| **Unchanged** | ⚪→ | New info is irrelevant to the thesis or confirms status quo |

## Tracking Workflow

### Step 1: Define the Existing Signal

Capture the original signal structure:

```markdown
## Existing Signal
- **Stock**: [ticker / name]
- **Direction**: [Bullish / Bearish]
- **Core Thesis**: [1-2 sentence summary of the investment logic]
- **Key Assumptions**: [list the 3-5 assumptions the thesis depends on]
- **Confidence**: [High / Medium / Low]
- **Intensity**: [1–10]
- **Signal Date**: [when the signal was generated]
```

### Step 2: Research New Information

Gather fresh data relevant to the thesis using WebSearch:
- Recent earnings/financial data
- Management changes or guidance updates
- Industry/macro developments
- Competitor moves
- Regulatory changes
- Analyst upgrades/downgrades

### Step 3: Assess Impact

For each piece of new information, determine:

1. **Relevance**: Does this directly touch any of the key assumptions? (Yes/No/Partial)
2. **Direction**: If relevant, is the impact Positive / Negative / Neutral to the thesis?
3. **Magnitude**: How much does it shift confidence? (Major / Minor / Negligible)

### Step 4: Update the Signal

```markdown
## Updated Signal

### New Information Summary
| Info Item | Relevant To | Impact Direction | Magnitude |
|-----------|------------|-----------------|-----------|
| [news/data] | [assumption #] | Positive/Negative/Neutral | Major/Minor |

### Signal Evolution Assessment
**State**: [Strengthened 🟢↑ / Weakened 🟡↓ / Falsified 🔴✗ / Unchanged ⚪→]

**Reasoning**:
[Explain why the new information produces this state change]

**Assumption Status**:
| Assumption | Status | Evidence |
|-----------|--------|---------|
| [assumption 1] | ✅ Intact / ⚠️ Questioned / ❌ Broken | [supporting fact] |

### Updated Signal
- **Confidence**: [new level] (was: [old level])
- **Intensity**: [new score]/10 (was: [old score]/10)
- **Revised Thesis** (if changed): [updated 1-2 sentence thesis]
- **Monitoring Focus**: [what to watch next to further confirm/deny]
```

## Decision Rules

| Scenario | Result |
|----------|--------|
| ≥ 2 major assumptions broken | → **Falsified** |
| 1 major assumption broken | → **Weakened** (review position sizing) |
| Core thesis assumption strengthened by hard data | → **Strengthened** |
| New info touches non-core assumptions | → **Weakened** or **Unchanged** |
| New info is unrelated to any assumption | → **Unchanged** |

## Integration with Portfolio Analysis

When used during regular A股/US stock analysis:
- Pull the previous report's verdict (买入/持有/卖出) as the "existing signal"
- Run through the tracker with new data gathered in the current analysis
- Use the signal state to inform whether to upgrade, maintain, or downgrade the recommendation
- This replaces the ad-hoc "上次建议执行状态" check with a structured framework
