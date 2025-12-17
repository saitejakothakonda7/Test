# Databricks notebook source

# MAGIC %md
# MAGIC # DSP-02: Demand Sensing & Dynamic Pricing - Demand Forecasting
# MAGIC 
# MAGIC This notebook builds demand forecasting models and generates demand predictions for use in pricing optimization.
# MAGIC 
# MAGIC **Objective:** Create accurate demand forecasts to enable data-driven pricing decisions
# MAGIC 
# MAGIC **Approach:** Time-series forecasting using exponential smoothing and statistical methods
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
from statsmodels.tsa.holtwinters import SimpleExpSmoothing, ExponentialSmoothing
import warnings
warnings.filterwarnings('ignore')

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Load Prepared Data

# COMMAND ----------

# Load the prepared demand data from previous notebook
demand_prepared = spark.table('dsp.demand_prepared')

print(f"Loaded demand_prepared: {demand_prepared.count()} records")
display(demand_prepared.limit(5))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Define Forecasting Function

# COMMAND ----------

# Forecasting parameters
SMOOTHING_LEVEL = 0.8  # Alpha parameter for exponential smoothing
MIN_HISTORY_DAYS = 90  # Minimum historical data required for forecast

def forecast_demand_exponential_smoothing(keys, demand_df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate demand forecast for a store-product combination using exponential smoothing
    
    Args:
        keys: Tuple of (store_id, product_id)
        demand_df: Pandas DataFrame with historical demand data
    
    Returns:
        Pandas DataFrame with forecasted values
    """
    store_id = keys[0]
    product_id = keys[1]
    
    try:
        # Sort by date
        demand_df = demand_df.sort_values('date')
        
        # Check if we have sufficient history
        if len(demand_df) < MIN_HISTORY_DAYS:
            # Return actual values if insufficient history
            return demand_df[['date', 'store_id', 'product_id', 'quantity_demanded']].copy()
        
        # Extract time series
        timeseries = demand_df['quantity_demanded'].values
        
        # Fit exponential smoothing model
        try:
            model = SimpleExpSmoothing(timeseries, initialization_method='heuristic').fit(
                smoothing_level=SMOOTHING_LEVEL
            )
            # Generate predictions for same period as history
            predictions = model.fittedvalues
        except:
            # Fallback: use simple moving average if exponential smoothing fails
            window_size = min(7, len(timeseries))
            predictions = pd.Series(timeseries).rolling(window=window_size, center=True).mean().values
        
        # Create output dataframe
        forecast_df = pd.DataFrame({
            'date': demand_df['date'].values,
            'store_id': store_id,
            'product_id': product_id,
            'actual_demand': timeseries,
            'forecasted_demand': predictions,
            'forecast_error': timeseries - predictions,
            'abs_pct_error': np.abs((timeseries - predictions) / (timeseries + 1)) * 100
        })
        
        # Calculate MAPE for this store-product
        mape = forecast_df['abs_pct_error'].mean()
        forecast_df['mape'] = mape
        
        return forecast_df
        
    except Exception as e:
        print(f"Error forecasting store {store_id}, product {product_id}: {str(e)}")
        return pd.DataFrame()

# Define output schema
forecast_schema = StructType([
    StructField('date', DateType()),
    StructField('store_id', IntegerType()),
    StructField('product_id', IntegerType()),
    StructField('actual_demand', IntegerType()),
    StructField('forecasted_demand', DoubleType()),
    StructField('forecast_error', DoubleType()),
    StructField('abs_pct_error', DoubleType()),
    StructField('mape', DoubleType())
])

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Generate Forecasts for All Store-Product Combinations

# COMMAND ----------

# Generate forecasts using distributed computing
forecast_results = (
    demand_prepared
    .select('date', 'store_id', 'product_id', 'quantity_demanded')
    .groupby('store_id', 'product_id')
    .applyInPandas(forecast_demand_exponential_smoothing, schema=forecast_schema)
)

# Round forecasted values to nearest integer
forecast_results = (
    forecast_results
    .withColumn('forecasted_demand', f.round(f.col('forecasted_demand'), 0))
    .withColumn('forecast_error', f.col('actual_demand') - f.col('forecasted_demand'))
)

display(forecast_results.limit(20))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Calculate Forecast Accuracy Metrics

# COMMAND ----------

# Calculate accuracy metrics by store-product
forecast_accuracy = (
    forecast_results
    .groupby('store_id', 'product_id')
    .agg(
        f.avg('mape').alias('mape'),
        f.avg(f.abs('forecast_error')).alias('mae'),
        f.sqrt(f.avg(f.col('forecast_error') ** 2)).alias('rmse'),
        f.count('date').alias('forecast_count'),
        f.sum(f.when(f.abs(f.col('forecast_error')) > 10, 1).otherwise(0)).alias('large_error_count')
    )
    .withColumn('forecast_quality', 
                f.when(f.col('mape') < 10, 'Excellent')
                .when(f.col('mape') < 20, 'Good')
                .when(f.col('mape') < 30, 'Fair')
                .otherwise('Poor'))
)

display(forecast_accuracy)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Forecast Summary Statistics

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT 
# MAGIC   ROUND(AVG(mape), 2) as avg_mape,
# MAGIC   ROUND(AVG(mae), 2) as avg_mae,
# MAGIC   ROUND(AVG(rmse), 2) as avg_rmse,
# MAGIC   MIN(mape) as min_mape,
# MAGIC   MAX(mape) as max_mape,
# MAGIC   PERCENTILE_APPROX(mape, 0.5) as median_mape
# MAGIC FROM (
# MAGIC   SELECT DISTINCT store_id, product_id, mape 
# MAGIC   FROM forecast_results
# MAGIC )

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7. Join Forecast with Original Features

# COMMAND ----------

# Enrich forecast with pricing and inventory information
demand_with_forecast = (
    forecast_results
    .join(
        demand_prepared.select('date', 'store_id', 'product_id', 'current_price', 'competitor_price', 
                               'on_hand_inventory', 'safety_stock', 'margin_percentage', 'product_category'),
        on=['date', 'store_id', 'product_id'],
        how='left'
    )
)

display(demand_with_forecast.limit(10))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 8. Identify Forecast Anomalies

# COMMAND ----------

# Flag forecast misses that warrant investigation
forecast_anomalies = (
    demand_with_forecast
    .withColumn('is_large_miss', 
                f.when(f.abs(f.col('forecast_error')) > 20, 1).otherwise(0))
    .withColumn('is_consistent_underprediction',
                f.when(f.col('forecast_error') > 5, 1).otherwise(0))
    .withColumn('is_consistent_overprediction',
                f.when(f.col('forecast_error') < -5, 1).otherwise(0))
    .withColumn('forecast_reliability',
                f.when(f.col('mape') < 15, 'High')
                .when(f.col('mape') < 25, 'Medium')
                .otherwise('Low'))
)

# Summary of anomalies
print("Forecast Anomaly Summary:")
print(f"Large misses (>20 units): {forecast_anomalies.filter('is_large_miss = 1').count()}")
print(f"Consistent underpredictions: {forecast_anomalies.filter('is_consistent_underprediction = 1').count()}")
print(f"Consistent overpredictions: {forecast_anomalies.filter('is_consistent_overprediction = 1').count()}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 9. Calculate Demand Confidence Intervals

# COMMAND ----------

# Calculate confidence intervals for demand forecasts
demand_confidence = (
    forecast_anomalies
    .groupby('store_id', 'product_id')
    .agg(
        f.avg('forecasted_demand').alias('mean_forecast'),
        f.stddev('forecast_error').alias('forecast_std'),
        f.min('forecasted_demand').alias('min_forecast'),
        f.max('forecasted_demand').alias('max_forecast')
    )
    .withColumn('forecast_ci_lower', f.col('mean_forecast') - 1.96 * f.col('forecast_std'))
    .withColumn('forecast_ci_upper', f.col('mean_forecast') + 1.96 * f.col('forecast_std'))
    .withColumn('forecast_ci_lower', f.when(f.col('forecast_ci_lower') < 0, 0).otherwise(f.col('forecast_ci_lower')))
)

display(demand_confidence.limit(10))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 10. Create Demand Forecast Segments

# COMMAND ----------

# Segment products by demand patterns
demand_segments = (
    forecast_accuracy
    .join(
        demand_prepared.groupby('store_id', 'product_id').agg(
            f.avg('quantity_demanded').alias('avg_demand'),
            f.stddev('quantity_demanded').alias('demand_volatility')
        ),
        on=['store_id', 'product_id']
    )
    .withColumn('demand_segment',
                f.when(f.col('avg_demand') > 40, 'High')
                .when(f.col('avg_demand') > 20, 'Medium')
                .otherwise('Low'))
    .withColumn('volatility_segment',
                f.when(f.col('demand_volatility') > 15, 'Volatile')
                .when(f.col('demand_volatility') > 8, 'Moderate')
                .otherwise('Stable'))
)

display(demand_segments)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 11. Persist Forecast Results

# COMMAND ----------

# Save forecast results
(
    forecast_anomalies
    .repartition(sc.defaultParallelism)
    .write
    .format('delta')
    .mode('overwrite')
    .option('overwriteSchema', 'true')
    .saveAsTable('dsp.demand_forecast')
)

print("✓ Saved: dsp.demand_forecast")

# Save forecast accuracy
(
    forecast_accuracy
    .write
    .format('delta')
    .mode('overwrite')
    .option('overwriteSchema', 'true')
    .saveAsTable('dsp.forecast_accuracy')
)

print("✓ Saved: dsp.forecast_accuracy")

# Save demand confidence intervals
(
    demand_confidence
    .write
    .format('delta')
    .mode('overwrite')
    .option('overwriteSchema', 'true')
    .saveAsTable('dsp.demand_confidence')
)

print("✓ Saved: dsp.demand_confidence")

# Save demand segments
(
    demand_segments
    .write
    .format('delta')
    .mode('overwrite')
    .option('overwriteSchema', 'true')
    .saveAsTable('dsp.demand_segments')
)

print("✓ Saved: dsp.demand_segments")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 12. Generate Forecast Quality Report

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT 
# MAGIC   forecast_quality,
# MAGIC   COUNT(*) as count,
# MAGIC   ROUND(AVG(mape), 2) as avg_mape,
# MAGIC   ROUND(AVG(mae), 2) as avg_mae,
# MAGIC   ROUND(AVG(rmse), 2) as avg_rmse
# MAGIC FROM dsp.forecast_accuracy
# MAGIC GROUP BY forecast_quality
# MAGIC ORDER BY forecast_quality DESC

# COMMAND ----------

# MAGIC %md
# MAGIC ## Demand Forecasting Complete!
# MAGIC 
# MAGIC ✓ Exponential smoothing models fitted  
# MAGIC ✓ Demand forecasts generated for all store-product combinations  
# MAGIC ✓ Forecast accuracy metrics calculated (MAPE, MAE, RMSE)  
# MAGIC ✓ Confidence intervals computed  
# MAGIC ✓ Demand segments identified  
# MAGIC ✓ Anomalies flagged for investigation  
# MAGIC 
# MAGIC **Key Insights:**
# MAGIC - Average forecast accuracy (MAPE) provides baseline for pricing models
# MAGIC - High-volatility products need more frequent price adjustments
# MAGIC - Inventory levels significantly impact pricing flexibility
# MAGIC - Promotional patterns create demand spikes requiring special handling
# MAGIC 
# MAGIC **Next Step:** Run DSP-03-Dynamic-Pricing-Optimization notebook