# Databricks notebook source

# MAGIC %md
# MAGIC # DSP-01: Demand Sensing & Dynamic Pricing - Data Preparation
# MAGIC 
# MAGIC This notebook performs data ingestion, cleaning, validation, and feature engineering for the Demand Sensing & Dynamic Pricing use case.
# MAGIC 
# MAGIC **Objective:** Prepare high-quality, feature-rich data for demand forecasting and pricing optimization
# MAGIC 
# MAGIC **Created:** 2024 | **Author:** Databricks Solutions
# MAGIC
# MAGIC ---

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Import Required Libraries

# COMMAND ----------

from pyspark.sql.types import *
from pyspark.sql import functions as f
from pyspark.sql.window import Window
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Create DSP Database and Configure Paths

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Create database to house data assets
# MAGIC DROP DATABASE IF EXISTS dsp CASCADE;
# MAGIC CREATE DATABASE IF NOT EXISTS dsp;
# MAGIC 
# MAGIC -- Show database created
# MAGIC SHOW DATABASES;

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Define Data Schema and Load Raw Data

# COMMAND ----------

# Define schema for demand sensing data
demand_schema = StructType([
    StructField('date', StringType()),
    StructField('store_id', IntegerType()),
    StructField('product_id', IntegerType()),
    StructField('product_category', StringType()),
    StructField('quantity_demanded', IntegerType()),
    StructField('on_hand_inventory', IntegerType()),
    StructField('safety_stock', IntegerType()),
    StructField('current_price', DoubleType()),
    StructField('base_price', DoubleType()),
    StructField('cost_price', DoubleType()),
    StructField('gross_margin', DoubleType()),
    StructField('margin_percentage', DoubleType()),
    StructField('competitor_price', DoubleType()),
    StructField('price_elasticity', DoubleType()),
    StructField('is_promoted', IntegerType()),
    StructField('promotion_discount_pct', DoubleType()),
    StructField('days_inventory', DoubleType()),
    StructField('stockout_risk', IntegerType())
])

# Read demand data
# Replace path with your actual location: /mnt/dsp/demand_sensing_data.csv
demand_raw = (
    spark.read
    .csv(
        'demand_sensing_data.csv',  # Local path for testing
        header=True,
        schema=demand_schema
    )
    .repartition(sc.defaultParallelism)
)

# Display sample data
display(demand_raw.limit(10))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Data Quality Validation

# COMMAND ----------

print(f"Total records: {demand_raw.count()}")
print(f"Date range: {demand_raw.select(f.min('date'), f.max('date')).collect()}")
print(f"Unique stores: {demand_raw.select('store_id').distinct().count()}")
print(f"Unique products: {demand_raw.select('product_id').distinct().count()}")
print(f"Unique categories: {demand_raw.select('product_category').distinct().count()}")

# Check for null values
print("\nNull value counts:")
demand_raw.select([f.count(f.when(f.col(c).isNull(), c)).alias(c) for c in demand_raw.columns]).show()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Data Transformation and Feature Engineering

# COMMAND ----------

# Convert date string to date type and add temporal features
demand_transformed = (
    demand_raw
    .withColumn('date', f.to_date(f.col('date'), 'yyyyMMdd'))
    .withColumn('year', f.year('date'))
    .withColumn('month', f.month('date'))
    .withColumn('quarter', f.quarter('date'))
    .withColumn('day_of_month', f.dayofmonth('date'))
    .withColumn('day_of_week', f.dayofweek('date'))  # 1=Sunday, 7=Saturday
    .withColumn('week_of_year', f.weekofyear('date'))
    .withColumn('is_weekend', f.when(f.col('day_of_week').isin(1, 7), 1).otherwise(0))
)

# Calculate revenue and key metrics
demand_with_metrics = (
    demand_transformed
    .withColumn('revenue', f.col('quantity_demanded') * f.col('current_price'))
    .withColumn('cogs', f.col('quantity_demanded') * f.col('cost_price'))
    .withColumn('sell_through_rate', 
                f.when(f.col('on_hand_inventory') > 0, 
                       f.col('quantity_demanded') / f.col('on_hand_inventory'))
                .otherwise(0))
    .withColumn('price_difference_competitor', f.col('current_price') - f.col('competitor_price'))
    .withColumn('price_ratio_competitor', f.col('current_price') / f.col('competitor_price'))
    .withColumn('promotion_flag', f.col('is_promoted'))
    .withColumn('effective_discount', 
                f.when(f.col('promotion_flag') == 1, f.col('promotion_discount_pct')).otherwise(0))
)

# Display transformed data
display(demand_with_metrics.limit(10))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Create Lag and Windowed Features for Time Series

# COMMAND ----------

# Define window specifications for lag features
window_spec = Window.partitionBy('store_id', 'product_id').orderBy('date')
window_7day = Window.partitionBy('store_id', 'product_id').orderBy('date').rangeBetween(-6, 0)
window_30day = Window.partitionBy('store_id', 'product_id').orderBy('date').rangeBetween(-29, 0)

# Create lag and rolling features
demand_lagged = (
    demand_with_metrics
    .withColumn('demand_lag_1', f.lag('quantity_demanded', 1).over(window_spec))
    .withColumn('demand_lag_7', f.lag('quantity_demanded', 7).over(window_spec))
    .withColumn('demand_lag_30', f.lag('quantity_demanded', 30).over(window_spec))
    .withColumn('demand_ma_7', f.avg('quantity_demanded').over(window_7day))
    .withColumn('demand_ma_30', f.avg('quantity_demanded').over(window_30day))
    .withColumn('price_lag_1', f.lag('current_price', 1).over(window_spec))
    .withColumn('revenue_lag_7', f.avg('revenue').over(window_7day))
    .withColumn('inventory_trend', 
                f.col('on_hand_inventory') - f.lag('on_hand_inventory', 1).over(window_spec))
    .withColumn('price_volatility_7day', 
                f.stddev('current_price').over(window_7day))
)

display(demand_lagged.limit(10))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7. Identify Anomalies and Data Quality Issues

# COMMAND ----------

# Flag anomalies
anomaly_detection = (
    demand_lagged
    .withColumn('is_zero_demand', f.when(f.col('quantity_demanded') == 0, 1).otherwise(0))
    .withColumn('is_zero_inventory', f.when(f.col('on_hand_inventory') == 0, 1).otherwise(0))
    .withColumn('is_high_stockout_risk', f.when(f.col('stockout_risk') == 1, 1).otherwise(0))
    .withColumn('is_excess_inventory', 
                f.when(f.col('days_inventory') > 60, 1).otherwise(0))
    .withColumn('is_price_anomaly',
                f.when(f.abs(f.col('current_price') - f.col('price_lag_1')) / f.col('price_lag_1') > 0.3, 1)
                .otherwise(0))
    .withColumn('is_demand_spike',
                f.when(f.col('quantity_demanded') > (f.col('demand_ma_7') + 2 * f.stddev('quantity_demanded').over(window_7day)), 1)
                .otherwise(0))
)

# Summary of anomalies
print("Anomaly Summary:")
anomaly_cols = ['is_zero_demand', 'is_zero_inventory', 'is_high_stockout_risk', 'is_excess_inventory', 'is_price_anomaly', 'is_demand_spike']
for col in anomaly_cols:
    count = anomaly_detection.filter(f.col(col) == 1).count()
    pct = (count / anomaly_detection.count()) * 100
    print(f"{col}: {count} records ({pct:.2f}%)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 8. Handle Missing Values in Lag Features

# COMMAND ----------

# For records at the beginning of time series, fill forward with available values
demand_imputed = (
    anomaly_detection
    .fillna({
        'demand_lag_1': 0,
        'demand_lag_7': 0,
        'demand_lag_30': 0,
        'price_lag_1': 0,
        'inventory_trend': 0,
        'price_volatility_7day': 0
    })
)

# For rolling averages, use last observation carried forward (LOCF)
demand_imputed = (
    demand_imputed
    .withColumn('demand_ma_7', 
                f.last('demand_ma_7', True).over(Window.partitionBy('store_id', 'product_id').orderBy('date').rowsBetween(Window.unboundedPreceding, Window.currentRow)))
    .withColumn('demand_ma_30',
                f.last('demand_ma_30', True).over(Window.partitionBy('store_id', 'product_id').orderBy('date').rowsBetween(Window.unboundedPreceding, Window.currentRow)))
)

display(demand_imputed.limit(10))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 9. Create Category-Level Aggregations

# COMMAND ----------

# Calculate category-level metrics for competitive analysis
category_metrics = (
    demand_imputed
    .groupBy('date', 'store_id', 'product_category')
    .agg(
        f.count('product_id').alias('num_products'),
        f.sum('quantity_demanded').alias('category_total_demand'),
        f.sum('revenue').alias('category_total_revenue'),
        f.avg('current_price').alias('category_avg_price'),
        f.avg('margin_percentage').alias('category_avg_margin'),
        f.avg('competitor_price').alias('category_avg_competitor_price'),
        f.sum(f.when(f.col('promotion_flag') == 1, 1).otherwise(0)).alias('promoted_items_count')
    )
)

display(category_metrics.limit(10))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 10. Create Product-Category Dimension

# COMMAND ----------

# Extract product master data
product_dimension = (
    demand_imputed
    .select('product_id', 'product_category')
    .distinct()
    .withColumn('product_lifecycle_stage', 
                f.when(f.rand() < 0.3, 'New')
                .when(f.rand() < 0.7, 'Mature')
                .otherwise('Declining'))
)

display(product_dimension)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 11. Persist Cleansed and Prepared Data

# COMMAND ----------

# Save the main demand preparation table
(
    demand_imputed
    .repartition(sc.defaultParallelism)
    .write
    .format('delta')
    .mode('overwrite')
    .option('overwriteSchema', 'true')
    .saveAsTable('dsp.demand_prepared')
)

print("✓ Saved: dsp.demand_prepared")

# Save category metrics
(
    category_metrics
    .write
    .format('delta')
    .mode('overwrite')
    .option('overwriteSchema', 'true')
    .saveAsTable('dsp.category_metrics')
)

print("✓ Saved: dsp.category_metrics")

# Save product dimension
(
    product_dimension
    .write
    .format('delta')
    .mode('overwrite')
    .option('overwriteSchema', 'true')
    .saveAsTable('dsp.product_dimension')
)

print("✓ Saved: dsp.product_dimension")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 12. Generate Data Quality Report

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT 
# MAGIC   COUNT(*) as total_records,
# MAGIC   COUNT(DISTINCT date) as distinct_dates,
# MAGIC   COUNT(DISTINCT store_id) as distinct_stores,
# MAGIC   COUNT(DISTINCT product_id) as distinct_products,
# MAGIC   MIN(date) as start_date,
# MAGIC   MAX(date) as end_date,
# MAGIC   ROUND(AVG(quantity_demanded), 2) as avg_daily_demand,
# MAGIC   ROUND(AVG(revenue), 2) as avg_daily_revenue,
# MAGIC   ROUND(AVG(current_price), 2) as avg_price,
# MAGIC   ROUND(AVG(margin_percentage), 2) as avg_margin_pct
# MAGIC FROM dsp.demand_prepared

# COMMAND ----------

# MAGIC %md
# MAGIC ## Data Preparation Complete!
# MAGIC 
# MAGIC ✓ Data loaded and validated  
# MAGIC ✓ Temporal features created  
# MAGIC ✓ Lag and rolling features engineered  
# MAGIC ✓ Anomalies identified and flagged  
# MAGIC ✓ Missing values imputed  
# MAGIC ✓ Category metrics aggregated  
# MAGIC ✓ Master dimensions created  
# MAGIC 
# MAGIC **Next Step:** Run DSP-02-Demand-Forecasting notebook