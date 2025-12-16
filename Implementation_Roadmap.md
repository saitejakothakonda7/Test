# IMPLEMENTATION ROADMAP: Dynamic Markdown Optimization Use Case

## Quick Reference: What This Use Case Does

✅ **Predicts** which SKUs will become slow-moving 30 days in advance
✅ **Recommends** optimal markdown prices using machine learning
✅ **Optimizes** for margin dollars while clearing inventory
✅ **Personalizes** pricing by store location and customer demographics
✅ **Integrates** with existing OSA data and inventory management

---

## Phase 1: Preparation (Weeks 1-2)

### Data Audit & Collection

**Inventory Data** (✓ Already have)
- osa_raw_data.csv - Daily inventory snapshots
- vendor_leadtime_info.csv - Replenishment lead times

**Data to Acquire**
- [ ] Historical markdown records (past 12-24 months)
  - Date of markdown, SKU, store, original price, markdown price, units sold
  - Source: POS system, pricing system, or sales data warehouse
- [ ] Product master data
  - Cost/acquisition price for each SKU
  - Product category, subcategory
  - Brand, supplier information
- [ ] Store master data
  - Store location, region, customer demographic profile
  - Store format (supermarket, discounter, etc.)
  - Store performance tier
- [ ] Promotional calendar
  - Planned promotional events (dates, offers, participating stores)
  - Historical promotional performance
- [ ] Competitor pricing (optional but valuable)
  - Competitor prices for similar SKUs
  - Frequency: Daily or weekly

### Stakeholder Alignment

**Executive Sponsorship**
- [ ] CFO/VP Finance: Cost savings, margin impact, ROI expectations
- [ ] SVP Merchandising: Pricing strategy, brand protection, competitive positioning
- [ ] CRO: Revenue impact, customer perception
- [ ] SVP Supply Chain: Inventory allocation, replenishment synchronization

**Working Group**
- [ ] Pricing Manager/Director - Lead user, strategy
- [ ] Data Scientist - ML model development
- [ ] Supply Chain Analyst - Inventory interpretation
- [ ] Finance/Planning - Margin validation
- [ ] IT/Infrastructure - System integration

**Success Criteria Definition**
- What does success look like? (e.g., -50% dead stock, +3% margin on clearance)
- What are acceptable risks? (e.g., brand dilution, margin floor)
- What's the timeline for ROI? (e.g., 12 months)

---

## Phase 2: Foundation Setup (Weeks 3-6)

### Technical Infrastructure

**Data Pipeline Setup**
```
1. Create data lake staging area for historical markdown records
   Location: /data/markdown_optimization/
   
2. Set up ETL jobs (daily/weekly)
   - Pull from POS: Sales transactions, prices, quantities
   - Pull from Inventory: OSA prepared data (osa.inventory table)
   - Pull from Promotions: Promotional calendar
   - Create unified daily snapshot table
   
3. Build feature store
   Table: markdown_features
   Grain: store_id, sku, date
   Fields: All features from MarkdownDataPreparation class
   Refresh: Daily
```

**Development Environment**
```
Databricks Workspace:
  /Workspace/markdown_optimization/
    ├── notebooks/
    │   ├── 01_data_exploration.py
    │   ├── 02_feature_engineering.py
    │   ├── 03_model_training.py
    │   ├── 04_optimization_engine.py
    │   └── 05_recommendations_generation.py
    ├── data/
    │   ├── raw/
    │   ├── processed/
    │   └── features/
    └── models/
        ├── lifecycle_predictor/
        ├── elasticity_models/
        └── optimization_engine/
```

### Data Preparation & Validation

**Historical Markdown Analysis**
```python
# Questions to answer:
1. How many SKU-store-date combinations have markdown data?
2. What's the distribution of discount percentages?
3. What's the average sales uplift post-markdown?
4. How does elasticity vary by category?
5. Are there seasonal patterns in markdowns?
6. What's the typical markdown duration?
```

**Data Quality Checks**
- [ ] No missing values in cost/price fields
- [ ] Prices are within reasonable ranges (>0, <$1000)
- [ ] Quantities are non-negative integers
- [ ] Dates are valid and chronological
- [ ] Store-SKU combinations have adequate history (min 20 records)

---

## Phase 3: Model Development (Weeks 7-14)

### Step 1: Feature Engineering (Weeks 7-8)

**Execute:** `MarkdownDataPreparation.create_time_series_features()`

```python
# Key features to generate:
- sales_7day_ma           # Short-term sales trend
- sales_30day_ma          # Long-term baseline
- sales_momentum           # Acceleration/deceleration
- days_since_replenishment # Age of inventory
- shelf_utilization_ratio  # Capacity vs. actual
- days_to_deplete         # Projected depletion date
- pipeline_ratio          # Incoming vs. current
- zero_sales_streak       # Consecutive non-sales days
- replenishment_flag      # Recent restocking
- units_under_promotion   # Current promotional activity

# Validation:
- Distribution checks (mean, std, min, max)
- Correlation analysis with sales
- Missing value handling
```

### Step 2: Inventory Lifecycle Prediction Model (Weeks 8-10)

**Objective:** Predict which SKUs will become slow-moving in 30 days

**Training Data Preparation**
```python
# Create training dataset
1. Label data: For each date, calculate sales in following 30 days
2. Define "slow-moving" = bottom 25th percentile of sales velocity
3. Create binary target: 1 if slow-moving, 0 if normal
4. Handle class imbalance (typically 20-30% slow-moving)

# Feature selection
Use features from Phase 1 + lag features (1d, 7d, 14d sales)

# Split data
Train: 70% (historical period)
Validation: 15% (recent past)
Test: 15% (most recent period)
```

**Model Training**
```python
from sklearn.ensemble import GradientBoostingClassifier

model = GradientBoostingClassifier(
    n_estimators=100,
    learning_rate=0.1,
    max_depth=5,
    min_samples_split=10,
    min_samples_leaf=5,
    random_state=42
)

# Train
model.fit(X_train, y_train)

# Evaluate
print(f"Train Accuracy: {model.score(X_train, y_train):.3f}")
print(f"Valid Accuracy: {model.score(X_valid, y_valid):.3f}")
print(f"Test Accuracy: {model.score(X_test, y_test):.3f}")

# Cross-validation metrics
from sklearn.metrics import roc_auc_score, precision_recall_curve
auc = roc_auc_score(y_test, model.predict_proba(X_test)[:, 1])
print(f"ROC-AUC: {auc:.3f}")
```

**Model Interpretation**
```python
# Feature importance
importances = pd.DataFrame({
    'feature': X_train.columns,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)

print(importances)
# Expected: sales_momentum, days_to_deplete, shelf_utilization highest
```

### Step 3: Price Elasticity Estimation (Weeks 9-11)

**Data Preparation**
```python
# Historical markdown dataset structure:
date, store_id, sku, category, current_price, new_price, 
current_quantity, new_quantity

# Calculate price elasticity
elasticity = (% change in quantity) / (% change in price)
         = ln(Q_new/Q_old) / ln(P_new/P_old)
         = (ln(Q_new) - ln(Q_old)) / (ln(P_new) - ln(P_old))

# Group by category + store + season
# Fit regression model for each group
```

**Elasticity Model Development**
```python
import statsmodels.formula.api as smf

# Build category-location specific models
elasticity_models = {}

for category in categories:
    for store in stores:
        cat_store_data = data[
            (data['category'] == category) & 
            (data['store_id'] == store)
        ]
        
        if len(cat_store_data) >= 15:  # Minimum observations
            # Fit log-log regression
            model = smf.ols(
                'log(quantity) ~ log(price) + seasonality + promotional',
                data=cat_store_data
            ).fit()
            
            elasticity_models[f"{category}_{store}"] = {
                'slope': model.params['log(price)'],
                'r_squared': model.rsquared,
                'n_obs': len(cat_store_data)
            }
```

**Elasticity Validation**
```python
# Expected findings:
✓ Most elasticities should be negative (-0.5 to -2.5)
✓ Luxury/discretionary items: higher elasticity (>-1.5)
✓ Staple/essentials: lower elasticity (<-0.8)
✓ Vary significantly by store location
✓ Higher elasticity during off-season

# Create default elasticity by category (in case individual estimate lacking)
category_defaults = {
    'Electronics': -1.8,
    'Apparel': -1.5,
    'Home': -1.2,
    'Groceries': -0.6
}
```

### Step 4: Markdown Optimization Engine (Weeks 12-14)

**Optimization Problem Definition**
```
Maximize: Total Margin $ = Σ (Units_Sold × (New_Price - Cost))

Subject to:
1. Minimum margin floor: (New_Price - Cost) / New_Price >= min_margin_pct (e.g., 15%)
2. Maximum discount cap: (Current_Price - New_Price) / Current_Price <= max_discount_pct (e.g., 35%)
3. Competitor price floor: New_Price >= competitor_price * (1 - competitor_margin_cap) (e.g., -15%)

Decision variable: discount_percentage ∈ [0, max_discount_pct]

Demand model: New_Units = Current_Units × (1 + elasticity × price_change_pct)^(1/elasticity)
```

**Implementation**
```python
from scipy.optimize import minimize
import numpy as np

class MarkdownOptimizer:
    
    def calculate_optimal_markdown(self, sku_dict, constraints):
        """
        sku_dict: {
            'current_price': float,
            'cost': float,
            'current_units': float,
            'elasticity': float
        }
        
        constraints: {
            'min_margin_pct': 0.15,
            'max_discount_pct': 0.35,
            'competitor_price_floor': float or None
        }
        """
        
        def objective(discount_pct):
            new_price = current_price * (1 - discount_pct)
            units_uplift = (1 + elasticity * discount_pct / (1 - discount_pct)) ^ (1 / elasticity)
            new_units = current_units * units_uplift
            margin_dollars = new_units * (new_price - cost)
            return -margin_dollars  # Negative for minimization
        
        # Define constraints
        constraints_list = []
        
        # Margin floor
        constraints_list.append({
            'type': 'ineq',
            'fun': lambda x: ((current_price * (1-x[0]) - cost) / 
                             (current_price * (1-x[0]))) - min_margin_pct
        })
        
        # Competitor floor
        if competitor_price_floor:
            constraints_list.append({
                'type': 'ineq',
                'fun': lambda x: (current_price * (1-x[0])) - competitor_price_floor
            })
        
        # Optimize
        x0 = np.array([0.15])  # Initial guess: 15% discount
        bounds = [(0, max_discount_pct)]
        
        result = minimize(
            objective,
            x0,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints_list
        )
        
        return {
            'optimal_discount_pct': result.x[0],
            'optimal_price': current_price * (1 - result.x[0]),
            'predicted_units': current_units * units_uplift,
            'predicted_margin': result.fun  # Note: negated
        }
```

---

## Phase 4: Validation & Pilot (Weeks 15-20)

### Validation Approach

**Backtest Period:** 8 weeks

```
Methodology:
1. Select historical period (8 weeks ago)
2. Generate markdown recommendations as if running system then
3. Compare recommended vs. actual markdown decisions made
4. Calculate counterfactual margin: what would margin be if recommendation followed?
5. Measure: Recommendation accuracy, margin uplift potential
```

**Pilot Deployment**

```
Test Group: 5 stores × 50 SKUs (250 test records)
Control Group: 5 similar stores × same SKUs (250 control records)

Duration: 8 weeks

Metrics:
- Clearance time: Test vs. Control
- Final sell-through %: Test vs. Control  
- Margin realization: Test vs. Control
- Customer satisfaction (if available)
```

### Monitoring Dashboard

**Real-Time Metrics**
```
1. Inventory Lifecycle Model
   - Accuracy of slow-moving predictions (comparing vs. actuals)
   - Recall: % of true slow-movers caught
   - Precision: % of flagged items actually slow

2. Optimization Engine
   - Actual vs. predicted sales uplift
   - Actual vs. predicted margin dollars
   - Discount recommendations adherence

3. Business Results
   - Average time to clearance
   - Clearance effectiveness (% of target)
   - Dead stock %, write-offs
   - Inventory turns
   - Gross margin %
```

---

## Phase 5: Full Deployment (Weeks 21-24)

### System Architecture

**Real-Time Recommendation Generation**
```
Daily Job (11 PM):
  1. Pull latest inventory snapshot (from osa.inventory table)
  2. Calculate features (MarkdownDataPreparation)
  3. Run lifecycle prediction model → get clearance probability
  4. Filter candidates (probability > 0.60)
  5. Run optimization engine for each candidate
  6. Generate recommendation feed
  → Store in markdown_recommendations table

Weekly Update (Monday 6 AM):
  1. Retrain elasticity models (if sufficient new data)
  2. Retrain lifecycle prediction model (weekly)
  3. Update competitor pricing (if available)
  4. Adjust constraints based on business calendar
```

**Integration Points**

```
1. → POS System: Push approved recommendations to pricing engine
2. → ERP System: Validate against cost/margin data
3. → Promotional Calendar: Coordinate timing with campaigns
4. → Demand Sensing: Flag conflicting signals
5. ← Feedback Loop: Capture actual markdown performance
```

### Recommendation Types

**Automated** (70% of recommendations)
```
Criteria:
- Clearance probability > 0.70
- Margin floor met with recommended price
- No conflicting promotion
- No recent markdown in past 14 days

Action: Auto-push to POS (pending final review)
```

**Manual Review Required** (30% of recommendations)
```
Criteria:
- Clearance probability 0.55-0.70
- Margin floor violations
- Strategic/brand-sensitive SKUs
- Overlapping with promotions
- Multiple stores simultaneously

Action: Route to pricing team for approval
```

---

## Phase 6: Optimization & Scaling (Months 6+)

### Model Continuous Improvement

**Monthly Review**
- [ ] Refit elasticity models
- [ ] Retrain lifecycle prediction (weekly actually)
- [ ] Analyze recommendation adherence rates
- [ ] Collect feedback from pricing team

**Quarterly Deep Dives**
- [ ] Analyze failed recommendations (why wasn't discount sufficient?)
- [ ] Identify systematic biases (e.g., over-predicting in certain categories)
- [ ] Benchmark elasticity against industry standards
- [ ] Competitive pricing landscape review

### Feature Enhancements

**Quarter 2:**
- [ ] Add promotional elasticity (how does discount lift differ during promo periods?)
- [ ] Implement geographic price differentiation
- [ ] Add complementary/substitution effects

**Quarter 3:**
- [ ] Multi-SKU bundle optimization
- [ ] Cross-store inventory rebalancing recommendations
- [ ] Dynamic timing optimization (optimal day/hour to activate markdown)

**Quarter 4:**
- [ ] Predictive markdown reversal (when to remove discount)
- [ ] End-of-season liquidation optimization
- [ ] Integration with inventory allocation system

---

## Success Metrics Summary

### Financial KPIs (Quarterly)

| Metric | Current | Target (12 months) | Target (24 months) |
|--------|---------|-------------------|-------------------|
| **Dead Stock %** | 12% | 8% | 5% |
| **Markdown as % of Sales** | 8% | 9.5% | 9% |
| **Margin % on Marked-Down Items** | 18% | 21% | 23% |
| **Inventory Turns** | 8x | 9.5x | 11x |
| **Write-offs & Obsolescence** | 2% of COGS | 1.2% | 0.8% |
| **Total Margin $ Uplift** | Baseline | +$3-5M | +$5-8M |

### Operational KPIs (Weekly)

| Metric | Target |
|--------|--------|
| Recommendation accuracy (actual uplift vs. predicted) | >85% |
| Slow-moving inventory detection recall | >90% |
| Recommendation adherence rate (approved/total) | >70% |
| Time-to-clearance vs. targets | 95% compliance |

---

## Risk Mitigation Plan

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| Over-aggressive markdowns hurt brand | Medium | High | Brand protection rules, executive review, competitor monitoring |
| Customer backlash on price variations | Medium | Medium | Transparent pricing, regional/store-level strategies |
| System complexity causes adoption resistance | Medium | High | Change management, clear ROI communication, user training |
| Data quality issues | Low | Medium | Validation rules, monitoring dashboards, data audit |
| Model degradation over time | High | Medium | Weekly retraining, performance tracking, automated alerts |

---

## Resource Requirements

### Team Composition

```
Full-Time:
- 1 Data Scientist (model development, monitoring)
- 1 Analytics Engineer (data pipeline, feature store)
- 0.5 Pricing Manager (strategy, business rules)
- 0.5 Supply Chain Analyst (inventory context)

Part-Time:
- 1 IT/Infrastructure (system integration)
- 1 Finance (validation, reporting)
- 1 Executive Sponsor (governance, sign-off)
```

### Budget Estimate

```
Months 1-6 (Development):
- Personnel: $300K
- Tools/Infrastructure: $50K (Databricks, optimization software)
- Testing/Validation: $25K
- Total: $375K

Months 7-12 (Operations):
- Personnel: $200K (decreased oversight, automation)
- Tools/Infrastructure: $30K
- Monitoring/Optimization: $20K
- Total: $250K

ROI: $4-8M annual savings / $625K investment = 6-12x return
Payback period: 2-4 months
```

---

## Executive Summary for Leadership

**What:** AI-powered markdown optimization system
**Why:** Reduce dead stock, improve margin realization, optimize inventory profitability
**When:** 6-month implementation; ROI in months 2-3
**Where:** All stores, all slow-moving SKUs
**Cost:** $625K over 12 months
**Benefit:** $4-8M annual improvement (5-15% incremental margin)
**Risk:** Medium; mitigated by phased rollout and brand protection rules

---

## Next Steps (This Week)

- [ ] Secure executive sponsor & pricing team lead
- [ ] Schedule data audit meeting with IT/POS teams
- [ ] Define success metrics with stakeholders
- [ ] Identify historical markdown dataset owner
- [ ] Schedule kickoff meeting for Phase 1
