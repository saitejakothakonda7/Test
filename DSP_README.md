# Demand Sensing & Dynamic Pricing (DSP) Accelerator

## Overview

The Demand Sensing & Dynamic Pricing accelerator is designed to help retailers optimize pricing and inventory management through data-driven demand forecasting and dynamic pricing strategies. This multi-notebook solution provides a comprehensive framework for:

1. **Demand Forecasting** - Predicting customer demand patterns based on historical data, seasonality, and external factors
2. **Price Elasticity Analysis** - Understanding how price changes affect demand across different products and stores
3. **Dynamic Pricing Optimization** - Recommending optimal prices to maximize revenue and margin while managing inventory
4. **Inventory Risk Assessment** - Identifying products at risk of stockout or overstock situations

## Use Case Description

Retailers face the challenge of balancing multiple competing objectives:
- **Revenue Maximization** - Setting prices to capture maximum customer spending
- **Margin Optimization** - Maintaining healthy profit margins while staying competitive
- **Inventory Management** - Reducing waste from excess inventory and lost sales from stockouts
- **Competitive Positioning** - Responding to competitor pricing while maintaining market share

The DSP accelerator addresses these challenges by:
- Analyzing historical demand patterns and price sensitivity
- Forecasting demand under different pricing scenarios
- Recommending optimal prices based on inventory levels, margin targets, and demand elasticity
- Monitoring competitive pricing and demand trends
- Identifying high-risk inventory situations requiring intervention

## Data Assets

### 1. Demand Sensing Data (`demand_sensing_data.csv`)
Contains daily transaction and inventory data across multiple stores and products

**Key Fields:**
- `date` - Transaction date (YYYYMMDD format)
- `store_id` - Store identifier
- `product_id` - Product SKU
- `product_category` - Product category
- `quantity_demanded` - Units sold
- `on_hand_inventory` - Current inventory level
- `safety_stock` - Minimum safe inventory level
- `current_price` - Current selling price ($)
- `base_price` - Reference/base price ($)
- `cost_price` - Cost to acquire product ($)
- `gross_margin` - Absolute profit per unit ($)
- `margin_percentage` - Profit margin (%)
- `competitor_price` - Competitor's selling price ($)
- `price_elasticity` - Sensitivity of demand to price changes
- `is_promoted` - Flag indicating promotional pricing
- `promotion_discount_pct` - Discount percentage if promoted (%)
- `days_inventory` - Days of supply on hand
- `stockout_risk` - Flag indicating inventory below safety stock

**Data Characteristics:**
- 5 stores × 5 products × 730 days = 18,250 records
- Time period: January 1, 2022 - December 31, 2023
- Realistic seasonality patterns (peaks and troughs throughout year)
- Price variations simulating competitive dynamics
- Promotion events (~15% of records)

### 2. Product Master Data (synthesized in notebooks)
Product categories and their baseline characteristics

### 3. External Factors (to be simulated)
Weather patterns, holidays, and seasonal trends

## Notebook Structure

### Notebook 1: DSP-01-Data-Preparation
**Purpose:** Data ingestion, cleaning, and feature engineering

**Key Activities:**
1. Load demand data from CSV
2. Validate data quality and handle missing values
3. Calculate derived metrics:
   - Revenue (quantity × price)
   - Inventory turnover ratios
   - Sell-through rates
   - Days inventory outstanding (DIO)
4. Create time-series features:
   - Day of week, month, quarter
   - Lag features (previous 7, 14, 30 days)
   - Rolling averages and standard deviations
5. Identify and flag anomalies

### Notebook 2: DSP-02-Demand-Forecasting
**Purpose:** Build demand forecasting models using time-series techniques

**Key Activities:**
1. Prepare data for modeling
2. Apply exponential smoothing to baseline demand
3. Build multiple forecasting models:
   - Simple Exponential Smoothing (baseline)
   - Prophet (seasonal decomposition)
   - ARIMA (autoregressive models)
4. Generate demand forecasts by store-product combination
5. Calculate forecast accuracy metrics (MAPE, RMSE)
6. Identify forecast errors and apply corrections

### Notebook 3: DSP-03-Dynamic-Pricing-Optimization
**Purpose:** Recommend optimal prices based on demand elasticity and business objectives

**Key Activities:**
1. Calculate price elasticity curves for each product
2. Analyze competitive positioning
3. Formulate pricing optimization as:
   - Maximize: Revenue × Margin × Availability
   - Subject to: Inventory constraints, margin minimums, competitive bounds
4. Generate pricing recommendations with confidence intervals
5. Simulate impact on demand and revenue
6. Create exception alerts for:
   - Stockout risk situations
   - High-margin underpriced products
   - Overstock requiring clearance pricing
7. Track metrics over time

## Key Business Metrics

| Metric | Definition | Target |
|--------|-----------|--------|
| **Forecast Accuracy (MAPE)** | Mean Absolute Percentage Error in demand forecasts | < 15% |
| **Gross Margin %** | (Revenue - COGS) / Revenue | > 35% |
| **Inventory Turnover** | COGS / Average Inventory | 8-12x annually |
| **Stockout Rate** | Days with inventory ≤ safety stock / Total days | < 5% |
| **Days Inventory Outstanding** | Average inventory / (Annual demand / 365) | 20-30 days |
| **Price Competitiveness** | Own price / Competitor price | 0.95-1.05 |
| **Revenue per Unit** | Total revenue / Total units sold | Track trend |
| **Elasticity Sensitivity** | % demand change / % price change | -0.5 to -1.5 |

## Technology Stack

- **Databricks** - Platform for unified analytics and ML
- **PySpark** - Distributed data processing
- **Pandas** - Data manipulation and analysis
- **StatsModels** - Statistical modeling (exponential smoothing, ARIMA)
- **Scikit-Learn** - Machine learning utilities
- **Delta Lake** - ACID-compliant data storage
- **SQL** - Data querying and aggregation

## Business Impact

### Revenue Optimization
- Identify underpriced high-demand products → 5-10% revenue uplift
- Optimize pricing around competitor actions
- Reduce unsaleable excess inventory through dynamic clearance pricing

### Margin Improvement
- Avoid unnecessary discounting on price-insensitive products
- Optimize promotion allocation to high-elasticity products
- Reduce markdown losses through proactive pricing

### Inventory Efficiency
- Reduce stockout events through better demand visibility
- Lower carrying costs through better turnover
- Minimize obsolescence through dynamic repricing

### Operational Excellence
- Automated demand forecasting reduces manual effort
- Data-driven pricing removes guesswork
- Early warning system for inventory issues

## Next Steps

1. Mount data files to `/mnt/dsp/` in your Databricks environment
2. Run notebooks sequentially: DSP-01 → DSP-02 → DSP-03
3. Review outputs and dashboards
4. Customize thresholds and parameters for your business
5. Set up scheduled runs for continuous insights
6. Integrate pricing recommendations into your POS/inventory system

## Support & Customization

This accelerator provides a foundation that can be extended with:
- Additional external data sources (weather, events, promotions)
- Advanced ML models (gradient boosting, neural networks)
- Real-time streaming data integration
- Integration with pricing systems and ERP
- Cross-category demand correlations
- Customer segmentation and personalized pricing
