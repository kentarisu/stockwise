# Pricing Analysis Formulas - Quick Reference

## Overview
This document explains the key formulas used in StockWise Pricing Analysis and why they matter for your business.

---

## 1. DEMAND RATIO

**Formula:** Recent Average (Last 7 Days) / Older Average (Days 8-30)

**What it does:** Shows if demand is increasing, stable, or decreasing

**How to read it:**
- 1.2 or higher = Strong demand → Consider raising price
- 0.8 to 1.2 = Stable demand → Keep current price
- 0.8 or lower = Weak demand → Consider lowering price

**Why it matters:** The AI uses this to decide whether to recommend price increases or decreases

---

## 2. AVERAGE DAILY DEMAND

**Formula:** Total Quantity Sold / Number of Days

**What it does:** Shows how fast products are selling per day

**Why it matters:** Used to predict future sales and plan inventory

---

## 3. PRICE ELASTICITY

**Formula:** ln(Quantity) = β₀ + β₁ × ln(Price) + seasonality factors

**What it does:** Measures how sensitive customers are to price changes

**How to read it:**
- Elasticity greater than 1.0 = Customers are price-sensitive → Lower prices to increase revenue
- Elasticity less than 1.0 = Customers less price-sensitive → Raise prices to boost profit

**Why it matters:** This is the core AI model that predicts how demand changes at different prices

---

## 4. MODEL CONFIDENCE (R²)

**Formula:** R² = 1 - (Sum of Squared Residuals) / (Total Sum of Squares)

**What it does:** Measures how reliable the elasticity model is

**How to read it:**
- R² ≥ 0.6 = HIGH confidence - Model explains 60%+ of demand changes
- R² 0.3-0.6 = MEDIUM confidence - Model explains 30-60% of changes
- R² < 0.3 = LOW confidence - Model explains less than 30% (less reliable)

**Why it matters:** Determines whether you can trust the AI recommendations

---

## 5. DEMAND PREDICTION

**Formula:** Q_new = Q_base × (P_new / P_current)^elasticity

**What it does:** Predicts how much will be sold at a new price

**Example:**
- Current: ₱1,200, selling 10 boxes/day, elasticity = -0.8
- New price: ₱1,320 (+10%)
- Predicted: 10 × (1,320/1,200)^(-0.8) = 9.17 boxes/day

**Why it matters:** Used to find the price that maximizes revenue

---

## 6. REVENUE OPTIMIZATION

**Formula:** Revenue = Price × Predicted_Quantity × 7 days

**What it does:** Tests multiple prices and picks the one that makes the most money

**How it works:**
1. Tests 17 price candidates from -20% to +20%
2. Predicts demand for each price
3. Calculates revenue for each
4. Picks the best one that meets safety rules

**Why it matters:** This is how the AI finds the "best" price automatically

---

## 7. MARGIN OF ERROR

**Formula:** |Actual Sales - Predicted Sales| / Predicted Sales × 100%

**What it does:** Measures how accurate the predictions are

**How to read it:**
- Less than 20% = Accurate predictions
- 20-50% = Reasonably accurate
- More than 50% = May need more data

**Why it matters:** Validates that the AI model is working correctly

---

## 8. SAFETY CONSTRAINTS

**Minimum Margin:** Price must be at least 10% above cost

**Maximum Change:** Price can only change ±10% at once (less if data is limited)

**Hold Band:** Changes less than 2% are ignored (too small to matter)

**Cooldown Period:** Must wait 3 days between price changes

**Stock Protection:** Won't recommend prices that would cause stock-outs

**Why it matters:** These rules ensure recommendations are safe and profitable

---

## WHY THESE FORMULAS MATTER

**The Problem:** Manually optimizing prices for 50-100 products takes hours daily and is error-prone.

**The Solution:** These formulas automate pricing analysis for all products simultaneously.

**The Benefits:**
- 3-5% revenue increase through optimal pricing
- Saves hours of work per day
- Protects profit margins automatically
- Prevents risky price changes
- Scales to hundreds of products

**Real Example:**
- Without system: Review 5-10 products/day, takes 2 weeks to review all 50
- With system: AI analyzes all 50 products daily, you review recommendations in 15 minutes

---

## QUICK SUMMARY

| Formula | Purpose |
|--------|---------|
| Demand Ratio | Detect demand trends |
| Avg Daily Demand | Sales velocity |
| Elasticity | Price sensitivity |
| R² | Model reliability |
| Demand Prediction | Forecast sales |
| Revenue Optimization | Find best price |
| Margin of Error | Validate accuracy |

All formulas work together to provide automated, data-driven pricing recommendations that maximize revenue while protecting profits.
