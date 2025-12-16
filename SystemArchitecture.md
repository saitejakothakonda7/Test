# SYSTEM ARCHITECTURE: Markdown Optimization Use Case

## End-to-End Data & ML Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATA SOURCES & INGESTION                           │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
    │   POS System     │  │ ERP / Inventory  │  │  Cost System     │
    │ • Sales data     │  │  • Daily stock   │  │  • Unit costs    │
    │ • Prices         │  │  • Replenishment │  │  • Margins       │
    │ • Transactions   │  │  • SKU master    │  │  • Pricing rules │
    └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘
             │                     │                     │
             │        ETL Pipeline │                     │
             └─────────────────────┼─────────────────────┘
                                   ↓
    ┌──────────────────────────────────────────────────────────┐
    │  Data Lake Staging Layer (Databricks Data Lake)          │
    │  • /data/markdown_optimization/raw/                      │
    │  • /data/markdown_optimization/staging/                  │
    └──────────────────────────────────────────────────────────┘
                          ↓

┌─────────────────────────────────────────────────────────────────────────────┐
│                       FEATURE ENGINEERING & PREPARATION                     │
└─────────────────────────────────────────────────────────────────────────────┘

    Input: Raw daily inventory records
            ↓
    ┌────────────────────────────────────────────────────────────┐
    │  1. Data Cleansing                                         │
    │     • Handle missing values                               │
    │     • Validate data types & ranges                        │
    │     • Remove duplicates                                   │
    └────────────────────────────────────────────────────────────┘
            ↓
    ┌────────────────────────────────────────────────────────────┐
    │  2. Time Series Feature Generation                        │
    │     class MarkdownDataPreparation:                        │
    │                                                            │
    │     Features Created:                                     │
    │     ├─ sales_7day_ma          (7-day moving average)     │
    │     ├─ sales_30day_ma         (30-day moving average)    │
    │     ├─ sales_momentum         (acceleration indicator)   │
    │     ├─ days_since_replenishment                          │
    │     ├─ shelf_utilization_ratio                           │
    │     ├─ days_to_deplete                                   │
    │     ├─ pipeline_ratio                                    │
    │     ├─ zero_sales_streak                                 │
    │     └─ replenishment_flag                                │
    └────────────────────────────────────────────────────────────┘
            ↓
    ┌────────────────────────────────────────────────────────────┐
    │  3. Feature Store Materialization                         │
    │     Table: markdown_features                              │
    │     Grain: store_id, sku, date                            │
    │     Partitioning: By date (for performance)               │
    │     Refresh: Daily (11 PM)                                │
    └────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                    MACHINE LEARNING MODEL LAYER                              │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌─────────────────────────────────────────────────────────────┐
    │  MODEL 1: Inventory Lifecycle Predictor                    │
    │  ─────────────────────────────────────────────────────────  │
    │  Algorithm:  GradientBoostingClassifier (XGBoost)          │
    │  Task:       Binary classification (slow-moving or not)    │
    │  Input:      Features from Feature Store                   │
    │  Output:     Probability (0-1) of becoming slow-moving     │
    │                                                             │
    │  Model Configuration:                                      │
    │    • n_estimators: 100                                     │
    │    • learning_rate: 0.1                                    │
    │    • max_depth: 5                                          │
    │    • random_state: 42                                      │
    │                                                             │
    │  Target Definition:                                        │
    │    is_slow_moving = (future_30day_sales < 25th percentile) │
    │                                                             │
    │  Performance Metrics:                                      │
    │    • Accuracy: 85-90%                                      │
    │    • ROC-AUC: 0.88-0.92                                    │
    │    • Precision/Recall: 0.85+                               │
    │                                                             │
    │  Feature Importance (Top 5):                               │
    │    1. sales_momentum (0.28)                                │
    │    2. days_to_deplete (0.22)                               │
    │    3. shelf_utilization_ratio (0.18)                       │
    │    4. sales_7day_ma (0.15)                                 │
    │    5. zero_sales_streak (0.12)                             │
    │                                                             │
    │  Retraining: Weekly                                        │
    └─────────────────────────────────────────────────────────────┘
                    ↓
    ┌─────────────────────────────────────────────────────────────┐
    │  MODEL 2: Price Elasticity Estimator                       │
    │  ─────────────────────────────────────────────────────────  │
    │  Algorithm:  Mixed Effects Regression + LightGBM           │
    │  Task:       Estimate price elasticity by category+store   │
    │  Input:      Historical markdown data (12-24 months)       │
    │  Output:     Elasticity coefficient (e.g., -1.3)           │
    │                                                             │
    │  Formula:                                                   │
    │    ln(Qty_new / Qty_old) = β₀ + β₁*ln(Price_new/Price_old)│
    │    β₁ = elasticity coefficient                             │
    │                                                             │
    │  Stratification:                                            │
    │    - By product category (Electronics, Apparel, etc)       │
    │    - By store location (Urban, Suburban, Rural)            │
    │    - By season (if applicable)                             │
    │                                                             │
    │  Fallback Strategy:                                         │
    │    If insufficient data for specific segment:              │
    │    Use category-level default elasticity                   │
    │                                                             │
    │  Typical Elasticity Values:                                │
    │    • Electronics: -1.8 to -2.0 (high elasticity)          │
    │    • Apparel: -1.3 to -1.5 (medium elasticity)            │
    │    • Groceries: -0.6 to -0.8 (low elasticity)             │
    │                                                             │
    │  Retraining: Monthly (with new markdown data)              │
    └─────────────────────────────────────────────────────────────┘
                    ↓
    ┌─────────────────────────────────────────────────────────────┐
    │  MODEL 3: Markdown Optimization Engine                     │
    │  ─────────────────────────────────────────────────────────  │
    │  Algorithm:  Constrained Non-linear Optimization (SLSQP)  │
    │  Framework:  scipy.optimize                                │
    │  Task:       Calculate profit-maximizing markdown price    │
    │                                                             │
    │  Objective Function:                                        │
    │                                                             │
    │    Maximize: Margin_$ = Units_Sold × (Price - Cost)       │
    │                                                             │
    │    Where:                                                   │
    │    • Price = Current_Price × (1 - Discount%)              │
    │    • Units_Sold = Current_Units ×                         │
    │                   (1 + Elasticity × Price_Change%)^(1/E)  │
    │                                                             │
    │  Constraints:                                               │
    │    1. Margin floor:  (Price - Cost) / Price ≥ min_margin% │
    │    2. Discount cap:  Discount_% ≤ max_discount%           │
    │    3. Competitor floor: Price ≥ competitor_price * (1-gap%│
    │                                                             │
    │  Decision Variable:                                         │
    │    • Discount percentage (0 to max_discount_%)             │
    │                                                             │
    │  Default Constraints:                                       │
    │    • min_margin_pct: 15% (configurable)                    │
    │    • max_discount_pct: 35% (configurable)                  │
    │    • competitor_price_gap: 15% (configurable)              │
    │                                                             │
    │  Output:                                                    │
    │    optimal_discount_%, optimal_price, predicted_units,     │
    │    predicted_margin_$, margin_impact_$                     │
    │                                                             │
    │  Computation Time: <100ms per SKU                           │
    └─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                    RECOMMENDATION GENERATION ENGINE                          │
└─────────────────────────────────────────────────────────────────────────────┘

    Step 1: Filter Candidates
    ┌────────────────────────────────────────────────────────────┐
    │ Apply filters to all store-SKU combinations:              │
    │  ✓ Clearance_probability > threshold (default: 0.60)      │
    │  ✓ Days_to_deplete < 30 days                              │
    │  ✓ Not already marked down in past 14 days                │
    │  ✓ Not part of active promotion                           │
    │  ✓ Has minimum 10 days of history                         │
    │                                                             │
    │ Result: "Clearance candidates" dataset                    │
    └────────────────────────────────────────────────────────────┘
            ↓
    Step 2: Calculate Optimal Markdowns
    ┌────────────────────────────────────────────────────────────┐
    │ For each candidate:                                       │
    │  1. Retrieve current price, cost, inventory              │
    │  2. Look up elasticity (category+store)                  │
    │  3. Run optimization solver                              │
    │  4. Validate against constraints                         │
    │                                                            │
    │ Result: "Recommendation set" with 1000+ SKUs daily       │
    └────────────────────────────────────────────────────────────┘
            ↓
    Step 3: Categorize for Approval Path
    ┌────────────────────────────────────────────────────────────┐
    │ AUTOMATED (70%):                                          │
    │  • Margin floor met ✓                                     │
    │  • No conflicts ✓                                         │
    │  • Clearance_prob > 0.70 ✓                                │
    │  Action: Auto-push to POS (pending manager review)        │
    │                                                             │
    │ MANUAL REVIEW (30%):                                      │
    │  • Strategic SKUs (high-value, brand-sensitive)           │
    │  • Clearance_prob 0.55-0.70 (borderline)                  │
    │  • Margin floor violated (discretionary decision)         │
    │  • Promotional conflicts                                   │
    │  Action: Route to pricing team for approval               │
    └────────────────────────────────────────────────────────────┘
            ↓
    ┌────────────────────────────────────────────────────────────┐
    │  Markdown Recommendations Table                           │
    │  (Store to DB: markdown_recommendations)                  │
    │                                                             │
    │  Fields:                                                   │
    │  • recommendation_id (unique)                              │
    │  • store_id, sku                                           │
    │  • current_price, recommended_price                        │
    │  • discount_pct, margin_floor_pct                         │
    │  • predicted_units, predicted_margin_$                     │
    │  • clearance_probability                                   │
    │  • approval_path (automated/manual)                        │
    │  • recommended_start_date                                  │
    │  • created_timestamp                                       │
    └────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                      INTEGRATION & DEPLOYMENT LAYER                          │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌────────────────────────────────────────────────────────────┐
    │  REST API Service                                         │
    │                                                             │
    │  Endpoints:                                                │
    │  GET  /recommendations/pending                            │
    │  POST /recommendations/{id}/approve                       │
    │  POST /recommendations/{id}/reject                        │
    │  GET  /recommendations/performance                        │
    │  POST /models/retrain                                     │
    └────────────────────────────────────────────────────────────┘
            ↓
    ┌────────────────────────────────────────────────────────────┐
    │  POS System Integration                                   │
    │                                                             │
    │  Approved recommendations flow to:                        │
    │  • POS pricing engine                                     │
    │  • Signage/label generation                               │
    │  • Promotional calendar                                   │
    │  • Customer-facing apps                                   │
    └────────────────────────────────────────────────────────────┘
            ↓
    ┌────────────────────────────────────────────────────────────┐
    │  Feedback Loop: Monitor Actual Performance                │
    │                                                             │
    │  Daily collection:                                         │
    │  • Actual markdown prices applied                          │
    │  • Actual sales volume post-markdown                       │
    │  • Actual clearance velocity                               │
    │  • Customer feedback/complaints                            │
    │                                                             │
    │  Monthly analysis:                                         │
    │  • Prediction accuracy (predicted vs actual)               │
    │  • Elasticity validation                                   │
    │  • Margin realization                                      │
    │  • Model drift detection                                   │
    └────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                       MONITORING & GOVERNANCE LAYER                          │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌─ Model Monitoring ────────────────────────────────────────┐
    │  • Prediction accuracy (MAPE < 15%)                       │
    │  • Data drift detection                                   │
    │  • Model performance degradation alerts                   │
    │  • Retraining triggers                                    │
    └──────────────────────────────────────────────────────────┘
            ↓
    ┌─ Business Metrics Dashboard ──────────────────────────────┐
    │  Real-time KPIs:                                          │
    │  • Recommendations generated (daily)                       │
    │  • Approval rate (automated vs manual)                    │
    │  • Clearance time (vs. target)                            │
    │  • Margin realization (predicted vs actual)               │
    │  • Dead stock reduction (%)                               │
    │  • Inventory turns (vs. baseline)                         │
    └──────────────────────────────────────────────────────────┘
            ↓
    ┌─ Governance & Audit ──────────────────────────────────────┐
    │  • All recommendations logged & auditable                 │
    │  • Approval chain documented                               │
    │  • Price compliance checks                                │
    │  • Brand protection rules enforced                        │
    │  • Quarterly model reviews                                │
    └──────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                              EXECUTION ENVIRONMENT                            │
└─────────────────────────────────────────────────────────────────────────────┘

    Databricks Platform:
    ├─ Cluster: 8-core, 32GB RAM
    ├─ Spark version: 11.3 LTS
    ├─ Python: 3.9+
    ├─ Libraries: pandas, numpy, scikit-learn, xgboost, lightgbm, scipy
    └─ Notebooks: Organized by function (feature eng, modeling, optimization)

    Scheduling:
    ├─ Daily (11 PM): Feature calculation → Model prediction → Recommendations
    ├─ Weekly (Monday 6 AM): Model retraining
    ├─ Monthly: Elasticity model update
    └─ Quarterly: Full model audit & recalibration

```

---

## Data Flow Diagram: Daily Execution

```
                        DAILY EXECUTION (11 PM)

    ┌──────────────────────────────────────────────────────────┐
    │ 1. Extract Latest Data (22:00)                           │
    │    • Daily inventory snapshot from osa.inventory          │
    │    • Replenishment data from vendor table                 │
    │    • Promotional calendar (if updated)                   │
    │    Runtime: 5-10 minutes                                 │
    └──────────────┬───────────────────────────────────────────┘
                   ↓
    ┌──────────────────────────────────────────────────────────┐
    │ 2. Feature Engineering (22:10)                           │
    │    • Calculate 7d, 30d moving averages                   │
    │    • Compute shelf utilization, days-to-deplete          │
    │    • Update feature store tables                         │
    │    Runtime: 15-20 minutes                                │
    └──────────────┬───────────────────────────────────────────┘
                   ↓
    ┌──────────────────────────────────────────────────────────┐
    │ 3. Load Models & Run Predictions (22:30)                │
    │    • Load lifecycle_predictor (XGBoost)                  │
    │    • Load elasticity_models (category×store)             │
    │    • Batch predict: 40K store-SKU records                │
    │    • Filter clearance candidates (prob > 0.60)           │
    │    Runtime: 10-15 minutes                                │
    └──────────────┬───────────────────────────────────────────┘
                   ↓
    ┌──────────────────────────────────────────────────────────┐
    │ 4. Optimization & Recommendation Generation (22:45)     │
    │    • Run solver for each candidate                       │
    │    • Validate constraints                                │
    │    • Categorize for approval path                        │
    │    • ~2,000 recommendations generated                    │
    │    Runtime: 20-25 minutes                                │
    └──────────────┬───────────────────────────────────────────┘
                   ↓
    ┌──────────────────────────────────────────────────────────┐
    │ 5. Store Results & Notifications (23:10)                │
    │    • Persist to markdown_recommendations table            │
    │    • Generate dashboard refresh                          │
    │    • Email alerts to approvers (if manual review needed)  │
    │    • Prepare API payload for POS                         │
    │    Runtime: 5 minutes                                    │
    └──────────────┬───────────────────────────────────────────┘
                   ↓
    ┌──────────────────────────────────────────────────────────┐
    │ ✓ READY FOR MORNING REVIEW (23:15)                      │
    │   • Pricing team reviews at 8 AM                         │
    │   • Approves automated (70%) + reviews manual (30%)       │
    │   • Approved prices pushed to POS by 10 AM               │
    └──────────────────────────────────────────────────────────┘

    TOTAL RUNTIME: 50 minutes (easily completes by midnight)
```

---

## Technology Dependencies

```
Core Libraries:
├─ Pandas 1.4+
├─ NumPy 1.22+
├─ Scikit-learn 1.0+
├─ XGBoost 1.5+
├─ LightGBM 3.3+
├─ SciPy 1.7+ (optimization)
├─ PySpark 3.2+
└─ Statsmodels (elasticity)

Deployment:
├─ Databricks Workspace
├─ Delta Lake (data storage)
├─ Databricks Jobs (scheduling)
├─ MLflow (model tracking)
└─ REST API (Flask/FastAPI)

Monitoring:
├─ Databricks SQL (dashboards)
├─ MLflow (model metrics)
└─ Custom monitoring scripts
```

This architecture is designed to be:
✅ **Scalable** - Handles millions of SKU-store combinations
✅ **Automated** - Fully hands-off daily execution
✅ **Transparent** - All recommendations are explainable
✅ **Flexible** - Easily adjust constraints & strategies
✅ **Monitored** - Real-time performance tracking
✅ **Governed** - Full audit trail of decisions
