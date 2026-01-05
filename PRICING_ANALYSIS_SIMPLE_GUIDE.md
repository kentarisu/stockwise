PRICING ANALYSIS SYSTEM - Simple Guide for Capstone Defense

================================================================================
CORE CONCEPT
================================================================================

Q: What does your system do?

A: Automatically recommends optimal prices for wholesale products using AI that analyzes sales data. Instead of guessing, the owner gets data-driven suggestions like "Increase Apple price to ₱1,320" with clear reasoning.


Q: Why is this needed?

A: Three problems in wholesale:
1. Prices change frequently (seasonal, suppliers, market conditions)
2. Too many products to manage manually (50-100+ items)
3. Wrong pricing is expensive (too high = lose customers, too low = lose profit)


================================================================================
HOW IT WORKS (4 Steps)
================================================================================

STEP 1: Collect Sales History
- Gathers last 120 days of sales data
- Records: date, product, quantity sold, price

STEP 2: Calculate Price Elasticity
- Measures how sales respond to price changes
- Example: If price goes up 10%, do sales drop 5%? 15%?

STEP 3: Find Optimal Price
- Tests 17 different prices (from -20% to +20%)
- Calculates revenue for each option
- Picks the price that makes the MOST money

STEP 4: Safety Checks
- Ensures 10% minimum profit margin
- Limits changes to ±10% maximum
- Requires human approval


================================================================================
KEY QUESTION: WHY LOG-LOG?
================================================================================

Q: What is log-log algorithm?

A: A mathematical method that finds the relationship between price changes and sales changes, measured in PERCENTAGES.


Q: Why use log-log instead of simpler methods?

A: Three reasons:

1. BUSINESS THINKING
   - Owners think in %: "Should I increase by 10%?"
   - NOT in absolute: "Should I increase by ₱120?"
   - Log-log works naturally with percentages

2. DIRECT ELASTICITY
   - The number you get IS the elasticity directly
   - No extra calculations needed
   - Example: coefficient = -0.8 means "1% price up → 0.8% sales down"

3. ECONOMIC STANDARD
   - Standard method in economics for 50+ years
   - Proven reliable for price analysis
   - Matches real-world behavior


Q: What is elasticity in simple terms?

A: How SENSITIVE customers are to price changes.

Inelastic (e.g., -0.8):
- Customers still buy even if price goes up
- Strategy: INCREASE price → more profit

Elastic (e.g., -1.5):
- Customers very price-sensitive
- Strategy: DECREASE price → sell more → more revenue


Q: How do you calculate elasticity?

Simple version:
1. Look at past sales: when price was high vs. low
2. Find the pattern: "Every 1% price increase caused 0.8% sales drop"
3. That's your elasticity: -0.8

Technical version:
ln(Quantity) = β₀ + β₁ × ln(Price) + seasonal_factors
Where β₁ = elasticity (found using OLS regression)


================================================================================
WHOLESALE-SPECIFIC FEATURES
================================================================================

Q: Why is this good for wholesale businesses?

A: Four wholesale-specific features:

1. FIFO INTEGRATION
   - Tracks actual batch costs (they change every delivery)
   - Ensures recommendations always protect profit margins
   - Example: New batch costs ₱1,200, system won't suggest below ₱1,320

2. COOLDOWN PERIOD
   - Waits 3 days between price changes
   - B2B customers need stable prices (not like Uber surge)
   - Protects business relationships

3. CONSERVATIVE LIMITS
   - Maximum ±10% change at once
   - Prevents shocking wholesale customers
   - Gradual adjustments

4. HUMAN APPROVAL
   - Admin must approve every change
   - Not fully automated (owner stays in control)
   - Can reject if doesn't make sense


Q: How does FIFO connect to pricing?

A: Critical safety feature:

Without FIFO:
- Old batch cost ₱1,000
- New batch cost ₱1,200
- AI might suggest ₱1,150 (looks profitable vs. ₱1,000)
- You lose money on new stock!

With FIFO Integration:
- System knows current batch costs ₱1,200
- Minimum allowed = ₱1,200 × 1.10 = ₱1,320
- Always protects profit on CURRENT inventory


================================================================================
SAFETY & ACCURACY
================================================================================

Q: What if AI makes a mistake?

A: Six safety layers:

1. Human approval required (admin clicks "Approve")
2. Minimum 10% profit margin enforced
3. Maximum ±10% change limit
4. 3-day cooldown between changes
5. Needs minimum 15 sales (rejects insufficient data)
6. Stock-out prevention (won't price too low if low stock)


Q: How accurate is it?

A: Measured by R² score:

R² = 0.65 (HIGH confidence) → Follow recommendation
R² = 0.45 (MEDIUM confidence) → Review carefully
R² = 0.15 (LOW confidence) → Be cautious, maybe reject

System shows confidence level for every recommendation.


================================================================================
REAL EXAMPLE (Simplified)
================================================================================

Product: Apple (Gala)
Current Price: ₱1,200
Cost (FIFO): ₱1,000

WEEK 1: Strong Sales
- Sold 83 boxes in 7 days (11.9 boxes/day)
- Previous 30-day average: 8.2 boxes/day
- Demand ratio: 11.9 / 8.2 = 1.45 (STRONG trend)

WEEK 2: AI Analysis
- Elasticity calculated: -0.76 (inelastic)
- R² score: 0.68 (HIGH confidence)
- Optimal price found: ₱1,320 (+10%)
- Predicted: 10.9 boxes/day × ₱1,320 = ₱14,388/day
- Current: 11.9 boxes/day × ₱1,200 = ₱14,280/day
- Revenue increase: +₱108/day

WEEK 2: Recommendation
SMS sent to admin:
"Apple (Gala): ₱1,200 → ₱1,320 (+10%)
Reason: Strong demand: 35 sales in past 3 days
Confidence: HIGH"

Admin approves → Price updated → System tracks results


================================================================================
TECHNICAL IMPLEMENTATION
================================================================================

Q: What technologies used?

A: 
- Backend: Django (Python)
- Data Science: NumPy, Pandas
- Database: PostgreSQL
- Frontend: Bootstrap 5, Chart.js
- Algorithm: OLS (Ordinary Least Squares) regression


Q: How does revenue optimization work?

A:
1. Create price grid: 17 options from ₱960 to ₱1,440
2. For each price, predict demand using elasticity
3. Calculate: Revenue = Price × Predicted_Quantity × 7 days
4. Check constraints (profit margin, max movement, stock)
5. Pick valid price with highest revenue


================================================================================
ANTICIPATED PANELIST QUESTIONS
================================================================================

Q: Why not just use cost-plus pricing (Cost × 1.30)?

A: Cost-plus ignores demand:
- High demand = missed opportunity (could charge more)
- Low demand = no sales (price too high)
- Our system uses ACTUAL sales data to optimize


Q: What if there's not enough data?

A: System requires minimum 15 sales per product:
- Less than 15 → uses safe default elasticity (-1.0)
- Shows "LOW confidence" warning
- Admin can reject recommendation


Q: How is this different from Uber surge pricing?

A:
Uber: Changes every few minutes, fully automated, 2-5× surge
Ours: Changes every 3+ days, needs approval, max ±10%

Why? B2B relationships need stability, not constant fluctuation.


Q: What are the limitations?

A:
1. Needs historical data (15+ sales)
2. Doesn't model external factors (weather, competitors)
3. Assumes past patterns predict future
4. Requires good data quality (garbage in = garbage out)


Q: What makes this innovative?

A:
1. FIFO-integrated pricing (protects margins with real-time costs)
2. Wholesale-specific design (cooldown, conservative limits)
3. Explainable AI (shows reasoning, not black box)
4. Complete system (not just algorithm, full workflow)


Q: Expected business impact?

A:
- Revenue: +3-5% from optimized pricing
- Time: Save 40 hours/month (automation)
- Margins: Protected with 10% minimum enforcement
- Decisions: Data-driven instead of guessing


================================================================================
KEY TALKING POINTS FOR DEFENSE
================================================================================

When explaining log-log:
"Businesses think in percentages. Log-log naturally captures percentage relationships. The coefficient IS the elasticity - no conversion needed. It's the economic standard for 50+ years."

When explaining how it works:
"Four steps: Collect sales data, calculate customer price sensitivity, test different prices to find revenue maximum, apply safety checks."

When explaining safety:
"Human-in-the-loop: admin must approve. Multiple constraints: 10% profit minimum, ±10% change maximum, 3-day cooldown. Shows confidence level for every recommendation."

When explaining wholesale fit:
"B2B customers need stable prices. Our system has cooldown periods, conservative limits, and integrates with FIFO to protect margins on current inventory costs."

When explaining innovation:
"First system to connect FIFO inventory costs to AI pricing. Ensures recommendations always account for current batch costs, not outdated averages. Designed specifically for wholesale, not retail."


================================================================================
FORMULA REFERENCE (If Asked)
================================================================================

Elasticity Model:
ln(Quantity) = β₀ + β₁×ln(Price) + month_dummies + weekday_dummies + error

Where:
- β₁ = elasticity coefficient
- Solved using: β = (X^T·X + λI)^(-1) · X^T·y

Demand Prediction:
Q_new = Q_current × (P_new / P_current)^elasticity

Revenue Optimization:
Revenue = Price × Predicted_Quantity × 7 days
Select: argmax(Revenue) subject to constraints

Constraints:
- Price ≥ Cost × 1.10 (minimum margin)
- |Price_change| ≤ 10% (maximum movement)
- Cooldown ≥ 3 days (minimum time between changes)


================================================================================
FINAL SUMMARY
================================================================================

Problem: Wholesale can't manually optimize 50-100 product prices daily

Solution: AI analyzes sales data, calculates price elasticity, recommends optimal prices

Key Method: Log-log regression (standard economic approach for % relationships)

Safety: Human approval, profit protection, conservative limits, confidence scoring

Innovation: FIFO integration, wholesale-specific design, explainable AI

Impact: +3-5% revenue, time savings, protected margins, data-driven decisions


Good luck with your defense! 🎓
