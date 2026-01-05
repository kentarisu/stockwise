 Demand-Driven Pricing Recommendation System
 Technical Documentation for Capstone Research

---

 1. Executive Summary

The StockWise Demand-Driven Pricing Recommendation System is an AI-powered pricing optimization tool designed for wholesale fruit and businesses. The system uses econometric modeling to analyze historical sales data and provide data-driven pricing recommendations that maximize revenue while maintaining profit margins.

Key Innovation: Machine learning-based elasticity modeling with human-in-the-loop approval, ensuring business owners maintain control while benefiting from data-driven insights.

---

 2. System Architecture

 2.1 Core Components

1. DemandPricingAI Engine (`core/pricing_ai.py`)
   - Log-log elasticity model training
   - Revenue optimization algorithm
   - Constraint enforcement

2. Database Models
   - `PricingRecommendation`: Stores AI suggestions (3-day expiration)
   - `PriceChangeHistory`: Audit trail of applied changes
   - `Sale`: Historical transaction data
   - `Product`: Catalog with current wholesale prices

3. Admin Interface
   - Pricing Analysis Dashboard
   - Recommendation approval/rejection
   - Price trend visualizations
   - Elasticity metrics display

4. Automation
   - Scheduled recommendation generation
   - SMS/Email notifications to admins
   - Automatic expiration of old recommendations

 2.2 Technology Stack

- Backend: Django (Python)
- Data Science: NumPy, Pandas (numerical computing)
- Database: PostgreSQL/MySQL
- Frontend: Bootstrap 5, Chart.js

---

 3. Pricing Algorithm

 3.1 Price Elasticity of Demand

The system is built on the economic principle of Price Elasticity of Demand (PED):

```
Elasticity (Îµ) = % Change in Quantity Demanded / % Change in Price
```

Interpretation:
- Îµ = -1.0: Unit elastic (1% price increase â†’ 1% quantity decrease)
- |Îµ| > 1.0: Elastic demand (customers very price-sensitive)
- |Îµ| < 1.0: Inelastic demand (customers less price-sensitive)

Wholesale Consideration: B2B customers typically show higher elasticity than end consumers since they:
- Compare prices across multiple suppliers
- Have budget constraints
- Can switch suppliers easily
- Purchase in bulk (small price differences = large cost impact)

 3.2 Log-Log Elasticity Model

The system uses log-log regression to estimate constant elasticity:

Mathematical Model:
```
ln(Quantity) = Î²â‚€ + Î²â‚Â·ln(Price) + Î£(month_dummies) + Î£(weekday_dummies) + error
```

Where:
- Î²â‚ = Elasticity (the coefficient we're estimating)
- month_dummies: Captures seasonal patterns (12 months)
- weekday_dummies: Captures day-of-week effects (7 days)

Why Log-Log?
1. Direct elasticity interpretation: Î²â‚ coefficient = elasticity
2. Handles multiplicative relationships: Captures % changes naturally
3. Economic foundation: Constant elasticity of demand model

Estimation Method: Ordinary Least Squares (OLS) with ridge regularization
```
Î² = (X^TÂ·X + Î»I)^(-1) Â· X^TÂ·y

Where:
- X = design matrix [1, ln_p, month_dummies, weekday_dummies]
- y = ln(quantity)
- Î» = 1e-6 (small regularization constant)
```

Model Quality Metric: RÂ² (Coefficient of Determination)
```
RÂ² = 1 - (Sum of Squared Residuals) / (Total Sum of Squares)

Confidence Levels:
- RÂ² â‰¥ 0.6: HIGH confidence
- 0.3 â‰¤ RÂ² < 0.6: MEDIUM confidence
- RÂ² < 0.3: LOW confidence
```

 3.3 Demand Signal Detection

The system calculates demand trends using moving averages:

```
u7  = Average daily sales over last 7 days (recent demand)
u30 = Average daily sales over last 30 days (baseline demand)
Demand Ratio = u7 / u30

Interpretation:
- Ratio â‰¥ 1.2: Strong demand â†’ Consider price INCREASE
- 0.8 < Ratio < 1.2: Stable demand â†’ Maintain current price
- Ratio â‰¤ 0.8: Weak demand â†’ Consider price DECREASE
```

 3.4 Revenue Optimization

Objective: Find price that maximizes revenue over planning horizon (7 days)

Algorithm:
```
For each product:
  1. Build price grid: 17 candidates from -20% to +20% in 2.5% steps
  
  2. For each candidate price P_new:
     a) Predict demand: Q_new = Q_base Ã— (P_new / P_current)^elasticity
     b) Calculate revenue: R = P_new Ã— Q_new Ã— 7 days
     c) Check constraints (see section 4)
  
  3. Select price with maximum revenue among valid candidates
  
  4. Classify action:
     - If change > +2%: INCREASE
     - If change < -2%: DECREASE
     - If |change| â‰¤ 2%: HOLD
```

---

 4. Safety Constraints

The system enforces multiple business rules to prevent risky pricing:

 4.1 Minimum Margin Constraint
```
Price â‰¥ Cost Ã— (1 + 0.10)  [10% minimum margin]
```
Purpose: Ensures profitability on all recommendations

 4.2 Maximum Movement Constraint
```
|Price_new - Price_current| / Price_current â‰¤ 0.10  [Â±10% max change]
```
Dynamic Adjustment:
- Low data (n < 6): limit to Â±6%
- Low confidence (RÂ² < 0.3): limit to Â±8%

Purpose: Prevents extreme price shocks that confuse wholesale customers

 4.3 Hold Band (Deadzone)
```
If |change| < 2%, ACTION = HOLD
```
Purpose: Avoids trivial changes that waste effort and confuse buyers

 4.4 Cooldown Period
```
If days_since_last_change < 3, ACTION = HOLD
```
Purpose: Allows time to observe customer response before next change

 4.5 Minimum Data Requirement
```
If sales_count < 15, use default elasticity = -1.0
```
Purpose: Prevents unreliable recommendations from sparse data

 4.6 Stock-Out Prevention
```
If predicted_demand Ã— 7 days > current_stock, penalize candidate
```
Purpose: Avoids prices that would deplete inventory prematurely

---

 5. Implementation Details

 5.1 Data Flow

Training Phase (runs daily):
```
1. Extract sales data (last 120 days)
   SELECT recorded_at, product_id, quantity, price FROM sales

2. Transform to log-log space
   ln_quantity = ln(quantity + 1e-6)
   ln_price = ln(price)

3. Add seasonal features
   month = EXTRACT(MONTH FROM recorded_at)
   weekday = EXTRACT(DOW FROM recorded_at)

4. Fit OLS regression per product
   Î² = (X^TÂ·X + Î»I)^(-1) Â· X^TÂ·y
   elasticity = Î²[1]

5. Calculate RÂ² and confidence level
```

Recommendation Phase:
```
1. Check cooldown period â†’ If violated, HOLD
2. Calculate demand signals (u7, u30, ratio)
3. Get elasticity from trained model (or use default)
4. Grid search over 17 candidate prices
5. Select revenue-maximizing price within constraints
6. Generate user-friendly explanation
7. Store recommendation (expires in 3 days)
8. Send SMS/Email notification to admins
```

Approval Phase:
```
Admin reviews via dashboard â†’
  If APPROVED:
    - Update Product.price
    - Log in PriceChangeHistory
    - Start 3-day cooldown period
  
  If REJECTED:
    - Record rejection
    - Recommendation expires naturally
```

 5.2 Database Schema

PricingRecommendation:
```sql
CREATE TABLE pricing_recommendations (
    recommendation_id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(product_id),
    current_price DECIMAL(10,2),
    suggested_price DECIMAL(10,2),
    change_pct DECIMAL(6,2),
    action VARCHAR(10),  -- 'INCREASE', 'DECREASE', 'HOLD'
    reason TEXT,
    elasticity DECIMAL(8,4),
    r2 DECIMAL(6,4),
    confidence VARCHAR(20),  -- 'HIGH', 'MED', 'LOW'
    created_at TIMESTAMP,
    expires_at TIMESTAMP  -- created_at + 3 days
);
```

PriceChangeHistory:
```sql
CREATE TABLE price_change_history (
    change_id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(product_id),
    old_price DECIMAL(10,2),
    new_price DECIMAL(10,2),
    change_pct DECIMAL(6,2),
    reason VARCHAR(50),  -- 'ai_recommendation', 'manual', etc.
    reason_details TEXT,
    demand_before DECIMAL(10,2),
    stock_level DECIMAL(10,2),
    service_type VARCHAR(100),  -- 'AI Demand-Based Pricing'
    created_by INTEGER REFERENCES users(user_id),
    created_at TIMESTAMP
);
```

 5.3 Key Configuration

PolicyConfig Parameters:
```python
min_margin_pct = 0.10         10% minimum profit margin
max_move_pct = 0.10           Â±10% maximum price change
cooldown_days = 3             Days between price changes
planning_horizon_days = 7     Revenue optimization period
min_obs_per_product = 15      Min sales for model training
default_elasticity = -1.0     Fallback elasticity (unit elastic)
hold_band_pct = 0.02          Â±2% threshold for HOLD action
```

---

 6. Use Case Examples

 Example 1: High Demand Product

Product: Apple (Gala) - Wholesale Box
Current Price: â‚±1,200 per box
Sales Last 7 Days: 45 boxes (6.4 boxes/day)
Sales Last 30 Days: 120 boxes (4.0 boxes/day)
Demand Ratio: 6.4 / 4.0 = 1.6 (strong upward pressure)

Model Metrics:
- Elasticity: -0.8 (inelastic - B2B customers need this product)
- RÂ²: 0.65 (HIGH confidence)
- Sample size: 23 sales

Revenue Analysis:
```
@ â‚±1,200: 6.4 boxes/day Ã— 7 days Ã— â‚±1,200 = â‚±53,760
@ â‚±1,320: 6.1 boxes/day Ã— 7 days Ã— â‚±1,320 = â‚±56,364 (+4.8%)
```

Recommendation:
- Action: INCREASE
- Suggested Price: â‚±1,320 (+10%)
- Reason: "Strong demand: 23 sales in past 3 days (45 boxes sold). Customers are buying frequently - increase price to boost profit margin."
- Confidence: HIGH

 Example 2: Slow-Moving Product

Product: Banana (Saba) - Wholesale 25kg Box
Current Price: â‚±600 per box
Sales Last 7 Days: 8 boxes (1.1 boxes/day)
Sales Last 30 Days: 45 boxes (1.5 boxes/day)
Demand Ratio: 1.1 / 1.5 = 0.73 (weak demand)

Model Metrics:
- Elasticity: -1.3 (elastic - customers have alternatives)
- RÂ²: 0.52 (MEDIUM confidence)
- Sample size: 14 sales

Revenue Analysis:
```
@ â‚±600: 1.1 boxes/day Ã— 7 days Ã— â‚±600 = â‚±4,620
@ â‚±540: 1.4 boxes/day Ã— 7 days Ã— â‚±540 = â‚±5,292 (+14.5%)
```

Recommendation:
- Action: DECREASE
- Suggested Price: â‚±540 (-10%)
- Reason: "Low demand: only 5 sales in past 3 days. Lowering price by 10% can attract more wholesale customers and increase revenue."
- Confidence: MED

---

 7. System Features

 7.1 Admin Dashboard

Pricing Analysis Page (`/pricing-analysis/`):
- Product table with current prices, elasticity, RÂ² scores
- AI recommendation badges (â†‘ INCREASE, â†“ DECREASE, â€” HOLD)
- Price trend charts (line graphs with sales overlay)
- Demand scatter plots (Price vs. Quantity with fitted curve)
- One-click approve/reject buttons

 7.2 Automated Notifications

SMS/Email Alerts:
- Sent when new recommendations are generated
- Summary of actionable suggestions (INCREASE/DECREASE only)
- Direct link to review dashboard
- Formatted for readability

Example SMS:
```
StockWise Pricing Alert: 3 new recommendations

1. Apple (Gala): â‚±1,200 â†’ â‚±1,320 (+10%)
   Reason: Strong demand trend

2. Banana (Saba): â‚±600 â†’ â‚±540 (-10%)
   Reason: Low sales activity

Review: http://127.0.0.1:8000/pricing-analysis/
```

 7.3 Reporting Integration

PDF Business Reports Include:
- Pricing Analysis section
- Table of products with elasticity metrics
- Price change history for report period
- AI recommendations summary

---

 8. Advantages and Limitations

 8.1 Advantages

1. Data-Driven Decisions: Removes guesswork from wholesale pricing
2. Revenue Optimization: Mathematically finds best price within constraints
3. Risk Mitigation: Multiple safety rules prevent extreme changes
4. Scalability: Handles hundreds of products simultaneously
5. Transparency: Explainable AI with clear reasoning
6. Continuous Learning: Models retrained with latest data

 8.2 Limitations

1. Data Requirements: Needs minimum 15 sales per product
2. Historical Dependence: Assumes past patterns predict future
3. External Factors: Doesn't model competitor prices, market events
4. Constant Elasticity: Assumes linear log-log relationship
5. Implementation Lag: 3-day cooldown and manual approval required

---

 9. Future Enhancements

1. Competitor Price Monitoring: Web scraping of competitor wholesale prices
2. Seasonal Forecasting: Advanced time series models (ARIMA, Prophet)
3. Bundle Pricing: Optimize prices for product combinations
4. Customer Segmentation: Different prices for different buyer types (restaurants vs. retailers)
5. A/B Testing: Randomly test price variants to validate elasticity
6. Real-Time Adjustments: Intraday pricing based on demand spikes

---

 10. Conclusion

The StockWise Demand-Driven Pricing Recommendation System applies econometric modeling and machine learning to wholesale pricing optimization. By combining:

1. Statistical rigor (log-log OLS regression)
2. Economic theory (price elasticity of demand)
3. Business constraints (margins, cooldown, stock)
4. Human oversight (approval workflow)

The system provides actionable pricing recommendations that help wholesale businesses maximize revenue while maintaining profitability and customer relationships.

Key Innovation: Product-specific elasticity estimation with seasonality controls, multi-constraint optimization, and confidence-based recommendations - all within a human-in-the-loop framework that preserves business owner control.

Research Contribution: Demonstrates practical application of classical econometric techniques to small-to-medium wholesale businesses, making advanced pricing analytics accessible beyond enterprise-level operations.

---

 References

1. Econometrics: Wooldridge, J. M. (2016). Introductory Econometrics: A Modern Approach. Cengage Learning.
2. Price Elasticity: Varian, H. R. (2014). Intermediate Microeconomics. W.W. Norton.
3. Revenue Management: Phillips, R. L. (2005). Pricing and Revenue Optimization. Stanford University Press.
4. Python Data Science: McKinney, W. (2010). "Data Structures for Statistical Computing in Python." Proceedings of the 9th Python in Science Conference.

---

System: StockWise Inventory Management System  
Module: Demand-Driven Pricing Recommendation Engine  
Business Type: Wholesale Fruits and Vegetables  
Date: January 2, 2026


