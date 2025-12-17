# Databricks notebook source

# MAGIC %md
# MAGIC # DSP-03: Demand Sensing & Dynamic Pricing - Pricing Optimization
# MAGIC 
# MAGIC This notebook generates dynamic pricing recommendations based on demand forecasts, price elasticity, and business constraints.
# MAGIC 
# MAGIC **Objective:** Recommend optimal prices that maximize revenue and margin while managing inventory risk
# MAGIC 
# MAGIC **Approach:** Constraint optimization considering elasticity, competition, inventory, and margin targets
# MAGIC 
# MAGIC ---

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Import Libraries

# COMMAND ----------

from pyspark.sql.types import *
from pyspark.sql import functions as f
from pyspark.sql.window import Window
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Load Forecast and Prepared Data

# COMMAND ----------

# Load required tables
demand_forecast = spark.table('dsp.demand_forecast')
demand_prepared = spark.table('dsp.demand_prepared')
forecast_accuracy = spark.table('dsp.forecast_accuracy')
demand_confidence = spark.table('dsp.demand_confidence')

print("✓ Loaded demand_forecast")
print("✓ Loaded demand_prepared")
print("✓ Loaded forecast_accuracy")
print("✓ Loaded demand_confidence")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Prepare Data for Pricing Analysis

# COMMAND ----------

# Join forecast with current pricing and inventory data
pricing_base = (
    demand_forecast
    .filter(f.col('date') == f.max('date').over(Window.partitionBy()))  # Latest date
    .select('store_id', 'product_id', 'forecasted_demand', 'forecast_reliability')
    .join(
        demand_prepared
        .select('store_id', 'product_id', 'current_price', 'base_price', 'cost_price', 
                'on_hand_inventory', 'safety_stock', 'competitor_price', 'price_elasticity',
                'margin_percentage', 'gross_margin', 'product_category')
        .dropDuplicates(['store_id', 'product_id']),
        on=['store_id', 'product_id'],
        how='left'
    )
)

display(pricing_base.limit(10))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Calculate Inventory Health Score

# COMMAND ----------

# Assess inventory situation
inventory_health = (
    pricing_base
    .withColumn('inventory_days_supply', f.col('on_hand_inventory') / (f.col('forecasted_demand') + 1))
    .withColumn('inventory_risk_score',
                f.when(f.col('on_hand_inventory') <= f.col('safety_stock'), 100)  # Critical
                .when(f.col('inventory_days_supply') < 7, 75)  # High risk
                .when(f.col('inventory_days_supply') < 15, 50)  # Medium risk
                .when(f.col('inventory_days_supply') < 30, 25)  # Low risk
                .otherwise(10))  # Excess inventory
    .withColumn('inventory_action',
                f.when(f.col('on_hand_inventory') <= f.col('safety_stock'), 'INCREASE_PRICE')
                .when(f.col('inventory_days_supply') > 60, 'CLEARANCE_PRICING')
                .otherwise('NEUTRAL'))
)

display(inventory_health)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Analyze Price Elasticity and Competitive Position

# COMMAND ----------

# Competitive and elasticity analysis
elasticity_analysis = (
    inventory_health
    .withColumn('price_position_vs_competitor', 
                f.round((f.col('current_price') - f.col('competitor_price')) / f.col('competitor_price') * 100, 2))
    .withColumn('is_underpriced',
                f.when(f.col('current_price') < f.col('competitor_price') * 0.95, 1).otherwise(0))
    .withColumn('is_overpriced',
                f.when(f.col('current_price') > f.col('competitor_price') * 1.05, 1).otherwise(0))
    .withColumn('elasticity_category',
                f.when(f.col('price_elasticity') > 1.2, 'HighlyElastic')
                .when(f.col('price_elasticity') > 1.0, 'Elastic')
                .when(f.col('price_elasticity') > 0.8, 'Inelastic')
                .otherwise('VeryInelastic'))
    .withColumn('competitive_opportunity',
                f.when(f.col('is_underpriced') == 1 & (f.col('elasticity_category').isin('VeryInelastic', 'Inelastic')), 'RAISE_PRICE')
                .when(f.col('is_overpriced') == 1 & (f.col('elasticity_category').isin('Elastic', 'HighlyElastic')), 'REDUCE_PRICE')
                .otherwise('MAINTAIN'))
)

display(elasticity_analysis)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Define Pricing Optimization Function

# COMMAND ----------

def calculate_optimal_price(
    current_price,
    base_price,
    cost_price,
    competitor_price,
    price_elasticity,
    forecasted_demand,
    on_hand_inventory,
    safety_stock,
    inventory_days_supply,
    margin_percentage,
    inventory_risk_score,
    inventory_action,
    competitive_opportunity
):
    """
    Calculate optimal price considering multiple objectives
    """
    
    # Base constraints
    min_price = cost_price * 1.1  # Minimum 10% margin
    max_price = base_price * 1.3  # Maximum 30% above base
    
    # Competitive bounds
    competitive_lower = competitor_price * 0.92
    competitive_upper = competitor_price * 1.08
    
    min_price = max(min_price, competitive_lower)
    max_price = min(max_price, competitive_upper)
    
    # Adjust based on inventory situation
    if inventory_action == 'CLEARANCE_PRICING':
        # Aggressive clearance for excess inventory
        optimal_price = cost_price * 1.15
    elif inventory_action == 'INCREASE_PRICE':
        # Premium pricing for scarcity
        optimal_price = min(max_price, current_price * 1.15)
    else:
        # Standard optimization
        if competitive_opportunity == 'RAISE_PRICE':
            # Raise towards competitive ceiling if inelastic
            optimal_price = min(max_price, current_price * 1.08)
        elif competitive_opportunity == 'REDUCE_PRICE':
            # Lower to capture market if elastic
            optimal_price = max(min_price, current_price * 0.92)
        else:
            # Maintain current price
            optimal_price = current_price
    
    # Ensure within bounds
    optimal_price = max(min_price, min(max_price, optimal_price))
    
    # Calculate impact
    revenue_at_current = current_price * forecasted_demand
    revenue_at_optimal = optimal_price * forecasted_demand * price_elasticity
    revenue_lift = (revenue_at_optimal - revenue_at_current) / (revenue_at_current + 1) * 100
    
    margin_at_optimal = optimal_price - cost_price
    
    return {
        'optimal_price': round(optimal_price, 2),
        'min_price': round(min_price, 2),
        'max_price': round(max_price, 2),
        'price_change_pct': round((optimal_price - current_price) / current_price * 100, 2),
        'revenue_lift_pct': round(revenue_lift, 2),
        'margin_at_optimal': round(margin_at_optimal, 2),
        'margin_pct_at_optimal': round((margin_at_optimal / optimal_price) * 100, 2) if optimal_price > 0 else 0
    }

# Register as SQL UDF
spark.udf.register("calculate_optimal_price", calculate_optimal_price, 
                   MapType(StringType(), DoubleType()))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7. Generate Pricing Recommendations

# COMMAND ----------

# Generate recommendations
pricing_recommendations = elasticity_analysis.rdd.map(lambda row: (
    row.store_id,
    row.product_id,
    row.product_category,
    row.current_price,
    row.base_price,
    row.cost_price,
    row.competitor_price,
    row.price_elasticity,
    row.forecasted_demand,
    row.on_hand_inventory,
    row.safety_stock,
    row.inventory_days_supply,
    row.margin_percentage,
    row.inventory_risk_score,
    row.inventory_action,
    row.competitive_opportunity,
    calculate_optimal_price(
        row.current_price,
        row.base_price,
        row.cost_price,
        row.competitor_price,
        row.price_elasticity,
        row.forecasted_demand,
        row.on_hand_inventory,
        row.safety_stock,
        row.inventory_days_supply,
        row.margin_percentage,
        row.inventory_risk_score,
        row.inventory_action,
        row.competitive_opportunity
    )
)).toDF([
    'store_id', 'product_id', 'product_category', 'current_price', 'base_price', 'cost_price',
    'competitor_price', 'price_elasticity', 'forecasted_demand', 'on_hand_inventory', 'safety_stock',
    'inventory_days_supply', 'margin_percentage', 'inventory_risk_score', 'inventory_action',
    'competitive_opportunity', 'optimization_result'
])

# Expand optimization result columns
from pyspark.sql.functions import col
pricing_recommendations = (
    pricing_recommendations
    .withColumn('optimal_price', col('optimization_result')['optimal_price'])
    .withColumn('min_price', col('optimization_result')['min_price'])
    .withColumn('max_price', col('optimization_result')['max_price'])
    .withColumn('price_change_pct', col('optimization_result')['price_change_pct'])
    .withColumn('revenue_lift_pct', col('optimization_result')['revenue_lift_pct'])
    .withColumn('margin_at_optimal', col('optimization_result')['margin_at_optimal'])
    .withColumn('margin_pct_at_optimal', col('optimization_result')['margin_pct_at_optimal'])
    .drop('optimization_result')
    .withColumn('recommendation_date', f.current_date())
)

display(pricing_recommendations)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 8. Create Action Priority Matrix

# COMMAND ----------

# Categorize recommendations by priority
priority_matrix = (
    pricing_recommendations
    .withColumn('priority_score',
                (f.col('revenue_lift_pct') * 0.4) +  # 40% weight: revenue impact
                (f.abs(f.col('inventory_risk_score') - 50) / 50 * 0.3) +  # 30% weight: inventory urgency
                (f.abs(f.col('price_change_pct')) * 0.3))  # 30% weight: magnitude of change
    .withColumn('recommendation_priority',
                f.when(f.col('priority_score') > 75, 'Critical')
                .when(f.col('priority_score') > 50, 'High')
                .when(f.col('priority_score') > 25, 'Medium')
                .otherwise('Low'))
    .withColumn('action_reason',
                f.concat_ws(' | ',
                    f.when(f.col('inventory_action') != 'NEUTRAL', f.col('inventory_action')),
                    f.when(f.col('competitive_opportunity') != 'MAINTAIN', f.col('competitive_opportunity')),
                    f.when(f.col('revenue_lift_pct') > 10, f.concat(f.lit('Revenue Lift: '), f.col('revenue_lift_pct'), f.lit('%')))
                ))
)

display(priority_matrix)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 9. Pricing Action Summary

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT 
# MAGIC   recommendation_priority,
# MAGIC   COUNT(*) as count,
# MAGIC   ROUND(AVG(price_change_pct), 2) as avg_price_change_pct,
# MAGIC   ROUND(AVG(revenue_lift_pct), 2) as avg_revenue_lift_pct,
# MAGIC   ROUND(AVG(margin_pct_at_optimal), 2) as avg_margin_pct
# MAGIC FROM (
# MAGIC   SELECT DISTINCT store_id, product_id, 
# MAGIC          recommendation_priority, price_change_pct, revenue_lift_pct, margin_pct_at_optimal
# MAGIC   FROM pricing_recommendations
# MAGIC )
# MAGIC GROUP BY recommendation_priority
# MAGIC ORDER BY CASE WHEN recommendation_priority = 'Critical' THEN 1 
# MAGIC               WHEN recommendation_priority = 'High' THEN 2
# MAGIC               WHEN recommendation_priority = 'Medium' THEN 3
# MAGIC               ELSE 4 END

# COMMAND ----------

# MAGIC %md
# MAGIC ## 10. Exception Alerts and High-Impact Changes

# COMMAND ----------

# Identify high-impact pricing decisions
price_exceptions = (
    priority_matrix
    .filter((f.abs(f.col('price_change_pct')) > 15) | 
            (f.col('revenue_lift_pct') > 25) |
            (f.col('inventory_action') != 'NEUTRAL'))
    .select('store_id', 'product_id', 'product_category', 'current_price', 'optimal_price',
            'price_change_pct', 'revenue_lift_pct', 'inventory_action', 'recommendation_priority')
    .orderBy(f.desc('price_change_pct'))
)

print(f"High-impact pricing changes: {price_exceptions.count()}")
display(price_exceptions.limit(20))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 11. Simulate Impact of Recommendations

# COMMAND ----------

# Calculate potential impact if all recommendations are implemented
impact_simulation = (
    priority_matrix
    .agg(
        f.count('*').alias('total_skus'),
        f.sum(f.when(f.col('price_change_pct') > 0, 1).otherwise(0)).alias('price_increases'),
        f.sum(f.when(f.col('price_change_pct') < 0, 1).otherwise(0)).alias('price_decreases'),
        f.round(f.avg(f.abs(f.col('price_change_pct'))), 2).alias('avg_price_change_pct'),
        f.round(f.avg(f.col('revenue_lift_pct')), 2).alias('avg_revenue_lift_pct'),
        f.round(f.sum(f.col('revenue_lift_pct')) / f.count('*'), 2).alias('total_revenue_lift_pct')
    )
)

print("Impact Simulation:")
display(impact_simulation)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 12. Comparative Analysis: Current vs Recommended

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT 
# MAGIC   'Current' as scenario,
# MAGIC   ROUND(AVG(current_price), 2) as avg_price,
# MAGIC   ROUND(AVG(margin_percentage), 2) as avg_margin_pct,
# MAGIC   ROUND(COUNT(*) * AVG(current_price) * AVG(forecasted_demand), 0) as projected_revenue
# MAGIC FROM (SELECT DISTINCT store_id, product_id, current_price, margin_percentage, forecasted_demand FROM pricing_recommendations)
# MAGIC 
# MAGIC UNION ALL
# MAGIC 
# MAGIC SELECT 
# MAGIC   'Recommended' as scenario,
# MAGIC   ROUND(AVG(optimal_price), 2) as avg_price,
# MAGIC   ROUND(AVG(margin_pct_at_optimal), 2) as avg_margin_pct,
# MAGIC   ROUND(COUNT(*) * AVG(optimal_price) * AVG(forecasted_demand) * AVG(price_elasticity), 0) as projected_revenue
# MAGIC FROM (SELECT DISTINCT store_id, product_id, optimal_price, margin_pct_at_optimal, forecasted_demand, price_elasticity FROM pricing_recommendations)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 13. Persist Pricing Recommendations

# COMMAND ----------

# Save main recommendations table
(
    priority_matrix
    .repartition(sc.defaultParallelism)
    .write
    .format('delta')
    .mode('overwrite')
    .option('overwriteSchema', 'true')
    .saveAsTable('dsp.pricing_recommendations')
)

print("✓ Saved: dsp.pricing_recommendations")

# Save exception alerts
(
    price_exceptions
    .write
    .format('delta')
    .mode('overwrite')
    .option('overwriteSchema', 'true')
    .saveAsTable('dsp.pricing_exceptions')
)

print("✓ Saved: dsp.pricing_exceptions")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 14. Generate Executive Summary Report

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT 
# MAGIC   COUNT(DISTINCT store_id) as total_stores,
# MAGIC   COUNT(DISTINCT product_id) as total_products,
# MAGIC   ROUND(AVG(current_price), 2) as current_avg_price,
# MAGIC   ROUND(AVG(optimal_price), 2) as recommended_avg_price,
# MAGIC   ROUND((AVG(optimal_price) - AVG(current_price)) / AVG(current_price) * 100, 2) as overall_price_change_pct,
# MAGIC   ROUND(AVG(revenue_lift_pct), 2) as projected_revenue_lift_pct,
# MAGIC   ROUND(AVG(margin_pct_at_optimal) - AVG(margin_percentage), 2) as margin_improvement_pct_pts,
# MAGIC   SUM(CASE WHEN recommendation_priority = 'Critical' THEN 1 ELSE 0 END) as critical_actions,
# MAGIC   SUM(CASE WHEN recommendation_priority = 'High' THEN 1 ELSE 0 END) as high_priority_actions
# MAGIC FROM dsp.pricing_recommendations

# COMMAND ----------

# MAGIC %md
# MAGIC ## Dynamic Pricing Optimization Complete!
# MAGIC 
# MAGIC ✓ Price elasticity and competitive position analyzed  
# MAGIC ✓ Inventory health assessed and risk scored  
# MAGIC ✓ Optimal prices calculated using constraint optimization  
# MAGIC ✓ Pricing actions prioritized by impact  
# MAGIC ✓ Exception alerts generated for high-impact changes  
# MAGIC ✓ Impact simulations completed  
# MAGIC ✓ Recommendations stored for implementation  
# MAGIC 
# MAGIC ## Key Deliverables
# MAGIC 
# MAGIC **`dsp.pricing_recommendations`** - Complete pricing recommendations for all store-product combinations
# MAGIC - Current vs Recommended pricing
# MAGIC - Expected revenue and margin impact
# MAGIC - Action reasoning and priority levels
# MAGIC - Constraints and bounds for safety
# MAGIC 
# MAGIC **`dsp.pricing_exceptions`** - High-impact changes requiring additional review
# MAGIC - Price changes > 15%
# MAGIC - Revenue lift opportunities > 25%
# MAGIC - Inventory-driven pricing actions
# MAGIC 
# MAGIC ## Implementation Recommendations
# MAGIC 
# MAGIC 1. **Review Critical Recommendations** - Validate top 20 recommendations before rollout
# MAGIC 2. **A/B Test Recommendations** - Test pricing changes on subset of stores
# MAGIC 3. **Monitor KPIs** - Track actual vs projected revenue and margin impact
# MAGIC 4. **Automate Execution** - Integrate recommendations into pricing system
# MAGIC 5. **Iterate Regularly** - Re-run analysis monthly or when major market changes occur
# MAGIC 
# MAGIC **Access Results:**
# MAGIC - View recommendations: `SELECT * FROM dsp.pricing_recommendations`
# MAGIC - View exceptions: `SELECT * FROM dsp.pricing_exceptions`
# MAGIC - View forecast accuracy: `SELECT * FROM dsp.forecast_accuracy`