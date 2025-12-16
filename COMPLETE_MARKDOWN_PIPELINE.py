
# ============================================================================
# MARKDOWN OPTIMIZATION USE CASE - COMPLETE END-TO-END PIPELINE
# ============================================================================
# Demonstrates full workflow with synthetic data for real-world application
# ============================================================================

import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from scipy.optimize import minimize
import warnings
warnings.filterwarnings('ignore')

print("=" * 80)
print("MARKDOWN OPTIMIZATION USE CASE - COMPLETE PIPELINE")
print("=" * 80)

# ============================================================================
# STEP 1: LOAD ALL DATA
# ============================================================================
print("\nStep 1: Loading Data...")

inventory_df = pd.read_csv('osa_raw_data.csv')
vendor_df = pd.read_csv('vendor_leadtime_info.csv')
product_master = pd.read_csv('product_master.csv')
historical_markdowns = pd.read_csv('historical_markdowns.csv')
promotional_calendar = pd.read_csv('promotional_calendar.csv')
competitor_pricing = pd.read_csv('competitor_pricing.csv')
store_master = pd.read_csv('store_master.csv')

print(f"✓ Inventory data: {len(inventory_df)} records")
print(f"✓ Product master: {len(product_master)} SKUs")
print(f"✓ Historical markdowns: {len(historical_markdowns)} events")
print(f"✓ Promotions: {len(promotional_calendar)} events")
print(f"✓ Competitor pricing: {len(competitor_pricing)} records")
print(f"✓ Store master: {len(store_master)} stores")

# ============================================================================
# STEP 2: CREATE FEATURES FROM INVENTORY DATA
# ============================================================================
print("\nStep 2: Feature Engineering...")

inventory_df['date'] = pd.to_datetime(inventory_df['date'], format='%Y%m%d')
inventory_df = inventory_df.sort_values(['store_id', 'sku', 'date']).reset_index(drop=True)

# Time series features
inventory_df['sales_7day_ma'] = inventory_df.groupby(['store_id', 'sku'])['total_sales_units'].transform(
    lambda x: x.rolling(window=7, min_periods=1).mean()
)
inventory_df['sales_30day_ma'] = inventory_df.groupby(['store_id', 'sku'])['total_sales_units'].transform(
    lambda x: x.rolling(window=30, min_periods=1).mean()
)

# Shelf utilization
inventory_df['shelf_utilization_ratio'] = (
    inventory_df['on_hand_inventory_units'] / (inventory_df['shelf_capacity'] + 1)
)

# Days to deplete
inventory_df['days_to_deplete'] = np.where(
    inventory_df['sales_7day_ma'] > 0,
    inventory_df['on_hand_inventory_units'] / inventory_df['sales_7day_ma'],
    999
)

# Sales momentum
inventory_df['sales_momentum'] = (
    (inventory_df['sales_7day_ma'] - inventory_df['sales_30day_ma']) / 
    (inventory_df['sales_30day_ma'] + 1)
)

# Inventory pipeline ratio
inventory_df['pipeline_ratio'] = (
    inventory_df['inventory_pipeline'] / (inventory_df['on_hand_inventory_units'] + 1)
)

# Create target: slow-moving indicator
inventory_df['is_slow_moving'] = (
    inventory_df['sales_30day_ma'] < inventory_df['sales_30day_ma'].quantile(0.25)
).astype(int)

print(f"✓ Generated 6 time-series features")
print(f"✓ Slow-moving SKUs identified: {inventory_df['is_slow_moving'].sum()} ({inventory_df['is_slow_moving'].sum() / len(inventory_df) * 100:.1f}%)")

# ============================================================================
# STEP 3: TRAIN LIFECYCLE PREDICTION MODEL
# ============================================================================
print("\nStep 3: Training Slow-Moving Inventory Predictor...")

feature_cols = ['sales_7day_ma', 'sales_30day_ma', 'sales_momentum', 
                'shelf_utilization_ratio', 'days_to_deplete', 'pipeline_ratio']

# Prepare data
valid_data = inventory_df[inventory_df[feature_cols].notna().all(axis=1)].copy()
X = valid_data[feature_cols]
y = valid_data['is_slow_moving']

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Scale features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Train model
lifecycle_model = GradientBoostingClassifier(n_estimators=100, max_depth=5, random_state=42)
lifecycle_model.fit(X_train_scaled, y_train)

train_score = lifecycle_model.score(X_train_scaled, y_train)
test_score = lifecycle_model.score(X_test_scaled, y_test)

print(f"✓ Model trained")
print(f"  - Train Accuracy: {train_score:.3f}")
print(f"  - Test Accuracy: {test_score:.3f}")

# Get feature importance
importances = pd.DataFrame({
    'feature': feature_cols,
    'importance': lifecycle_model.feature_importances_
}).sort_values('importance', ascending=False)

print(f"\nTop 3 Features for Slow-Moving Detection:")
print(importances.head(3).to_string(index=False))

# ============================================================================
# STEP 4: ESTIMATE PRICE ELASTICITY
# ============================================================================
print("\nStep 4: Estimating Price Elasticity...")

# Calculate elasticity by category
elasticity_by_category = {}

for category in historical_markdowns['category'].unique():
    cat_data = historical_markdowns[historical_markdowns['category'] == category].copy()

    # Calculate elasticity = % change in qty / % change in price
    cat_data['price_change_pct'] = (cat_data['markdown_price'] - cat_data['original_price']) / cat_data['original_price']
    cat_data['qty_change_pct'] = (cat_data['markdown_quantity_sold'] - cat_data['base_quantity_sold']) / cat_data['base_quantity_sold']

    # Filter valid data
    valid = (cat_data['price_change_pct'] != 0) & (cat_data['qty_change_pct'].notna())
    if len(cat_data[valid]) > 5:
        X_elast = cat_data[valid]['price_change_pct'].values.reshape(-1, 1)
        y_elast = cat_data[valid]['qty_change_pct'].values

        # Simple linear regression
        slope = np.polyfit(X_elast.flatten(), y_elast, 1)[0]
        elasticity_by_category[category] = slope
    else:
        elasticity_by_category[category] = -1.2  # Default

print(f"✓ Price Elasticity Estimates by Category:")
for cat, elast in elasticity_by_category.items():
    print(f"  - {cat}: {elast:.2f}")

# ============================================================================
# STEP 5: IDENTIFY CLEARANCE CANDIDATES
# ============================================================================
print("\nStep 5: Identifying Clearance Candidates...")

# Get latest data per store-sku
latest_data = inventory_df.sort_values('date').groupby(['store_id', 'sku']).tail(1).copy()

# Predict slow-moving probability
latest_data['clearance_prob'] = lifecycle_model.predict_proba(
    scaler.transform(latest_data[feature_cols])
)[:, 1]

# Get candidates (prob > 0.6)
candidates = latest_data[latest_data['clearance_prob'] > 0.6].copy()
candidates = candidates.sort_values('clearance_prob', ascending=False)

print(f"✓ Total clearance candidates: {len(candidates)}")
print(f"✓ Total inventory at risk: {candidates['on_hand_inventory_units'].sum():,.0f} units")
print(f"\nTop 10 Clearance Candidates:")
print(candidates[['store_id', 'sku', 'on_hand_inventory_units', 'sales_7day_ma', 'clearance_prob']].head(10).to_string(index=False))

# ============================================================================
# STEP 6: MARKDOWN OPTIMIZATION
# ============================================================================
print("\nStep 6: Running Markdown Optimization Engine...")

def optimize_markdown(store_id, sku, on_hand_inventory, sales_7day_ma, category, current_price, unit_cost, elasticity):
    """Calculate optimal markdown price"""

    # Current situation
    current_quantity = int(sales_7day_ma)
    max(5, current_quantity)  # Minimum 5 units

    # Constraints
    min_margin_pct = 0.15
    max_discount_pct = 0.35

    # Objective: maximize margin dollars
    def objective(discount_pct):
        new_price = current_price * (1 - discount_pct[0])
        margin_per_unit = new_price - unit_cost

        if elasticity != 0:
            price_elasticity_change = discount_pct[0] / (1 - discount_pct[0] + 0.001)
            demand_uplift = (1 + elasticity * price_elasticity_change) ** (1 / elasticity)
        else:
            demand_uplift = 1.0

        new_quantity = current_quantity * demand_uplift
        total_margin = new_quantity * margin_per_unit

        return -total_margin  # Negative for minimization

    # Constraints
    def margin_constraint(discount_pct):
        new_price = current_price * (1 - discount_pct[0])
        return ((new_price - unit_cost) / (new_price + 0.001)) - min_margin_pct

    constraints = [{'type': 'ineq', 'fun': margin_constraint}]
    bounds = [(0, max_discount_pct)]
    x0 = np.array([0.20])  # Initial guess: 20% discount

    result = minimize(objective, x0, method='SLSQP', bounds=bounds, constraints=constraints)

    if result.success:
        optimal_discount = result.x[0]
    else:
        optimal_discount = 0.0

    # Calculate metrics
    new_price = current_price * (1 - optimal_discount)
    if elasticity != 0:
        price_change_pct = optimal_discount / (1 - optimal_discount + 0.001)
        demand_uplift = (1 + elasticity * price_change_pct) ** (1 / elasticity)
    else:
        demand_uplift = 1.0

    new_quantity = current_quantity * demand_uplift
    current_margin = current_quantity * (current_price - unit_cost)
    new_margin = new_quantity * (new_price - unit_cost)

    return {
        'store_id': store_id,
        'sku': sku,
        'current_price': current_price,
        'optimal_price': new_price,
        'discount_pct': optimal_discount * 100,
        'current_quantity': current_quantity,
        'predicted_quantity': new_quantity,
        'quantity_uplift_pct': (new_quantity - current_quantity) / (current_quantity + 0.001) * 100,
        'current_margin_dollars': current_margin,
        'predicted_margin_dollars': new_margin,
        'margin_improvement_dollars': new_margin - current_margin,
        'margin_improvement_pct': (new_margin - current_margin) / (current_margin + 0.001) * 100,
        'clearance_probability': 0  # Will fill below
    }

# Run optimization for top candidates
recommendations = []
for idx, (_, row) in enumerate(candidates.head(20).iterrows()):
    sku_info = product_master[product_master['sku'] == row['sku']].iloc[0]
    elasticity = elasticity_by_category.get(sku_info['category'], -1.2)

    rec = optimize_markdown(
        store_id=row['store_id'],
        sku=row['sku'],
        on_hand_inventory=row['on_hand_inventory_units'],
        sales_7day_ma=row['sales_7day_ma'],
        category=sku_info['category'],
        current_price=sku_info['current_price'],
        unit_cost=sku_info['unit_cost'],
        elasticity=elasticity
    )
    rec['clearance_probability'] = row['clearance_prob']
    recommendations.append(rec)

recommendations_df = pd.DataFrame(recommendations)

print(f"✓ Generated {len(recommendations_df)} markdown recommendations")
print(f"\nTop 10 Markdown Recommendations:")
display_cols = ['store_id', 'sku', 'current_price', 'optimal_price', 'discount_pct', 
                'margin_improvement_dollars', 'clearance_probability']
print(recommendations_df[display_cols].head(10).to_string(index=False))

# ============================================================================
# STEP 7: SUMMARY METRICS
# ============================================================================
print("\n" + "=" * 80)
print("MARKDOWN OPTIMIZATION SUMMARY METRICS")
print("=" * 80)

total_current_margin = recommendations_df['current_margin_dollars'].sum()
total_new_margin = recommendations_df['predicted_margin_dollars'].sum()
total_uplift = total_new_margin - total_current_margin

print(f"\nFinancial Impact (20 Top Candidates):")
print(f"  Current Total Margin:        ${total_current_margin:,.0f}")
print(f"  Predicted Total Margin:      ${total_new_margin:,.0f}")
print(f"  Total Margin Improvement:    ${total_uplift:,.0f} ({total_uplift/total_current_margin*100:.1f}%)")
print(f"\nPricing Strategy:")
print(f"  Average Discount:            {recommendations_df['discount_pct'].mean():.1f}%")
print(f"  Average Quantity Uplift:     {recommendations_df['quantity_uplift_pct'].mean():.1f}%")
print(f"\nClearance Performance:")
print(f"  High Risk Items (prob > 0.8): {len(candidates[candidates['clearance_prob'] > 0.8])}")
print(f"  Medium Risk Items (0.6-0.8):  {len(candidates[(candidates['clearance_prob'] >= 0.6) & (candidates['clearance_prob'] <= 0.8)])}")

# Save recommendations
recommendations_df.to_csv('markdown_recommendations.csv', index=False)
print(f"\n✓ Recommendations saved to: markdown_recommendations.csv")

print("\n" + "=" * 80)
print("✅ MARKDOWN OPTIMIZATION PIPELINE COMPLETE")
print("=" * 80)
