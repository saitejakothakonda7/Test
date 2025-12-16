# MARKDOWN OPTIMIZATION USE CASE - Python Implementation
# Dynamic Markdown Optimization & Inventory Clearance Prediction
# Author: AI Retail Optimization Team
# Date: December 2025

import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from scipy.optimize import minimize
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# PART 1: DATA PREPARATION & FEATURE ENGINEERING
# ============================================================================

class MarkdownDataPreparation:
    """
    Prepare inventory and sales data for markdown optimization
    """
    
    def __init__(self, inventory_df, vendor_df):
        self.inventory_df = inventory_df.copy()
        self.vendor_df = vendor_df.copy()
        
    def create_time_series_features(self):
        """
        Generate time-series features from daily inventory data
        """
        # Convert date to datetime
        self.inventory_df['date'] = pd.to_datetime(self.inventory_df['date'], format='%Y%m%d')
        
        # Sort by store, sku, date
        self.inventory_df = self.inventory_df.sort_values(['store_id', 'sku', 'date']).reset_index(drop=True)
        
        # Calculate 7-day and 30-day moving averages of sales
        self.inventory_df['sales_7day_ma'] = self.inventory_df.groupby(['store_id', 'sku'])['total_sales_units'].transform(
            lambda x: x.rolling(window=7, min_periods=1).mean()
        )
        self.inventory_df['sales_30day_ma'] = self.inventory_df.groupby(['store_id', 'sku'])['total_sales_units'].transform(
            lambda x: x.rolling(window=30, min_periods=1).mean()
        )
        
        # Days since last replenishment
        replenishment_days = self.inventory_df.groupby(['store_id', 'sku'])['replenishment_flag'].transform(
            lambda x: (~(x == 1)).cumsum()
        )
        self.inventory_df['days_since_replenishment'] = replenishment_days
        
        # Shelf capacity utilization ratio
        self.inventory_df['shelf_utilization_ratio'] = (
            self.inventory_df['on_hand_inventory_units'] / 
            (self.inventory_df['shelf_capacity'] + 1)  # +1 to avoid division by zero
        )
        
        # Days to deplete inventory at current sales rate
        self.inventory_df['days_to_deplete'] = np.where(
            self.inventory_df['sales_7day_ma'] > 0,
            self.inventory_df['on_hand_inventory_units'] / self.inventory_df['sales_7day_ma'],
            999  # High value if no sales
        )
        
        # Inventory pipeline ratio (incoming vs current)
        self.inventory_df['pipeline_ratio'] = (
            self.inventory_df['inventory_pipeline'] / 
            (self.inventory_df['on_hand_inventory_units'] + 1)
        )
        
        # Sales momentum (change in 7-day average vs 30-day average)
        self.inventory_df['sales_momentum'] = (
            (self.inventory_df['sales_7day_ma'] - self.inventory_df['sales_30day_ma']) / 
            (self.inventory_df['sales_30day_ma'] + 1)
        )
        
        # Zero-sales streak
        self.inventory_df['zero_sales_streak'] = (
            self.inventory_df.groupby(['store_id', 'sku'])
            .apply(lambda x: (x['total_sales_units'] == 0).cumsum())
            .reset_index(level=0, drop=True)
        )
        self.inventory_df.loc[self.inventory_df['total_sales_units'] > 0, 'zero_sales_streak'] = 0
        
        return self.inventory_df
    
    def create_clearance_target(self, future_days=30, sales_threshold_percentile=25):
        """
        Create binary target variable for slow-moving inventory prediction
        
        Target = 1 if SKU is in bottom 25% of sales velocity in next 30 days
        """
        # Calculate future sales velocity for each store-sku
        future_sales = (
            self.inventory_df.groupby(['store_id', 'sku'])['total_sales_units']
            .shift(-future_days)
            .rolling(window=future_days, min_periods=1)
            .mean()
        )
        
        # Calculate percentile threshold
        percentile_val = future_sales.quantile(sales_threshold_percentile / 100)
        
        # Create binary target
        self.inventory_df['is_slow_moving'] = (future_sales < percentile_val).astype(int)
        
        # Drop rows where target is NaN (last 30 days)
        valid_idx = self.inventory_df['is_slow_moving'].notna()
        
        return self.inventory_df[valid_idx]


# ============================================================================
# PART 2: INVENTORY LIFECYCLE PREDICTION MODEL
# ============================================================================

class InventoryLifecyclePredictor:
    """
    Predict which SKUs will become slow-moving within 14-30 days
    using Gradient Boosting classifier
    """
    
    def __init__(self):
        self.model = GradientBoostingClassifier(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=5,
            random_state=42,
            verbose=0
        )
        self.scaler = StandardScaler()
        self.feature_cols = None
        
    def train(self, X, y):
        """
        Train the slow-moving inventory prediction model
        
        X: DataFrame with features
        y: Series with binary target (1 = slow-moving, 0 = normal)
        """
        # Define feature set for model
        self.feature_cols = [
            'sales_7day_ma', 'sales_30day_ma', 'sales_momentum',
            'days_since_replenishment', 'shelf_utilization_ratio',
            'days_to_deplete', 'pipeline_ratio', 'zero_sales_streak'
        ]
        
        # Remove rows with NaN values
        mask = X[self.feature_cols].notna().all(axis=1)
        X_clean = X[self.feature_cols][mask]
        y_clean = y[mask]
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X_clean)
        
        # Train model
        self.model.fit(X_scaled, y_clean)
        
        # Print feature importance
        importances = pd.DataFrame({
            'feature': self.feature_cols,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print("\n=== Inventory Lifecycle Prediction - Feature Importance ===")
        print(importances.to_string(index=False))
        
        return self
    
    def predict(self, X):
        """
        Predict probability of slow-moving inventory
        """
        X_scaled = self.scaler.transform(X[self.feature_cols])
        probabilities = self.model.predict_proba(X_scaled)[:, 1]
        
        return probabilities


# ============================================================================
# PART 3: PRICE ELASTICITY ESTIMATION
# ============================================================================

class PriceElasticityEstimator:
    """
    Estimate price elasticity of demand using historical price and quantity data
    Builds category + location specific elasticity models
    """
    
    def __init__(self):
        self.elasticity_models = {}  # Store elasticity by category + store
        self.elasticity_coefficients = {}
        
    def estimate_elasticity_from_historical_data(self, history_df, current_data):
        """
        Estimate elasticity using historical markdown data
        
        history_df should contain: date, store_id, sku, price, quantity, category
        
        Elasticity = % change in quantity / % change in price
        ln(Q2/Q1) / ln(P2/P1)
        """
        
        # Group by category and store
        elasticities = {}
        
        for category in history_df['product_category'].unique():
            cat_data = history_df[history_df['product_category'] == category]
            
            for store in cat_data['store_id'].unique():
                store_cat_data = cat_data[cat_data['store_id'] == store].sort_values('date')
                
                if len(store_cat_data) < 10:  # Need sufficient data
                    continue
                
                # Calculate price changes and quantity changes
                store_cat_data = store_cat_data.copy()
                store_cat_data['price_change_pct'] = store_cat_data['price'].pct_change()
                store_cat_data['quantity_change_pct'] = store_cat_data['quantity'].pct_change()
                
                # Filter valid data points (non-zero changes)
                valid = (store_cat_data['price_change_pct'] != 0) & (store_cat_data['quantity_change_pct'].notna())
                valid_data = store_cat_data[valid]
                
                if len(valid_data) > 5:
                    # Estimate elasticity using linear regression on log-log space
                    X = np.log(np.abs(valid_data['price_change_pct']) + 0.001).values.reshape(-1, 1)
                    y = np.log(np.abs(valid_data['quantity_change_pct']) + 0.001).values
                    
                    # Simple linear fit
                    slope = np.polyfit(X.flatten(), y, 1)[0]
                    elasticities[f"{category}_{store}"] = slope
        
        self.elasticity_coefficients = elasticities
        
        print("\n=== Price Elasticity by Category & Store ===")
        for key, val in sorted(elasticities.items(), key=lambda x: x[1]):
            print(f"{key}: {val:.3f}")
        
        return self
    
    def get_elasticity(self, category, store_id, default=-1.2):
        """
        Get elasticity coefficient for category + store
        Falls back to default if not found
        """
        key = f"{category}_{store_id}"
        return self.elasticity_coefficients.get(key, default)


# ============================================================================
# PART 4: MARKDOWN OPTIMIZATION ENGINE
# ============================================================================

class MarkdownOptimizer:
    """
    Calculate optimal markdown price using constrained optimization
    
    Objective: Maximize Margin Dollars = Units_Sold × (Price - Cost)
    Subject to constraints on:
      - Minimum margin floor
      - Maximum discount cap
      - Competitive pricing floor
    """
    
    def __init__(self, elasticity_estimator):
        self.elasticity_estimator = elasticity_estimator
    
    def calculate_optimal_markdown(self, row, constraints):
        """
        Calculate optimal markdown for a single SKU
        
        row: dict with current_price, cost, current_quantity, category, store_id
        constraints: dict with min_margin_pct, max_discount_pct, competitor_price_floor
        """
        
        current_price = row.get('current_price', 100)
        current_quantity = row.get('current_quantity', 10)
        cost = row.get('cost', current_price * 0.6)
        category = row.get('category')
        store_id = row.get('store_id')
        
        # Get constraints
        min_margin_pct = constraints.get('min_margin_pct', 0.10)
        max_discount_pct = constraints.get('max_discount_pct', 0.40)
        competitor_price_floor = constraints.get('competitor_price_floor', current_price * 0.85)
        
        # Get elasticity for this category + store
        elasticity = self.elasticity_estimator.get_elasticity(category, store_id)
        
        # Objective function: maximize margin dollars
        def objective(discount_pct):
            # discount_pct is in [0, 1]
            new_price = current_price * (1 - discount_pct)
            new_margin_per_unit = new_price - cost
            
            # Demand uplift based on elasticity and price change
            price_elasticity_change = discount_pct / (1 - discount_pct + 0.0001)
            demand_uplift_multiplier = (1 + elasticity * price_elasticity_change) ** (1/elasticity if elasticity != 0 else 1)
            
            new_quantity = current_quantity * demand_uplift_multiplier
            
            total_margin_dollars = new_quantity * new_margin_per_unit
            
            return -total_margin_dollars  # Negative because we minimize
        
        # Constraint functions
        constraints_list = [
            # Minimum margin floor: (price - cost) / price >= min_margin_pct
            {'type': 'ineq', 
             'fun': lambda discount_pct: ((current_price * (1 - discount_pct) - cost) / (current_price * (1 - discount_pct) + 0.0001)) - min_margin_pct
            },
            # Competitive price floor: new_price >= competitor_price_floor
            {'type': 'ineq',
             'fun': lambda discount_pct: (current_price * (1 - discount_pct)) - competitor_price_floor
            }
        ]
        
        # Bounds: discount between 0 and max_discount_pct
        bounds = [(0, max_discount_pct)]
        
        # Initial guess
        x0 = np.array([0.15])  # Start with 15% discount
        
        # Optimize
        result = minimize(objective, x0, method='SLSQP', bounds=bounds, constraints=constraints_list)
        
        if result.success:
            optimal_discount_pct = result.x[0]
        else:
            optimal_discount_pct = 0.0  # No markdown recommended
        
        # Calculate metrics at optimal discount
        new_price = current_price * (1 - optimal_discount_pct)
        new_margin_per_unit = new_price - cost
        price_elasticity_change = optimal_discount_pct / (1 - optimal_discount_pct + 0.0001)
        demand_uplift_multiplier = (1 + elasticity * price_elasticity_change) ** (1/elasticity if elasticity != 0 else 1)
        new_quantity = current_quantity * demand_uplift_multiplier
        total_margin_dollars = new_quantity * new_margin_per_unit
        
        return {
            'current_price': current_price,
            'optimal_price': new_price,
            'discount_pct': optimal_discount_pct * 100,
            'current_quantity': current_quantity,
            'predicted_quantity': new_quantity,
            'quantity_uplift_pct': (new_quantity - current_quantity) / (current_quantity + 0.0001) * 100,
            'current_margin_dollars': current_quantity * (current_price - cost),
            'predicted_margin_dollars': total_margin_dollars,
            'margin_impact': total_margin_dollars - (current_quantity * (current_price - cost))
        }


# ============================================================================
# PART 5: MAIN EXECUTION & REPORTING
# ============================================================================

def main():
    """
    Main execution pipeline for markdown optimization
    """
    
    print("\n" + "="*80)
    print("MARKDOWN OPTIMIZATION USE CASE - MAIN EXECUTION")
    print("="*80)
    
    # Step 1: Load data
    print("\n[Step 1] Loading data...")
    inventory_df = pd.read_csv('osa_raw_data.csv')
    vendor_df = pd.read_csv('vendor_leadtime_info.csv')
    print(f"Loaded {len(inventory_df)} inventory records for {inventory_df['sku'].nunique()} SKUs")
    
    # Step 2: Data preparation & feature engineering
    print("\n[Step 2] Creating features...")
    data_prep = MarkdownDataPreparation(inventory_df, vendor_df)
    inventory_features = data_prep.create_time_series_features()
    print(f"Generated features: {list(inventory_features.columns)}")
    
    # Step 3: Train inventory lifecycle prediction model
    print("\n[Step 3] Training inventory lifecycle prediction model...")
    # Note: In production, historical markdown data would be needed for clearance target
    # For demonstration, we'll use a synthetic target based on sales velocity
    
    lifecycle_predictor = InventoryLifecyclePredictor()
    
    # Create synthetic target for demonstration
    inventory_features['is_slow_moving'] = (
        (inventory_features['sales_30day_ma'] < inventory_features['sales_30day_ma'].quantile(0.25))
    ).astype(int)
    
    # Train on subset of data
    X_train, X_test = train_test_split(
        inventory_features.dropna(), 
        test_size=0.2, 
        random_state=42
    )
    
    y_train = X_train['is_slow_moving']
    y_test = X_test['is_slow_moving']
    
    lifecycle_predictor.train(X_train, y_train)
    
    # Evaluate
    train_score = lifecycle_predictor.model.score(
        lifecycle_predictor.scaler.transform(X_train[lifecycle_predictor.feature_cols]), 
        y_train
    )
    test_score = lifecycle_predictor.model.score(
        lifecycle_predictor.scaler.transform(X_test[lifecycle_predictor.feature_cols]), 
        y_test
    )
    
    print(f"\nModel Performance:")
    print(f"  Train Accuracy: {train_score:.3f}")
    print(f"  Test Accuracy: {test_score:.3f}")
    
    # Step 4: Get predictions
    print("\n[Step 4] Generating slow-moving inventory predictions...")
    X_test['clearance_probability'] = lifecycle_predictor.predict(X_test)
    
    # Flag high-probability clearance candidates
    clearance_candidates = X_test[X_test['clearance_probability'] > 0.6].copy()
    clearance_candidates = clearance_candidates.sort_values('clearance_probability', ascending=False)
    
    print(f"\nIdentified {len(clearance_candidates)} SKUs for potential markdown")
    print("\nTop 10 Clearance Candidates:")
    print(clearance_candidates[['store_id', 'sku', 'sales_7day_ma', 'on_hand_inventory_units', 'clearance_probability']].head(10).to_string())
    
    # Step 5: Markdown optimization (demonstration with synthetic elasticity)
    print("\n[Step 5] Calculating optimal markdown recommendations...")
    
    elasticity_estimator = PriceElasticityEstimator()
    # In production, would train on historical markdown data
    # For now, use default elasticity
    elasticity_estimator.elasticity_coefficients = {key: -1.2 for key in range(100)}
    
    optimizer = MarkdownOptimizer(elasticity_estimator)
    
    # Define optimization constraints
    constraints = {
        'min_margin_pct': 0.15,        # Don't go below 15% margin
        'max_discount_pct': 0.35,      # Don't discount more than 35%
        'competitor_price_floor': None  # Not used in demo
    }
    
    # Calculate optimal markdowns for top candidates
    markdown_recommendations = []
    
    for idx, (_, row) in enumerate(clearance_candidates.head(5).iterrows()):
        markdown_rec = optimizer.calculate_optimal_markdown(
            {
                'current_price': 100,  # Synthetic
                'cost': 60,  # Synthetic
                'current_quantity': row['on_hand_inventory_units'],
                'category': row['product_category'],
                'store_id': int(row['store_id'])
            },
            constraints
        )
        
        markdown_rec['sku'] = row['sku']
        markdown_rec['store_id'] = row['store_id']
        markdown_rec['clearance_probability'] = row['clearance_probability']
        
        markdown_recommendations.append(markdown_rec)
    
    # Display recommendations
    print("\n" + "="*80)
    print("MARKDOWN OPTIMIZATION RECOMMENDATIONS")
    print("="*80)
    
    rec_df = pd.DataFrame(markdown_recommendations)
    display_cols = ['store_id', 'sku', 'current_price', 'optimal_price', 'discount_pct', 
                    'predicted_quantity', 'predicted_margin_dollars', 'clearance_probability']
    
    print("\n" + rec_df[display_cols].to_string(index=False))
    
    # Summary metrics
    total_current_margin = rec_df['current_margin_dollars'].sum()
    total_predicted_margin = rec_df['predicted_margin_dollars'].sum()
    total_margin_uplift = total_predicted_margin - total_current_margin
    
    print("\n" + "="*80)
    print("SUMMARY METRICS")
    print("="*80)
    print(f"Total Current Margin (${current_price} baseline): ${total_current_margin:,.2f}")
    print(f"Total Predicted Margin (with markdown): ${total_predicted_margin:,.2f}")
    print(f"Total Margin Uplift: ${total_margin_uplift:,.2f} ({(total_margin_uplift/total_current_margin*100):.1f}%)")
    print(f"Average Discount Recommended: {rec_df['discount_pct'].mean():.1f}%")
    print(f"Average Predicted Quantity Uplift: {rec_df['quantity_uplift_pct'].mean():.1f}%")
    
    print("\n✓ Markdown optimization analysis complete!")
    
    return {
        'lifecycle_predictor': lifecycle_predictor,
        'optimizer': optimizer,
        'recommendations': rec_df,
        'clearance_candidates': clearance_candidates
    }


if __name__ == '__main__':
    results = main()
