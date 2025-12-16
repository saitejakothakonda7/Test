# NEW USE CASE SUMMARY: Dynamic Markdown Optimization

## One-Page Overview

### The Opportunity

Your current **On-Shelf Availability (OSA)** system identifies inventory problems—what's out of stock or overstocked. The new **Markdown Optimization** use case answers the next question: **How do we profitably clear that excess inventory before it becomes dead stock?**

### The Problem

Retailers currently lose **$2-4M annually** (for a $100M retailer) due to:
- **Dead stock accumulation** (10-15% of inventory)
- **Late markdowns** (waiting too long to discount)
- **Over-discounting** (not knowing price elasticity)
- **One-size-fits-all pricing** (not accounting for location differences)

### The Solution

**AI predicts slow-moving inventory 30 days in advance and recommends data-driven markdown prices that maximize margin while clearing stock.**

---

## How It Works (3 Steps)

### Step 1: Predict Slow-Moving Inventory
```
Inputs:    Daily sales, shelf capacity, inventory age
ML Model:  Gradient Boosting (XGBoost)
Output:    Probability that SKU will be slow-moving in 30 days
Example:   "SKU 123 at Store 45 has 75% probability of becoming 
           slow-moving in next 30 days"
```

### Step 2: Estimate Price Elasticity
```
Inputs:    Historical markdowns (12-24 months of data)
           - What price changes drove what demand changes?
ML Model:  Category × Store elasticity regression
Output:    Price elasticity coefficient (e.g., -1.3)
Example:   "A 10% price reduction drives 13% demand uplift 
           in Electronics at urban stores"
```

### Step 3: Optimize Markdown Price
```
Inputs:    Current inventory, cost, elasticity, constraints
Solver:    Constrained linear optimization
Output:    Recommended markdown price & timing
Example:   "Mark down SKU 123 from $100 to $78 (22% off)
           Expected margin: +$350 vs. current path
           Recommended timing: Start Tuesday"
```

---

## Key Metrics & Expected Impact

| Metric | Current | With System | Improvement |
|--------|---------|------------|------------|
| **Dead Stock Rate** | 12% | 6% | ↓50% |
| **Days to Clear Inventory** | 45 days | 20 days | ↓55% |
| **Margin on Clearance Items** | 18% | 21% | ↑3 pts |
| **Inventory Turns** | 8x | 10x | ↑25% |
| **Annual Impact** | — | **+$4-8M** | — |

---

## Data & Technology Stack

### Data Sources (Integration Points)
- ✓ **Inventory Data** (from existing OSA system)
- ✓ **Vendor Lead Times** (from existing OSA system)
- 🔲 Historical Markdown Records (to acquire from POS)
- 🔲 Product Costs (from Finance/ERP)
- 🔲 Competitor Pricing (market intelligence or external API)

### ML & Optimization Technology
```
Feature Engineering  → Pandas, Spark
Prediction Models    → XGBoost, LightGBM
Elasticity Modeling  → Scikit-learn, StatsModels
Price Optimization   → Linear Programming (scipy.optimize)
Deployment           → Databricks, REST API
```

---

## Implementation Timeline

```
Phase 1 (Weeks 1-2):     Data audit, stakeholder alignment
Phase 2 (Weeks 3-6):     Infrastructure setup, data pipeline
Phase 3 (Weeks 7-14):    Model development & training
Phase 4 (Weeks 15-20):   Validation & pilot testing
Phase 5 (Weeks 21-24):   Full deployment
Phase 6 (Months 6+):     Continuous optimization

⏱️ Total: 6 months to full deployment
💰 Cost: $625K
💵 ROI: 6-12x (payback in 2-4 months)
```

---

## Business Value Breakdown

### Financial Impact
```
Revenue Impact:
  - Faster inventory clearance
  - Reduce markdowns beyond planned amounts
  - Avoid write-offs
  ⇒ +$1-2M margin improvement

Cost Reduction:
  - Reduce dead stock carrying costs
  - Fewer write-offs and obsolescence
  ⇒ +$1-2M cost savings

Capital Efficiency:
  - Inventory turns ↑25%
  - Cash tied up in inventory ↓
  ⇒ +$2-4M working capital freed up

Total Annual Benefit: $4-8M
```

### Strategic Benefits
✅ Margin protection during clearance (don't over-discount)
✅ Faster inventory turns (better capital efficiency)
✅ Data-driven pricing (vs. gut-feel decisions)
✅ Location-specific strategies (urban vs. rural dynamics)
✅ Brand protection (controlled clearance approach)

---

## How This Differs from OSA

| Dimension | OSA | Markdown Optimization |
|-----------|-----|----------------------|
| **What it does** | Detects stocking problems | Optimizes pricing & clearance |
| **When** | Daily monitoring | 30-day forward looking |
| **Who uses it** | Inventory managers | Pricing/Merchandising team |
| **Output** | "Fix it" alerts | "Price it optimally" recommendations |
| **Example** | "Out of stock risk in 7 days" | "Mark down to $X by Tuesday" |

**Key Insight:** OSA prevents the problem. Markdown Optimization solves it profitably.

---

## What You Get (Deliverables)

### During Implementation
1. ✅ Data pipeline (automated daily markdown recommendations)
2. ✅ ML models (lifecycle prediction + elasticity estimation)
3. ✅ Optimization engine (calculate optimal prices)
4. ✅ Recommendation dashboard (for pricing team review)
5. ✅ Monitoring system (track accuracy & performance)

### After Launch
1. 📊 Weekly markdown recommendations (SKU × Store × Price)
2. 📈 Performance dashboard (accuracy, margin impact)
3. 🔄 Continuous model updates (weekly retraining)
4. 📱 Mobile-friendly interface for approvers
5. 🔌 API integration with POS/pricing system

---

## Success Criteria

### Phase Gate Targets

**Phase 4 Pilot (Week 20):**
- Slow-moving prediction accuracy: ≥85%
- Elasticity model R²: ≥0.75
- Margin uplift in pilot: ≥2%
- ✓ Go/No-Go decision for full rollout

**Phase 5 Full Launch (Month 6):**
- 90%+ of recommendations deployed
- Recommendation adherence: ≥70%
- Actual vs. predicted margin match: ≤10% error
- Dead stock reduction: 30-40% (vs. baseline)

**12-Month Results:**
- Dead stock: ↓50% (from 12% to 6%)
- Margin improvement: +3-5% on clearance items
- Inventory turns: ↑20% (from 8x to 10x)
- ROI: 6-12x on investment

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| **Brand dilution from aggressive markdowns** | Margin floor constraints, brand protection rules, executive review gate |
| **Elasticity model errors** | Backtest on historical data, pilot validation, weekly monitoring |
| **Over/under-discounting** | Optimization constraints, manual review for edge cases |
| **System adoption resistance** | Change management, clear ROI story, user training |
| **Data quality issues** | Data validation rules, automated monitoring, periodic audits |

---

## Getting Started (Next Steps)

### This Week
- [ ] Schedule kickoff meeting with CFO, SVP Merchandising, Pricing Director
- [ ] Define success metrics & KPI targets
- [ ] Identify data owners for historical markdowns

### Next 2 Weeks
- [ ] Form working group (data scientist, supply chain analyst, finance)
- [ ] Audit current markdown decision process
- [ ] Request historical markdown dataset from POS team
- [ ] Schedule detailed requirements workshop

### Weeks 3-4
- [ ] Begin data collection & pipeline setup
- [ ] Start exploratory data analysis
- [ ] Finalize constraints & business rules
- [ ] Set up infrastructure & development environment

---

## Comparison: Building Blocks

```
           OSA System (Existing)
                  ↓
         [Inventory Problem Detection]
                  ↓
      Identifies what's overstocked
                  ↓
      ← But what's the solution? →
                  ↓
      Markdown Optimization (NEW)
                  ↓
        [Pricing Solution Engine]
                  ↓
      Recommends optimal clearance pricing
                  ↓
      ← Integrated Value Chain →
```

Together: **From Problem Identification to Profitable Resolution**

---

## Quick Facts

**Problem Statement:**
Retailers lose millions annually to dead stock because they lack data-driven markdown strategies.

**Market Size:**
$100M retailer × 10-15% dead stock × 50% recoverable = $5-7M opportunity

**Solution:**
AI predicts slow-moving inventory early and recommends profit-maximizing markdown prices.

**Competition:**
High-end retailers (Nordstrom, Target, Walmart) are already using similar systems → **First-mover advantage critical**

**Effort:**
6 months, $625K, cross-functional team

**Return:**
$4-8M annual benefit, 6-12x ROI, 2-4 month payback

---

## Contact & Questions

**For Technical Questions:**
- Data Science lead at [email]
- Analytics engineering at [email]

**For Business Questions:**
- Pricing strategy lead at [email]
- Supply chain director at [email]

**Executive Sponsor:**
- VP Finance/CFO at [email]

---

## Appendix: Real-World Examples

### Example 1: Seasonal Overstocking
```
Scenario: Summer apparel overstocked as fall approaches
Problem:  Dead stock accumulating, approaching season-end

Current Approach:
  - Wait until September 1st
  - Emergency 50% off clearance
  - Margins collapse on remaining inventory
  - $200K write-off

Markdown Optimization Approach:
  - August 10: System predicts slow-moving (92% probability)
  - August 12: Recommend 22% markdown to $39 (vs. $50)
  - August 15: Start markdown
  - August 31: 85% cleared at 18% margin
  - Result: +$50K margin vs. emergency clearance
```

### Example 2: Competitive Pressure
```
Scenario: Competitor drops prices on electronics
Problem:  Local store losing sales velocity

Current Approach:
  - Match competitor price (react)
  - Often over-discount
  - Margin compression across all channels

Markdown Optimization Approach:
  - System detects sales decline (day 2)
  - Calculates store-specific elasticity
  - Recommends location-specific markdown (competitor price - 5%)
  - Protects other channels & locations
  - Result: Better margin efficiency
```

### Example 3: Demand Forecast Misses
```
Scenario: Forecasted 500 units, only 300 sell
Problem:  200 excess units need clearance

Current Approach:
  - Hope for return order
  - Eventually discount at season-end
  - Tied-up capital for months

Markdown Optimization Approach:
  - Day 14: Predicts this won't sell at regular price
  - Recommends proactive 15% markdown
  - Accelerates clearance to day 28
  - Frees capital 3 weeks early
  - Result: +$15K working capital freed
```

---

**Document Version:** 1.0 | **Last Updated:** December 16, 2025 | **Status:** Ready for Executive Review
