# Supply Chain Planning & Optimization (SCOPO) - Agentic Use Case

## Overview
This multi-notebook Databricks use case demonstrates an **agentic demand planning and supply chain optimization system** that automatically monitors inventory levels, forecasts demand, optimizes reorder strategies, and generates actionable recommendations for supply chain managers.

## Use Case Description

### Business Problem
Retail enterprises face critical supply chain challenges:
- **Demand Forecasting Accuracy**: Predicting customer demand across multiple stores and products
- **Inventory Optimization**: Balancing stockouts vs. excess inventory
- **Dynamic Reordering**: Determining optimal order quantities and timing
- **Cost Optimization**: Minimizing inventory holding costs while meeting service levels
- **Supplier Coordination**: Managing lead times and order fulfillment

### Solution Architecture
The SCOPO system uses an **agentic approach** with multiple specialized agents:
1. **Demand Forecasting Agent**: Predicts future demand using time-series models
2. **Inventory Analysis Agent**: Identifies stockout risks and excess inventory
3. **Replenishment Agent**: Calculates optimal reorder quantities (EOQ)
4. **Cost Analysis Agent**: Evaluates financial impact of inventory decisions
5. **Recommendation Agent**: Generates actionable insights and actions

### Key Metrics
- **Demand Forecast Accuracy (MAPE)**
- **Service Level (Fill Rate)**
- **Inventory Turnover Ratio**
- **Carrying Cost vs. Stockout Cost**
- **Supplier Performance Metrics**

## Data Structure

### Input Data: `demand_planning_data.csv`
Main dataset containing daily inventory and demand information:
- **date**: Transaction date
- **store_id**: Store identifier
- **product_id**: Product SKU
- **forecasted_demand**: Predicted demand units
- **actual_demand**: Actual demand units
- **stock_on_hand**: Current inventory units
- **base_price**: Product price
- **unit_cost**: Product cost
- **promotion_discount**: Promotional discount (0-20%)
- **lead_time_days**: Supplier lead time
- **supplier_id**: Supplier identifier
- **qty_on_order**: Units on order from supplier

## Notebook Structure

### Notebook 1: SCOPO-01-Data-Preparation
**Purpose**: Data ingestion, validation, and preparation
- Load CSV data
- Create base delta tables
- Calculate derived metrics (demand patterns, seasonality)
- Validate data quality
- Output: `scopo.demand_raw` and `scopo.demand_prepared`

### Notebook 2: SCOPO-02-Demand-Forecasting
**Purpose**: Demand forecasting and accuracy analysis
- Implement time-series forecasting models (Exponential Smoothing, ARIMA)
- Calculate forecast accuracy (MAPE, MAE, RMSE)
- Identify demand patterns and seasonality
- Generate forecast anomaly alerts
- Output: `scopo.demand_forecast` and `scopo.forecast_accuracy`

### Notebook 3: SCOPO-03-Inventory-Analysis
**Purpose**: Inventory health assessment and risk identification
- Calculate ABC analysis (Pareto classification)
- Identify slow-moving vs fast-moving items
- Flag stockout risks and excess inventory
- Calculate safety stock requirements
- Generate inventory alerts
- Output: `scopo.inventory_analysis` and `scopo.inventory_alerts`

### Notebook 4: SCOPO-04-Replenishment-Optimization
**Purpose**: Optimal reordering strategy
- Calculate Economic Order Quantity (EOQ)
- Determine reorder points considering lead time
- Optimize order timing
- Generate replenishment recommendations
- Evaluate supplier alternatives
- Output: `scopo.replenishment_strategy` and `scopo.reorder_recommendations`

### Notebook 5: SCOPO-05-Cost-Optimization
**Purpose**: Financial analysis and cost minimization
- Calculate inventory holding costs
- Estimate stockout costs and lost revenue
- Perform trade-off analysis
- Recommend optimal inventory levels
- Generate cost savings opportunities
- Output: `scopo.cost_analysis` and `scopo.optimization_results`

### Notebook 6: SCOPO-06-Agent-Orchestration
**Purpose**: Agentic recommendation system
- Coordinate all agents
- Synthesize insights across modules
- Generate executive recommendations
- Create action items and KPI dashboards
- Output: `scopo.agent_recommendations` and `scopo.executive_summary`

## Key Features

### Agentic Capabilities
- **Autonomous Decision-Making**: Each agent independently analyzes its domain
- **Collaborative Intelligence**: Agents share insights to reach optimal decisions
- **Adaptive Optimization**: Recommenations adjust based on current inventory state
- **Exception Management**: Automatic alerts for anomalies
- **Scalability**: Handles 1000s of store-product combinations

### Advanced Analytics
- Time-series decomposition (trend, seasonality, residuals)
- Predictive modeling with cross-validation
- Multi-objective optimization (service level vs cost)
- Supplier performance benchmarking
- Scenario analysis and what-if modeling

### Actionable Outputs
- Reorder recommendations with quantities and timing
- Supplier performance scorecards
- Cost-benefit analysis
- KPI dashboards
- Executive summary with top N actions

## Running the Use Case

1. **Upload data file**: Place `demand_planning_data.csv` in `/mnt/scopo/` or upload via UI
2. **Run notebooks sequentially**: SCOPO-01 → SCOPO-02 → SCOPO-03 → SCOPO-04 → SCOPO-05 → SCOPO-06
3. **Monitor outputs**: Check created delta tables and generated recommendations
4. **Act on recommendations**: Implement top priority actions

## Success Metrics

- **Forecast Accuracy**: Achieve MAPE < 15%
- **Service Level**: Maintain > 95% fill rate
- **Inventory Turnover**: Increase by 20%
- **Cost Savings**: Reduce holding costs by 15%
- **Decision Time**: < 2 minutes to generate full recommendations

---
Created by Databricks Advisory | Enterprise Supply Chain Analytics
