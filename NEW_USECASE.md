# NEW USE CASE: Dynamic Markdown Optimization & Inventory Clearance Prediction

## Executive Summary

Building upon the OSA (On-Shelf Availability) foundation that identifies stocking issues, this new use case focuses on **Dynamic Markdown Optimization with AI-Powered Inventory Clearance Prediction**. The system leverages real-time sales velocity, demand patterns, inventory age, shelf capacity constraints, and markdown elasticity to automatically recommend optimal pricing strategies that maximize margin realization while clearing slow-moving inventory before season-end or expiry.

### Business Problem

Retailers face significant challenges:
- **Dead Stock Accumulation**: Slow-moving SKUs tie up working capital (estimated 10-15% of retail inventory)
- **Markdown Timing Issues**: Reactive markdowns often occur too late, resulting in excessive discounting
- **Lost Margin Opportunity**: Manual markdown decisions lack data-driven elasticity analysis, leading to over-discounting of price-sensitive items
- **Multi-Location Complexity**: Optimal markdown pricing varies significantly by store location, customer demographics, and local competition
- **Supply Chain Lag**: Traditional approaches don't account for incoming inventory or promotional lifecycles

### Solution Overview

The new use case predicts which SKUs will become slow-moving or excess inventory within 14-30 days and recommends:
1. **Optimal markdown price points** using machine learning price elasticity models
2. **Timing of markdowns** based on inventory burn-down projections
3. **Location-specific strategies** considering local demand patterns
4. **Clearance event optimization** aligning markdown recommendations with promotions

---

## Data Requirements & Integration

### Primary Data Sources (from existing OSA system)
- **Inventory Data** (osa_raw_data.csv)
  - Daily sales units
  - On-hand inventory
  - Shelf capacity utilization
  - Replenishment patterns
  - Days since last sale

- **Lead Time Data** (vendor_leadtime_info.csv)
  - Replenishment lead times
  - Order pipeline visibility

### New Data Requirements

| Data Element | Source | Purpose |
|---|---|---|
| **Historical Markdown Records** | POS/ERP System | Price elasticity calibration |
| **Promotional Calendar** | Marketing/Merchandising | Alignment with promotion timing |
| **Competitor Pricing** | Market Intelligence Tools | Competitive positioning baseline |
| **Product Attributes** | Master Data | Category-specific elasticity profiles |
| **Customer Demographics** | Store/Region Data | Location-specific demand patterns |
| **Product Cost/Margin** | Finance/Planning | Margin floor constraints |
| **Store Traffic Patterns** | Foot Traffic Analytics | Demand seasonality indicators |
| **Weather Data** | External APIs | Seasonal demand drivers |

---

## Machine Learning Models & Algorithms

### 1. **Inventory Age & Lifecycle Prediction Model**
**Algorithm**: Time Series Analysis + XGBoost Classification

**Objective**: Predict which SKUs will enter "clearance-worthy" status in next 14-30 days

**Features**:
- Days since last replenishment
- Sales velocity (7-day, 14-day, 30-day moving averages)
- Seasonality index
- Promotional history
- Shelf capacity utilization ratio
- Inventory pipeline vs. current sales rate ratio

**Output**: 
- Probability score (0-1) of becoming slow-moving
- Predicted days until critical stock level
- Clearance urgency flag (High/Medium/Low)

---

### 2. **Price Elasticity & Demand Curve Estimation**
**Algorithm**: Gradient Boosting (LightGBM) + Mixed Effects Regression

**Objective**: Estimate price-demand relationship at product category + location level

**Features**:
- Historical transaction data (price, quantity, date)
- Product attributes (size, brand, category)
- Competitive pricing
- Promotional intensity
- Store demographics
- Seasonality indicators

**Output**:
- Elasticity coefficient (e.g., -1.5 means 1% price reduction → 1.5% demand increase)
- Price-demand curve coefficients
- Confidence intervals
- Segment-specific elasticity (by store location, customer type)

---

### 3. **Markdown Recommendation Engine**
**Algorithm**: Constrained Optimization + Linear Programming

**Objective**: Calculate optimal markdown price points maximizing margin realization

**Constraints**:
- Minimum margin floor (e.g., don't go below 10% margin)
- Maximum discount cap (e.g., don't exceed 40% off)
- Competitive price floor (can't undersell major competitors by >15%)
- Clearance urgency (must clear X% of inventory within Y days)
- Inventory pipeline (don't over-discount if new stock arriving)

**Decision Variables**:
- Target markdown discount %
- Timing (when to initiate markdown)
- Duration (how long to maintain price)
- Geographic applicability (which stores get which price)

**Optimization Objective**: Maximize total margin dollars = Σ(Unit Sales × New Unit Margin)

**Output**:
- Recommended discount % by SKU × Store
- Predicted sales lift at recommended price
- Expected margin realization (vs. if no markdown)
- Suggested promotional messaging

---

### 4. **Inventory Burn-Down Simulation**
**Algorithm**: Monte Carlo Simulation + Demand Forecasting

**Objective**: Project inventory levels under different markdown scenarios

**Simulation Components**:
- Base demand forecast (from existing OSA demand sensing)
- Markdown elasticity impact (uplift multiplier)
- Promotional calendar alignment
- Competitive response scenarios
- Supply chain uncertainty (lead time variability)

**Output**:
- Probability distribution of inventory at key dates
- Expected clearance date at each discount level
- Risk of stock-out vs. excess inventory
- Recommended safety stock adjustments

---

## Use Case Workflow

### Phase 1: Data Ingestion & Preparation
```
1. Pull daily inventory snapshots from osa_raw_data
2. Calculate KPIs:
   - Daily sales velocity
   - Inventory age (days on shelf)
   - Shelf capacity utilization %
   - Days-to-depletion (at current sales rate)
   - Inventory pipeline ratio
3. Enrich with promotional calendar and competitor pricing
4. Calculate product cost basis and current margin
```

### Phase 2: Slow-Moving Inventory Detection
```
1. Run Inventory Lifecycle Prediction Model
2. Identify SKUs with high clearance urgency in next 30 days
3. Segment by:
   - Seasonal (temporary low sales expected)
   - Structural (persistent demand problem)
   - Promotional (tied to ended promotion)
   - Overstocking (arrived too much inventory)
4. Flag for markdown consideration (exclude items with known demand spike, upcoming promotions)
```

### Phase 3: Price Elasticity Calibration
```
1. Extract historical markdown data (last 12-24 months)
2. Build category-location specific elasticity models
3. Validate with holdout test set
4. Calculate confidence intervals and sensitivity ranges
5. Store elasticity coefficients for each segment
```

### Phase 4: Markdown Optimization
```
For each flagged SKU:
1. Determine clearance objective (timeline, volume, margin floor)
2. Run constrained optimization:
   - Input: Current price, cost, elasticity, constraints
   - Solve: Maximum margin equation
   - Output: Optimal markdown price
3. Simulate inventory burn-down at recommended price
4. Generate recommendation with:
   - Discount %, confidence level
   - Expected sales uplift
   - Margin realization comparison (with/without markdown)
   - Suggested promotional message
```

### Phase 5: Geographic & Temporal Optimization
```
1. Calculate location-specific elasticity variations
2. Recommend different prices by store cluster
3. Determine optimal markdown timing (day of week, season)
4. Align with promotional calendar
5. Account for competitive calendar events
```

### Phase 6: Execution & Monitoring
```
1. Generate markdown recommendation feed for retailers
2. Push approved markdowns to POS systems
3. Monitor actual vs. predicted sales uplift
4. Track margin realization
5. Adjust elasticity models based on actual performance
6. Alert on anomalies (e.g., demand spike when expecting clearance)
```

---

## Expected Business Impact

| Metric | Current State | Projected (with AI) | Upside |
|---|---|---|---|
| **Dead Stock Reduction** | 12-15% of inventory | 6-8% | 40-50% ↓ |
| **Markdown Timing** | Reactive (too late) | Proactive (30-day lead) | 25-30% better sell-through |
| **Margin Realization** | Sub-optimal discounting | +3-5% via optimal pricing | $2-4M annual (for $100M retailer) |
| **Forecast Accuracy** | 65-70% for sales after markdown | 85-90% | +20-25 pts |
| **Inventory Turns** | 6-8x annually | 9-11x annually | 15-20% ↑ |
| **Clearance Effectiveness** | 70-75% of target | 90-95% of target | +15-25 pts |

---

## Technical Architecture

### Data Pipeline
```
osa_raw_data.csv → Data Prep Layer → Feature Engineering
                          ↓
                    Spark/Pandas Processing
                          ↓
vendor_leadtime.csv ← Time Series Aggregation ← Historical Markdown Data
                          ↓
                    Feature Store
                          ↓
ML Models (Phase 1-4) ← Elasticity Calibration, Inventory Prediction
                          ↓
Optimization Engine → Recommendation Generation
                          ↓
POS/ERP Integration → Execution & Monitoring
```

### Technology Stack
- **Data Processing**: Spark (for large-scale aggregations)
- **ML Modeling**: 
  - XGBoost/LightGBM (inventory prediction, elasticity)
  - scikit-learn (demand forecasting)
  - PyMC3 (Bayesian elasticity estimation)
- **Optimization**: PuLP or Gurobi (constrained optimization)
- **Simulation**: SimPy (Monte Carlo)
- **Deployment**: Databricks + REST APIs for real-time recommendations

---

## Implementation Roadmap

### Phase 1 (Weeks 1-4): Foundation
- Data integration from existing OSA system
- Historical markdown dataset assembly
- Baseline elasticity model training

### Phase 2 (Weeks 5-8): Core Models
- Inventory lifecycle prediction
- Price elasticity estimation by segment
- Markdown timing optimization

### Phase 3 (Weeks 9-12): Optimization Engine
- Constrained optimization solver
- Inventory burn-down simulation
- Geographic price differentiation

### Phase 4 (Weeks 13-16): Deployment & Monitoring
- Integration with POS/ERP systems
- Real-time recommendation API
- Performance tracking and model retraining

---

## Competitive Advantages

1. **Proactive vs. Reactive**: 30-day forward-looking vs. reactive markdown timing
2. **Data-Driven Elasticity**: Machine learning–based elasticity vs. static assumptions
3. **Multi-Dimensional Optimization**: Considers margin, clearance timing, competitive positioning simultaneously
4. **Geographic Customization**: Location-specific pricing vs. one-size-fits-all
5. **Real-Time Adaptation**: Continuous model updates vs. quarterly static markdown plans
6. **Integrated Framework**: Leverages OSA data for seamless inventory-to-pricing workflow

---

## Success Metrics & KPIs

### Financial KPIs
- Gross margin $ from clearance sales
- Reduction in deadstock write-offs
- Inventory carrying cost savings
- ROI on markdown vs. cost of goods sold

### Operational KPIs
- Percentage of slow-moving SKUs correctly identified (recall)
- Percentage of clearance recommendations approved by merchants
- Actual vs. predicted sales uplift accuracy
- Time-to-clearance vs. targets

### Quality KPIs
- Forecast accuracy (MAPE) for markdown impact
- Model elasticity calibration R² score
- Margin realization (actual vs. recommended)

---

## Risk Mitigation

| Risk | Mitigation |
|---|---|
| Over-discounting strategic SKUs | Whitelist/blacklist capability; manual approval gates |
| Competitor retaliation | Monitor competitive pricing; adjust elasticity in real-time |
| Demand spike during markdown period | Early warning system from OSA demand sensing module |
| Data quality issues | Validation rules; outlier detection; human review |
| Model staleness | Continuous retraining; performance monitoring triggers |
| Markdown fatigue | Frequency caps; brand protection rules |

---

## Conclusion

This **Dynamic Markdown Optimization** use case transforms the OSA system from inventory diagnostics into an actionable pricing engine. By predicting slow-moving inventory 30 days in advance and recommending data-driven, location-specific markdown strategies, retailers can significantly improve margin realization while reducing dead stock. The integration with existing OSA data, demand signals, and supply chain visibility creates a cohesive ecosystem for inventory and pricing optimization.
