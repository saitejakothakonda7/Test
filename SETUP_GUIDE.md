# Setup and Installation Guide for DSP Accelerator

## Overview
This guide provides step-by-step instructions to deploy the Demand Sensing & Dynamic Pricing (DSP) accelerator in your Databricks environment.

## Prerequisites

### 1. Databricks Environment Requirements
- **Databricks Workspace** - Standard or Premium tier
- **Cluster Configuration**:
  - Runtime: 12.2+ (supports PySpark 3.3+)
  - Python 3.9+
  - Minimum: 4 cores, 16GB RAM (Standard_DS4_v2 or equivalent)
  - Recommended: 8 cores, 32GB RAM for production workloads

### 2. Required Libraries
The following libraries are included in default Databricks runtime:
- PySpark
- Pandas
- NumPy
- Delta Lake

Additional library installation:
```bash
# In Databricks cluster, go to Cluster -> Libraries -> Install New
# PyPI packages to install:
statsmodels==0.14.0
scikit-learn==1.3.0
```

### 3. Data Setup

#### Option A: Using Provided Synthetic Data (Recommended for Demo)

1. **Upload Data File**
   - Download `demand_sensing_data.csv` (18,250 records, ~2.5MB)
   - In Databricks workspace: Data → Add Data
   - Upload the CSV file
   - Note the path (e.g., `/Filestore/shared_uploads/demand_sensing_data.csv`)

2. **Create Mount Point** (Optional but recommended)
   ```python
   # In a Databricks notebook cell:
   dbutils.fs.mount(
       source="wasbs://dsp@[storage_account].blob.core.windows.net/data",
       mount_point="/mnt/dsp",
       extra_configs={"fs.azure.account.key.[storage_account].blob.core.windows.net":"[access_key]"}
   )
   # Then copy data to mount
   dbutils.fs.cp("file:/path/to/demand_sensing_data.csv", "/mnt/dsp/demand_sensing_data.csv")
   ```

#### Option B: Using Your Own Data

Prepare a CSV file with the following schema:

```
date,store_id,product_id,product_category,quantity_demanded,on_hand_inventory,
safety_stock,current_price,base_price,cost_price,gross_margin,margin_percentage,
competitor_price,price_elasticity,is_promoted,promotion_discount_pct,
days_inventory,stockout_risk
```

**Field Requirements:**
- `date`: YYYYMMDD format (integer or string)
- `store_id`: Unique store identifier (integer)
- `product_id`: Product SKU (integer)
- `product_category`: Category name (string)
- `quantity_demanded`: Units sold (integer, ≥0)
- `on_hand_inventory`: Current stock (integer, ≥0)
- `safety_stock`: Minimum stock level (integer)
- `current_price`: Selling price ($, float)
- `base_price`: Reference price ($, float)
- `cost_price`: Acquisition cost ($, float)
- `gross_margin`: Profit per unit ($, float)
- `margin_percentage`: Profit margin (%, float)
- `competitor_price`: Competitor selling price ($, float)
- `price_elasticity`: Demand elasticity coefficient (float, 0.5-2.0)
- `is_promoted`: Promotion flag (0 or 1)
- `promotion_discount_pct`: Discount percentage (%, float)
- `days_inventory`: Days supply on hand (float)
- `stockout_risk`: Risk flag (0 or 1)

## Installation Steps

### Step 1: Create Workspace Notebooks

1. In Databricks workspace, create a new folder: `/Repos/dsp-accelerator/`

2. Import the three notebooks:
   - `DSP_01_Data_Preparation.py`
   - `DSP_02_Demand_Forecasting.py`
   - `DSP_03_Pricing_Optimization.py`

   **Method 1: Upload Files**
   - Workspace → Create → File → Upload notebook
   - Select each .py file
   - Place in `/Repos/dsp-accelerator/`

   **Method 2: Copy-Paste**
   - Create new notebook for each
   - Copy content from provided files
   - Name accordingly

### Step 2: Update Data Path References

In DSP-01 notebook, find this line:
```python
demand_raw = (
    spark.read
    .csv(
        'demand_sensing_data.csv',  # UPDATE THIS PATH
        header=True,
        schema=demand_schema
    )
)
```

Replace with your actual data path:
```python
# Option A: Local file system
'dbfs:/FileStore/shared_uploads/demand_sensing_data.csv'

# Option B: Mounted storage
'/mnt/dsp/demand_sensing_data.csv'

# Option C: Cloud storage (ADLS, S3)
'abfss://container@account.dfs.core.windows.net/demand_sensing_data.csv'
```

### Step 3: Create Databricks Cluster

1. Go to **Compute** → **Create Cluster**

2. Configure:
   - **Cluster Name**: `dsp-accelerator`
   - **Cluster Mode**: Single Node or Multi-Node
   - **Databricks Runtime**: 12.2 LTS or newer
   - **Worker Type**: Standard_D4s_v3 (minimum)
   - **Min/Max Workers**: 2/4 (adjust per your data volume)
   - **Driver Type**: Same as worker type

3. **Install Libraries**:
   - Click cluster → Libraries → Install New → PyPI
   - Type `statsmodels`
   - Install

### Step 4: Execute Notebooks Sequentially

**Important: Run in this exact order:**

1. **Run DSP-01: Data Preparation**
   - Open notebook
   - Attach to cluster
   - Click "Run All"
   - Monitor progress (typically 5-10 minutes)
   - Check for green checkmarks ✓

2. **Run DSP-02: Demand Forecasting**
   - After DSP-01 completes successfully
   - Open notebook
   - Run All
   - Monitor progress (typically 10-15 minutes)
   - Verify forecast accuracy (MAPE < 25%)

3. **Run DSP-03: Pricing Optimization**
   - After DSP-02 completes successfully
   - Open notebook
   - Run All
   - Review recommendations
   - Check exception alerts

## Verification Checklist

After running all notebooks, verify success:

```sql
-- Check database and tables created
SHOW DATABASES LIKE 'dsp';
USE dsp;
SHOW TABLES;

-- Verify data in each table
SELECT COUNT(*) FROM dsp.demand_prepared;
SELECT COUNT(*) FROM dsp.demand_forecast;
SELECT COUNT(*) FROM dsp.pricing_recommendations;

-- Check data quality
SELECT 
  COUNT(*) as total_records,
  COUNT(DISTINCT store_id) as stores,
  COUNT(DISTINCT product_id) as products,
  MIN(date) as start_date,
  MAX(date) as end_date
FROM dsp.demand_forecast;

-- Review pricing recommendations
SELECT 
  recommendation_priority,
  COUNT(*) as count,
  ROUND(AVG(price_change_pct), 2) as avg_price_change,
  ROUND(AVG(revenue_lift_pct), 2) as avg_revenue_lift
FROM dsp.pricing_recommendations
GROUP BY recommendation_priority;
```

## Troubleshooting

### Issue: "Table not found" error in DSP-02 or DSP-03

**Solution:**
- Ensure DSP-01 completed successfully (no red error boxes)
- Check that all tables were created: `SHOW TABLES IN dsp;`
- Re-run DSP-01 if needed before proceeding

### Issue: "OutOfMemoryError" during execution

**Solution:**
- Increase cluster memory: stop cluster, resize to larger instance type
- Reduce data volume for testing: filter to fewer dates or stores
- Check for long-running jobs: go to Spark UI → Executors

### Issue: "FileNotFoundError" when loading CSV

**Solution:**
- Verify file exists: `dbutils.fs.ls('path/to/file')`
- Check path spelling and case sensitivity
- Ensure file format is valid CSV with headers
- Try with full DBFS path: `dbfs:/path/to/file`

### Issue: "Module not found: statsmodels"

**Solution:**
- Go to cluster → Libraries → Install New → PyPI
- Type `statsmodels` and install
- Wait for installation to complete
- Restart cluster or notebook

## Performance Optimization

### For Large Datasets (>10M records)

1. **Increase Cluster Size**:
   - Use 8-16 worker nodes
   - Use memory-optimized instance types (D-series)

2. **Partition Data**:
   ```python
   # Add to end of DSP-01
   spark.sql("""
   ALTER TABLE dsp.demand_prepared 
   SET TBLPROPERTIES ('delta.columnMapping.mode'='name')
   """)
   ```

3. **Optimize Delta Format**:
   ```python
   # After writing tables
   spark.sql("OPTIMIZE dsp.demand_prepared")
   spark.sql("OPTIMIZE dsp.demand_forecast")
   spark.sql("OPTIMIZE dsp.pricing_recommendations")
   ```

### For Production Deployment

1. **Schedule Jobs**:
   - Go to Workflows → Create new job
   - Select "Notebook task"
   - Set notebook path: `/Repos/dsp-accelerator/DSP_01_Data_Preparation`
   - Schedule: Daily/Weekly (based on data update frequency)

2. **Set Up Alerts**:
   - Configure email notifications on job failure
   - Set up dashboard to monitor metrics

3. **Access Control**:
   - Set folder permissions: Workspace → dsp-accelerator → Permissions
   - Grant access to relevant users/groups

## Next Steps

1. **Explore Results**:
   - Create dashboard with pricing recommendations
   - Build SQL queries for business intelligence
   - Export results to Power BI or Tableau

2. **Customize for Your Business**:
   - Adjust thresholds in optimization functions
   - Add additional features specific to your products
   - Integrate with your pricing system

3. **Integrate with External Systems**:
   - Export recommendations to CSV
   - API integration with POS systems
   - Real-time pricing updates

## Support Resources

- **Databricks Documentation**: https://docs.databricks.com/
- **PySpark Documentation**: https://spark.apache.org/docs/latest/api/python/
- **StatsModels Documentation**: https://www.statsmodels.org/

## Contact & Feedback

For questions or issues:
- Review notebook comments and inline documentation
- Check Databricks cluster logs: Compute → cluster → Logs
- Refer to DSP_README.md for detailed use case information

---

**Version**: 1.0  
**Last Updated**: December 2024  
**Compatibility**: Databricks Runtime 12.2+, PySpark 3.3+