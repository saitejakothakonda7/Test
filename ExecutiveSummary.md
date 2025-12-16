# EXECUTIVE SUMMARY TABLE: New Markdown Optimization Use Case

## Quick Lookup Reference

### What You're Getting

| Item | Details |
|------|---------|
| **Use Case Name** | Dynamic Markdown Optimization & Inventory Clearance Prediction |
| **Problem Solved** | How to profitably clear slow-moving inventory before it becomes dead stock |
| **Business Impact** | +$4-8M annual margin improvement (for $100M retailer) |
| **Implementation Time** | 6 months |
| **ROI** | 6-12x; payback in 2-4 months |
| **Complexity** | Medium (moderate ML, high integration) |
| **Risk Level** | Low-Medium (mitigated by constraints & approval gates) |

---

### The Three-Model Stack

| Model | Algorithm | Input Data | Output | Use |
|-------|-----------|-----------|--------|-----|
| **Lifecycle Predictor** | XGBoost Classifier | 9 time-series features | Probability (0-1) slow-moving in 30 days | Identify clearance candidates |
| **Elasticity Estimator** | Mixed Effects Regression + LightGBM | Historical markdowns (12-24 mo) | Elasticity coefficient by category+store | Predict demand impact of price changes |
| **Markdown Optimizer** | Constrained Optimization (SLSQP) | Price, cost, elasticity, constraints | Optimal markdown price (maximizes margin $) | Calculate best discount level |

---

### Data Requirements

| Data Element | Source | Frequency | Size | Status |
|---|---|---|---|---|
| Inventory snapshots | OSA system (osa_raw_data.csv) | Daily | 40K+ records/day | ✅ Have |
| Vendor lead times | OSA system (vendor_leadtime_info.csv) | Static | 100 records | ✅ Have |
| **Historical markdowns** | POS system | Historical (12-24 mo) | 10K-100K records | 🔲 Need |
| **Product costs** | ERP/Finance | Static | 100-1000 SKUs | 🔲 Need |
| **Competitor pricing** | Market intelligence | Daily (optional) | Store-level | 🔲 Optional |
| **Promotional calendar** | Marketing | Monthly | Event-level | 🔲 Need |

---

### Financial Model

```
Investment:
  Personnel (6 months):          $300K
  Infrastructure/Tools:           $50K
  Testing & Validation:           $25K
  Ongoing Operations (6 months):  $250K
  ─────────────────────────────
  Total Year 1:                   $625K

Returns:
  Margin improvement (3-5% on clearance items)        +$2-4M
  Dead stock reduction (40-50% fewer write-offs)      +$1-2M
  Working capital freed (inventory turns ↑25%)        +$2-4M
  ─────────────────────────────
  Total Year 1 (Conservative):    +$5-10M

ROI: 6-12x
Payback Period: 2-4 months
```

---

### Success Metrics by Phase

| Phase | Gate | Metric | Target | Pass/Fail |
|-------|------|--------|--------|-----------|
| **Weeks 1-2** | Setup | Data audit complete | 100% identified | ✓ Required |
| **Weeks 3-6** | Infrastructure | Feature store live | Daily updates | ✓ Required |
| **Weeks 7-14** | Model Dev | Model accuracy | 85%+ accuracy | ✓ Required |
| **Weeks 15-20** | Pilot | Margin uplift | ≥2% vs baseline | ✓ Go/No-Go |
| **Weeks 21-24** | Launch | Recommendation adoption | ≥70% approval | ✓ Go/No-Go |
| **Month 6** | Full Scale | Dead stock reduction | ≥30% vs baseline | ✓ Target |
| **Month 12** | Annual Review | Total margin impact | +$4-8M | ✓ Target |

---

### Feature Engineering Details

```
INPUT DATA (from OSA system)
  ├─ Daily Sales Units
  ├─ On-Hand Inventory
  ├─ Replenishment Flag
  ├─ Shelf Capacity
  └─ Product Category

TIME-SERIES FEATURES (generated)
  ├─ sales_7day_ma               ← 7-day moving average
  ├─ sales_30day_ma              ← 30-day baseline
  ├─ sales_momentum              ← Acceleration/deceleration
  ├─ days_since_replenishment    ← Inventory age
  ├─ shelf_utilization_ratio     ← Capacity vs actual
  ├─ days_to_deplete             ← Depletion projection
  ├─ pipeline_ratio              ← Incoming/current inventory
  ├─ zero_sales_streak           ← Consecutive non-sale days
  └─ replenishment_flag          ← Recent restocking indicator

RESULTING DATASET
  Grain: store_id × sku × date
  Records: 40,000+ daily
  Features: 20+
  Target: is_slow_moving (binary)
```

---

### Model Performance Expectations

#### Lifecycle Predictor (Slow-Moving Detection)
```
Metric              Expected  Benchmark   Note
─────────────────────────────────────────────────
Accuracy            85-90%    Static rules (60-70%)
Precision (Recall): 85%+      Minimize false alarms
AUC-ROC             0.88-0.92 High discrimination
F1 Score            0.85+     Balanced performance

Interpretation:
  • 85% of slow-moving items correctly identified
  • 85% of flagged items are truly slow-moving
  • 88%+ discrimination between classes
```

#### Elasticity Model (Price Sensitivity)
```
Metric              Expected  Benchmark     Note
─────────────────────────────────────────────────
R² Score            0.75-0.85 Linear model (0.55-0.65)
MAPE (forecast)     12-15%    Manual estimates (25%+)
Elasticity Range    -0.6 to -2.0 Category-specific

Typical Values by Category:
  Electronics:  -1.8 to -2.0  (High sensitivity)
  Apparel:      -1.3 to -1.5  (Medium sensitivity)
  Groceries:    -0.6 to -0.8  (Low sensitivity)
```

#### Optimization Engine (Margin Prediction)
```
Metric              Expected  Benchmark         Note
─────────────────────────────────────────────────
Margin Impact       +2-5%     No optimization    vs. current
Clearance Speed     ↓55%      vs. current        Days to clear
Recommendation Fit  90%+      Manual decisions   Within constraints
```

---

### Integration Points

```
Inbound Connections (Data Consumers):
  ← OSA System          (inventory snapshots, features)
  ← POS System          (historical prices, volumes, transactions)
  ← ERP System          (costs, constraints, alerts)
  ← Promotional Calendar (upcoming events, conflicts)
  ← Competitor Pricing  (optional: market intelligence)

Outbound Connections (Data Producers):
  → POS Pricing Engine  (approved markdowns)
  → Dashboard/BI Tools  (performance metrics)
  → Notification System (alerts to approvers)
  → Feedback Loop       (actual vs predicted monitoring)
```

---

### Risk Assessment Matrix

```
Risk                              Probability  Impact  Mitigation           Risk Level
──────────────────────────────────────────────────────────────────────────────────
Model predicts wrong              Medium       Medium  Backtest, monitoring    YELLOW
Over-discount strategics          Medium       High    Constraints, review     YELLOW
Elasticity errors by location     Medium       Medium  Stratified models       YELLOW
Data quality issues               Low          Medium  Validation rules        GREEN
Adoption resistance               Medium       Medium  Change mgmt, training   YELLOW
System complexity                 Low          Medium  Documentation, support  GREEN
Competitor response               Low          Low     Monitor, adjust         GREEN
Brand dilution                    Low          High    Brand rules enforced    GREEN
```

---

### Deliverables Timeline

```
MONTH 1 (Weeks 1-4):
  ✓ Data audit complete
  ✓ Data pipeline operational
  ✓ Feature store created
  ✓ Team onboarded

MONTH 2 (Weeks 5-8):
  ✓ Lifecycle model trained
  ✓ Elasticity models built
  ✓ Optimization engine coded
  ✓ Unit testing complete

MONTH 3 (Weeks 9-12):
  ✓ Integration testing
  ✓ Performance benchmarks
  ✓ Backtesting results
  ✓ Pilot selection approved

MONTH 4 (Weeks 13-16):
  ✓ Pilot deployment
  ✓ Real-world validation
  ✓ Performance data collection
  ✓ Go/No-Go decision

MONTH 5-6 (Weeks 17-24):
  ✓ Full-scale deployment
  ✓ API integration complete
  ✓ Production monitoring live
  ✓ First monthly review

MONTH 7-12:
  ✓ Continuous optimization
  ✓ Quarterly reviews
  ✓ Model retraining
  ✓ Feature enhancements
```

---

### Team Composition & Responsibilities

```
Full-Time (6 months):
├─ Data Scientist (1.0 FTE)
│  Tasks: Model development, feature engineering, hyperparameter tuning
│
├─ Analytics Engineer (1.0 FTE)
│  Tasks: Data pipeline, feature store, optimization engine coding
│
├─ Pricing Strategist (0.5 FTE)
│  Tasks: Business rules, constraints, approval workflows
│
└─ Supply Chain Lead (0.5 FTE)
   Tasks: Inventory interpretation, operational validation

Part-Time:
├─ IT/Infrastructure (0.5 FTE)
│  Tasks: System integration, API management
│
├─ Finance (0.3 FTE)
│  Tasks: ROI tracking, margin validation
│
└─ Executive Sponsor (0.2 FTE)
   Tasks: Governance, sign-offs, escalations

Total Headcount: 3 FTE + support
```

---

### Key Decisions Required from Leadership

| Decision | Options | Recommendation | Timeline |
|----------|---------|-----------------|----------|
| **Brand Protection** | Strict | Implement margin floors & brand rules | Before Week 1 |
| **Geographic Variation** | Full by store | Start with region-level, refine | Week 2 |
| **Approval Process** | Automated/Manual % | 70% automated, 30% manual review | Week 3 |
| **Markdown Timeline** | Forward-looking window | 30 days (vs. 14 or 60) | Week 1 |
| **Elasticity Stratification** | Category/Store/Season | Category × Store × Season | Week 5 |
| **Rollout Approach** | Phased/Big-bang | Phased (pilot → rollout) | Week 15 |

---

### Common Questions & Answers

**Q: Won't customers notice price variations by location?**
A: Regional price variations are standard industry practice (e.g., Target, Walmart). Transparency + consistency builds trust.

**Q: What if the model misses a slow-moving item?**
A: 15% miss rate expected. OSA team still has alerts for inventory builds. System is enhancement, not replacement.

**Q: How do we prevent over-discounting?**
A: Hard constraints enforce: (1) Minimum margin floor, (2) Maximum discount cap, (3) Competitive floor.

**Q: What's the learning curve for pricing team?**
A: Low. Recommendations are straightforward: "Mark this down X% to $Y price." Existing workflows fit naturally.

**Q: Can we customize constraints per brand/category?**
A: Yes. Constraints are configurable by category, store type, season, etc. Built-in flexibility.

**Q: What happens if a recommendation doesn't work?**
A: System learns. Weekly retraining incorporates actual outcomes, adjusts elasticity/rules accordingly.

**Q: How does this integrate with promotions?**
A: System checks promotional calendar. Avoids conflicts. Can combine markdown + promotion if strategic.

**Q: What's the main risk?**
A: Model prediction errors or brand dilution. Mitigated by constraints, manual review gate, monitoring.

---

### Competitive Advantage Positioning

```
What Current Systems Do (Manual):
  ❌ React to excess inventory (too late)
  ❌ Use gut feel for pricing (inconsistent)
  ❌ One price for all locations (inefficient)
  ❌ Unclear margin impact (post-hoc analysis)

What This System Does (AI-Powered):
  ✅ Predict excess inventory 30 days early (proactive)
  ✅ Calculate optimal prices via elasticity models (data-driven)
  ✅ Location-specific pricing (efficient)
  ✅ Margin impact quantified upfront (transparent)
  ✅ 6-12x ROI within first year (proven)
```

---

### Success Stories Blueprint

```
Scenario A: Seasonal Overstocking
─────────────────────────────────
Before: $200K write-off on summer apparel
After:  Proactive 22% markdown, 85% clearance, +$50K margin
Insight: Predictive early action pays dividends

Scenario B: Competitive Pressure
─────────────────────────────────
Before: Reactive match, margin compression across channels
After:  Location-specific optimal markdown, margin protected
Insight: Data-driven beats reactive every time

Scenario C: Forecast Miss
─────────────────────────────────
Before: 200 units excess, tied up for months, eventual write-off
After:  Clearance in 28 days via optimal markdown, capital freed 3 weeks early
Insight: Working capital impact often exceeds margin savings
```

---

### Next Actions (Week 1)

- [ ] **Day 1:** Schedule executive kickoff (CFO, SVP Merchandising, Pricing Director)
- [ ] **Day 2:** Define success metrics & constraints
- [ ] **Day 3:** Identify data owners (POS, cost, promotions)
- [ ] **Day 4:** Secure executive sponsor commitment
- [ ] **Day 5:** Finalize team assignments & start calendar

---

**BOTTOM LINE:** AI-powered markdown optimization transforms inventory management from reactive problem-solving to proactive profit-maximization. 6-month implementation. $625K cost. $4-8M annual benefit. 6-12x ROI.

**Status:** Ready for decision & greenlight 🟢
