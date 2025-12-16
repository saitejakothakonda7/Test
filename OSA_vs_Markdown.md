# COMPARISON: OSA vs NEW MARKDOWN OPTIMIZATION USE CASE

## Overview Comparison

| Aspect | OSA (Current) | Markdown Optimization (NEW) |
|--------|---------------|----------------------------|
| **Focus** | Identifying stocking problems | Optimizing pricing & inventory clearance |
| **Problem** | What inventory issues exist? | How to clear slow inventory profitably? |
| **Time Horizon** | Daily/Weekly monitoring | 30-day forward looking |
| **Output** | Alerts & flags | Pricing recommendations |
| **Action** | Operational fixes (replenishment, merchandising) | Strategic pricing decisions |
| **Business Impact** | Prevent stockouts & oversell | Maximize margin realization |

---

## Data Flow Comparison

### Current OSA Use Case

```
Raw Inventory Data
        ↓
Data Preparation
  • Fill missing dates
  • Impute forward fill
  • Identify events
        ↓
Phantom Inventory Detection
  (Identify tracking discrepancies)
        ↓
Out-of-Stock Analysis
  (Safety stock calculations)
  (Lead time risk analysis)
        ↓
On-Shelf Availability Issues
  (Flagged problems)
        ↓
ALERT: Out-of-stock risk detected
ACTION: Replenish immediately, fix merchandising
```

### NEW Markdown Optimization Use Case

```
Raw Inventory Data + Vendor Lead Times
        ↓
Time Series Feature Engineering
  • Sales velocity (7d, 30d MA)
  • Inventory age
  • Shelf utilization
  • Days-to-deplete
  • Sales momentum
  • Zero-sales streak
        ↓
Slow-Moving Inventory Prediction
  (XGBoost classifier - 30 day lookahead)
        ↓
Price Elasticity Calibration
  (Historical markdown data analysis)
  (Category × Location regression)
        ↓
Markdown Optimization
  (Constrained optimization solver)
  (Max margin dollars objective)
        ↓
Clearance Recommendation
  • Optimal price point
  • Timing
  • Location-specific variant
        ↓
RECOMMENDATION: Markdown to $X by Y date
ACTION: Update pricing, align with promotions
```

---

## Technical Comparison

### Models & Algorithms

| Aspect | OSA | Markdown Optimization |
|--------|-----|----------------------|
| **Inventory Prediction** | Time window analysis | Gradient Boosting Classifier (XGBoost) |
| **Out-of-Stock Detection** | Threshold-based rules | N/A (focus on clearance) |
| **Phantom Inventory** | Accounting reconciliation | Not applicable |
| **Pricing Optimization** | None | Constrained Linear Programming |
| **Elasticity Modeling** | None | Mixed Effects Regression / LightGBM |
| **Forecasting** | Historical averages | ML-based demand curves |

### Key Differences in Features

**OSA Features:**
- Daily sales units
- On-hand inventory vs. target
- Replenishment pipeline status
- Safety stock thresholds
- Lead times

**Markdown Optimization Features:**
- Sales velocity trends (7d, 30d MA)
- Sales momentum (acceleration/deceleration)
- Shelf utilization ratio
- Days to deplete inventory
- Zero-sales streaks
- Inventory age
- Pipeline-to-sales ratio

---

## Problem Statement Alignment

### Current OSA Problems Solved

1. **Out-of-Stock Prevention**
   - "When will this SKU run out?"
   - "Is inventory sufficient to meet demand?"

2. **On-Shelf Availability**
   - "Is the product accessible to customers?"
   - "Is there phantom inventory?"

3. **Operational Issues**
   - "What inventory events need attention?"
   - "Is replenishment sufficient?"

### NEW Markdown Problems Solved

1. **Slow-Moving Inventory Clearance**
   - "Which SKUs will become slow-moving in next 30 days?"
   - "When should we reduce price?"

2. **Margin Optimization**
   - "What discount % maximizes profit while clearing inventory?"
   - "How does elasticity vary by store location?"

3. **Strategic Pricing**
   - "What's the optimal price to meet clearance targets?"
   - "How should timing align with promotions?"

4. **Dead Stock Reduction**
   - "Avoid write-offs by proactive markdowns"
   - "Minimize carrying cost on excess inventory"

---

## Business Value Comparison

### OSA Value Proposition

| Benefit | Value |
|---------|-------|
| **Reduced Stockouts** | $2-5M annually (prevent lost sales) |
| **Improved COGS** | 3-5% reduction via better replenishment |
| **Customer Satisfaction** | +15-20% product availability |
| **Operational Efficiency** | 20% reduction in manual inventory checks |

**Total Annual Impact:** $3-8M for $100M retailer

### Markdown Optimization Value Proposition

| Benefit | Value |
|---------|-------|
| **Margin Improvement** | +3-5% via data-driven discounting |
| **Dead Stock Reduction** | 40-50% fewer write-offs |
| **Inventory Turns** | +15-20% improvement |
| **Working Capital** | $5-10M released from inventory |

**Total Annual Impact:** $5-12M for $100M retailer

---

## Complementary Integration

### How They Work Together

```
OSA identifies:
"Store A, SKU 123 has 80 units on-hand 
but safety stock is 50 units"

Markdown Optimization builds on this:
"That extra 30 units are at risk of becoming slow-moving
Recommend 20% markdown to accelerate sales"

Result:
1. Prevent future out-of-stock via better pricing
2. Reduce dead inventory carrying cost
3. Optimize margin on excess units
```

### Data Flow Integration

```
                    Inventory Raw Data
                          ↓
                   ┌──────┴──────┐
                   ↓              ↓
              OSA Module    Markdown Module
                   ↓              ↓
            Stock-Out Alerts  Clearance Flags
                   ↓              ↓
           Replenishment       Pricing
           Decisions           Decisions
                   ↓              ↓
              Combined Action Plan
```

---

## Implementation Roadmap Comparison

### OSA Implementation (Past)

```
Weeks 1-4:    Data preparation, fill gaps, create calculated fields
Weeks 5-8:    Phantom inventory detection rules
Weeks 9-12:   Out-of-stock calculation engine
Weeks 13-16:  Alert generation and dashboard
Result:       Daily alerts for inventory problems
```

### Markdown Optimization Implementation (Planned)

```
Weeks 1-4:    Feature engineering from OSA data
Weeks 5-8:    Inventory lifecycle model training
Weeks 9-12:   Price elasticity calibration, optimization engine
Weeks 13-16:  Recommendation API, POS integration, monitoring
Result:       Weekly markdown recommendations for slow-moving SKUs
```

### Integration Timeline

```
Months 1-2:   Maintain separate systems (parallel operation)
Months 3-4:   Integrate data pipelines (shared feature store)
Months 5-6:   Combined analytics dashboard (OSA + Pricing)
Months 7-12:  Advanced use cases (promotional pricing, dynamic bundles)
```

---

## Success Metrics Comparison

### OSA Metrics

```
Stock Availability:
  • On-shelf availability rate: 93% → 96%
  • Stockout frequency: -25%
  • Fill rate: 94% → 98%

Operational:
  • Phantom inventory detection accuracy: 85%
  • Alert false positive rate: <10%
  • Replenishment lead time: -15%

Financial:
  • Lost sales recovery: +$2-3M
  • Safety stock optimization: -10%
```

### Markdown Optimization Metrics

```
Sales & Inventory:
  • Inventory turns: 8x → 10x
  • Dead stock rate: 12% → 6%
  • Days-to-clearance: 45d → 20d

Margin:
  • Gross margin % (clearance items): +2-3%
  • Avoided write-offs: $1-2M
  • Margin dollars from markdown: +$2-4M

Forecast Accuracy:
  • Slow-moving prediction recall: >90%
  • Sales uplift prediction MAPE: <15%
  • Elasticity model R²: >0.80
```

---

## Technology Stack Comparison

### OSA Stack

```
Data Processing:  Spark, SQL, Pandas
Algorithms:       Threshold-based rules, Window functions
Modeling:         Statistical calculations
Dashboard:        Databricks Notebooks, SQL Views
Alert Engine:     Rules-based triggers
```

### Markdown Optimization Stack

```
Data Processing:  Spark, Pandas, NumPy
Feature Engineering: sklearn, custom transformers
ML Models:        XGBoost, LightGBM, scipy.optimize
Optimization:     Linear Programming (PuLP/Gurobi)
Simulation:       Monte Carlo (SimPy, numpy random)
Deployment:       REST API, Databricks Jobs
Monitoring:       MLflow, custom trackers
```

---

## Organizational Impact

### OSA Skills Required

- Inventory managers
- Supply chain analysts
- SQL/Data engineering
- Merchandisers

### Markdown Optimization Skills Required

- Data scientists
- ML engineers
- Operations researchers
- Pricing analysts
- Supply chain strategists

**New roles needed:** ML model owner, pricing optimization specialist

---

## Risk & Mitigation Comparison

### OSA Risks

| Risk | Mitigation |
|------|-----------|
| Wrong alerts (false positives) | Threshold tuning, manual review |
| Replenishment over-correction | Safety stock buffers |
| Operational disruption | Phased rollout |

### Markdown Optimization Risks

| Risk | Mitigation |
|------|-----------|
| Over-discounting | Margin floor constraints, whitelist |
| Brand damage | Competitor price monitoring, brand protections |
| Demand shock | Real-time alerts, pause mechanism |
| Model staleness | Weekly retraining, performance monitoring |
| Cannibalization | Region-specific pricing strategies |

---

## Roadmap: Beyond Single Use Cases

### Future Integrated Scenarios (Years 2-3)

1. **Integrated Inventory Lifecycle Management**
   ```
   Demand Sensing (predict demand)
        ↓ ↓ ↓
   OSA (ensure availability) + Markdown (optimize clearance)
        ↓ ↓
   Unified Inventory Strategy
   ```

2. **Dynamic Promotional Planning**
   - Combine OSA alerts with markdown recommendations
   - Auto-trigger clearance events when inventory exceeds thresholds
   - Coordinate with marketing calendar

3. **Real-Time Pricing Intelligence**
   - Continuous elasticity updates
   - Competitive pricing monitoring
   - Dynamic clearance pricing

4. **Multi-SKU Bundle Optimization**
   - Pair slow-moving items with fast-movers
   - Optimize bundle pricing
   - Protect core brands

5. **Fulfillment Optimization**
   - Allocate slow-moving inventory across channels
   - Optimize store-to-store transfers
   - Cross-location clearance strategies

---

## Conclusion

| Dimension | Relationship |
|-----------|--------------|
| **Sequencing** | OSA is prerequisites; Markdown optimization layer on top |
| **Data Dependency** | Markdown leverages OSA-prepared features (inventory data) |
| **Time Horizon** | OSA: Daily; Markdown: 30-day forward |
| **Decision Type** | OSA: Tactical (fix problems); Markdown: Strategic (optimize value) |
| **Business Value** | Both ~$5-8M annually; combined $10-15M potential |
| **Implementation** | Start with OSA; layer Markdown after 6 months |

**Key Insight:** OSA solves the inventory **availability** problem. Markdown Optimization solves the inventory **profitability** problem. Together, they create a complete inventory-to-pricing value chain.
