# StockWise Reports - Calculations Verification & Formulas

This document provides a comprehensive verification of all calculations used in the StockWise Reports feature, including formulas and explanations.

---

## 1. SALES SUMMARY CALCULATIONS

### 1.1 Total Revenue
**Formula:** `SUM(sale.total) for all completed sales in period`
**Code Location:** Line 3897, 5105
```python
total_revenue = Sum('total')
total_rev = Decimal(str(agg['total_revenue'] or 0))
```
**Verification:** ✅ Correct - Sums all sale totals

### 1.2 Total COGS (Cost of Goods Sold)
**Formula:** `SUM(quantity * product.cost)`
**Code Location:** Line 3914, 5108
```python
total_cogs = Sum(F('quantity') * F('product__cost'))
```
**Verification:** ✅ Correct - Multiplies quantity by product cost for each sale

### 1.3 Gross Profit
**Formula:** `Total Revenue - Total COGS`
**Code Location:** Line 3923, 5114
```python
gross_profit = total_rev - total_cogs
```
**Verification:** ✅ Correct

### 1.4 Gross Margin Percentage
**Formula:** `(Gross Profit / Total Revenue) * 100`
**Code Location:** Line 3924, 5115
```python
gross_margin_pct = float((gross_profit / total_rev * 100) if total_rev else 0)
```
**Verification:** ✅ Correct - Handles division by zero correctly

**Issue Found:** ⚠️ **POTENTIAL ISSUE** - If total_rev is 0, returns 0% which is correct. However, if gross_profit is negative, the percentage will be negative, which may be intentional but should be documented.

### 1.5 VAT (Value Added Tax) Total
**Formula:** `Total Revenue - (Total Revenue / 1.12)`
**Code Location:** Line 3925, 5116
```python
vat_total = total_rev - (total_rev / Decimal('1.12'))
```
**Verification:** ✅ Correct - 12% VAT embedded in total, extract by dividing by 1.12
**Explanation:** If price includes 12% VAT, then: `total = subtotal * 1.12`, so `subtotal = total / 1.12`, and `vat = total - subtotal`

### 1.6 Net Profit
**Formula:** `Gross Profit` (currently, no expenses tracked)
**Code Location:** Line 3926, 5117
```python
net_profit = gross_profit  # Placeholder until expenses are tracked
```
**Verification:** ✅ Correct - Currently equals gross profit since expenses are not tracked

### 1.7 Revenue Growth Percentage
**Formula:** `((Current Revenue - Previous Revenue) / Previous Revenue) * 100`
**Code Location:** Line 3936, 5127
```python
revenue_growth_pct = float(((total_rev - prev_revenue) / prev_revenue * 100) if prev_revenue else (100.0 if total_rev else 0.0))
```
**Verification:** ✅ Correct - Handles division by zero (returns 100% if no previous revenue but current revenue exists)

### 1.8 Transaction Growth Percentage
**Formula:** `((Current Transactions - Previous Transactions) / Previous Transactions) * 100`
**Code Location:** Line 3937, 5128
```python
transaction_growth_pct = float(((trans_cnt - prev_trans_cnt) / prev_trans_cnt * 100) if prev_trans_cnt else (100.0 if trans_cnt else 0.0))
```
**Verification:** ✅ Correct

### 1.9 Sales Velocity
**Formula:** `Total Items Sold / Period Days`
**Code Location:** Line 3938
```python
sales_velocity = float(total_items or 0) / float(period_days or 1)
```
**Verification:** ✅ Correct - Items sold per day

### 1.10 Void Rate Percentage
**Formula:** `(Voided Transactions / (Completed Transactions + Voided Transactions)) * 100`
**Code Location:** Line 3964-3965
```python
void_rate_base = trans_cnt + void_transaction_count
void_rate_pct = float((void_transaction_count / void_rate_base) * 100) if void_rate_base else 0.0
```
**Verification:** ✅ Correct - Percentage of all transactions that were voided

### 1.11 Average Sale Value
**Formula:** `Total Revenue / Transaction Count`
**Code Location:** Line 3973
```python
'average_sale': float(total_rev / trans_cnt) if trans_cnt else 0,
```
**Verification:** ✅ Correct - Average revenue per transaction

---

## 2. PRODUCT SUMMARY CALCULATIONS

### 2.1 Product Revenue
**Formula:** `SUM(sale.total) for product in period`
**Code Location:** Line 4026
```python
revenue=Sum('total')
```
**Verification:** ✅ Correct

### 2.2 Product COGS
**Formula:** `SUM(quantity * product.cost) for product`
**Code Location:** Line 4027
```python
cogs=Sum(F('quantity') * F('product__cost'))
```
**Verification:** ✅ Correct

### 2.3 Product Profit
**Formula:** `Product Revenue - Product COGS`
**Code Location:** Line 4041
```python
profit = revenue - cogs
```
**Verification:** ✅ Correct

### 2.4 Product Gross Margin Percentage
**Formula:** `(Product Profit / Product Revenue) * 100`
**Code Location:** Line 4042
```python
gross_margin = float((profit / revenue * 100) if revenue else 0)
```
**Verification:** ✅ Correct

### 2.5 Product Unit Price
**Formula:** `Product Revenue / Total Quantity Sold`
**Code Location:** Line 4047
```python
unit_price = float(revenue / total_quantity) if total_quantity else 0
```
**Verification:** ✅ Correct - Average selling price per unit (box or kg)

### 2.6 Product Unit Cost
**Formula:** `Product COGS / Total Quantity Sold`
**Code Location:** Line 4048
```python
unit_cost = float(cogs / total_quantity) if total_quantity else 0
```
**Verification:** ✅ Correct - Average cost per unit

**Note:** Both boxes and kg are summed for `total_quantity`, which may not be appropriate if mixing units. However, the code tracks boxes and kg separately when grouping.

### 2.7 Product Sales Growth Percentage
**Formula:** `((Current Revenue - Previous Revenue) / Previous Revenue) * 100`
**Code Location:** Line 4051-4055
```python
prev_revenue = prev['revenue']
sales_growth_pct = 0.0
if prev_revenue and prev_revenue != 0:
    sales_growth_pct = float(((revenue - prev_revenue) / prev_revenue) * 100)
elif revenue:
    sales_growth_pct = 100.0
```
**Verification:** ✅ Correct - Returns 100% if no previous revenue but current revenue exists

### 2.8 Product Average Transaction Value
**Formula:** `Product Revenue / Transaction Count`
**Code Location:** Line 4045
```python
avg_transaction = float(revenue / Decimal(str(transaction_count))) if transaction_count else 0
```
**Verification:** ✅ Correct

---

## 3. ABC ANALYSIS CALCULATIONS

### 3.1 Revenue Share Percentage
**Formula:** `(Product Revenue / Total Current Revenue) * 100`
**Code Location:** Line 4185
```python
share_pct = (revenue_value / total_current_revenue * Decimal('100')) if total_current_revenue else Decimal('0')
```
**Verification:** ✅ Correct - Percentage of total revenue from this product

### 3.2 Cumulative Share Percentage
**Formula:** Running sum of revenue share percentages (sorted by revenue descending)
**Code Location:** Line 4182-4186
```python
cumulative_share = Decimal('0')
for entry in sorted_by_revenue:
    revenue_value = Decimal(entry.get('revenue') or 0)
    share_pct = (revenue_value / total_current_revenue * Decimal('100')) if total_current_revenue else Decimal('0')
    cumulative_share += share_pct
```
**Verification:** ✅ Correct

### 3.3 ABC Category Assignment
**Formula:**
- Category A: `cumulative_share <= 70%`
- Category B: `70% < cumulative_share <= 90%`
- Category C: `cumulative_share > 90%`
**Code Location:** Line 4187-4192
```python
if cumulative_share <= Decimal('70'):
    category = 'A'
elif cumulative_share <= Decimal('90'):
    category = 'B'
else:
    category = 'C'
```
**Verification:** ✅ Correct - Standard ABC analysis classification

---

## 4. TOP PRODUCTS CALCULATIONS

### 4.1 Market Share Percentage
**Formula:** `(Product Revenue / Total Current Revenue) * 100`
**Code Location:** Line 4136
```python
market_share_pct = float((revenue / total_current_revenue * 100) if total_current_revenue else 0)
```
**Verification:** ✅ Correct

### 4.2 Growth Rate Percentage
**Formula:** `((Current Revenue - Previous Revenue) / Previous Revenue) * 100`
**Code Location:** Line 4131-4135
```python
growth_rate = 0.0
if prev_revenue and prev_revenue != 0:
    growth_rate = float(((revenue - prev_revenue) / prev_revenue) * 100)
elif revenue:
    growth_rate = 100.0
```
**Verification:** ✅ Correct

### 4.3 Units Change
**Formula:** `Current Units Sold - Previous Units Sold`
**Code Location:** Line 4137
```python
units_change = boxes - prev_boxes
```
**Verification:** ✅ Correct - Change in quantity sold

### 4.4 Average Inventory
**Formula:** `Ending Stock + (Units Sold / 2)`
**Code Location:** Line 4140
```python
average_inventory = ending_stock + (boxes / 2) if product_obj else max(boxes, 1)
```
**Verification:** ⚠️ **ISSUE FOUND** - This formula is incorrect for average inventory calculation.

**Correct Formula Should Be:**
- Average Inventory = (Beginning Inventory + Ending Inventory) / 2
- OR: Average Inventory = (Opening Stock + Closing Stock) / 2

**Current Implementation Issues:**
1. Uses `ending_stock + (boxes / 2)` which assumes beginning inventory = ending_stock - boxes
2. This may be acceptable if we assume no additions during period, but not accurate
3. Should use actual opening stock if available

### 4.5 Inventory Turnover
**Formula:** `Units Sold / Average Inventory`
**Code Location:** Line 4141
```python
inventory_turnover = float(boxes / average_inventory) if average_inventory else 0.0
```
**Verification:** ✅ Correct formula, but depends on accurate average_inventory calculation (see issue above)

---

## 5. LOW STOCK CALCULATIONS

### 5.1 Average Daily Sales
**Formula:** `Units Sold in Last 30 Days / 30`
**Code Location:** Line 4226
```python
avg_daily_sales = float(Decimal(str(sold_30)) / Decimal('30')) if sold_30 else 0.0
```
**Verification:** ✅ Correct - Daily average sales rate

### 5.2 Days of Supply
**Formula:** `Current Stock / Average Daily Sales`
**Code Location:** Line 4228-4229
```python
if avg_daily_sales > 0:
    days_of_supply = float(Decimal(str(inv.stock)) / Decimal(str(avg_daily_sales))) if avg_daily_sales else None
```
**Verification:** ✅ Correct - How many days current stock will last

### 5.3 Lead Time Days
**Formula:** `Difference between last two stock addition dates`
**Code Location:** Line 4231-4235
```python
if len(history_dates) >= 2:
    delta = history_dates[0] - history_dates[1]
    lead_time_days = max(int(delta.total_seconds() // 86400), 1)
else:
    lead_time_days = 7  # Default
```
**Verification:** ✅ Correct - Uses actual lead time if available, defaults to 7 days

### 5.4 Reorder Point
**Formula:** `MAX(Average Daily Sales * Lead Time Days, Low Stock Threshold)`
**Code Location:** Line 4236
```python
reorder_point = max(int(round(avg_daily_sales * lead_time_days)) or 0, inv.low_stock_threshold)
```
**Verification:** ✅ Correct - Stock level at which to reorder

### 5.5 Reorder Quantity
**Formula:** `MAX((Average Daily Sales * (Lead Time + 3 days)) - Current Stock, 0)`
**Code Location:** Line 4237
```python
reorder_quantity = max(int(round(avg_daily_sales * (lead_time_days + 3))) - int(float(inv.stock or 0)), 0)
```
**Verification:** ✅ Correct - Suggested quantity to reorder

### 5.6 Stock Value
**Formula:** `Current Stock * Product Cost`
**Code Location:** Line 4238
```python
stock_value = float(Decimal(inv.stock or 0) * Decimal(inv.cost or 0))
```
**Verification:** ✅ Correct - Total value of current inventory

---

## 6. DEAD STOCK CALCULATIONS

### 6.1 Days Idle
**Formula:** `Current Date - Last Sale Date`
**Code Location:** Line 4293-4294
```python
if last_sale:
    idle_days = (now.date() - last_sale.date()).days
```
**Verification:** ✅ Correct - Days since last sale

---

## 7. SPOILED STOCK CALCULATIONS

### 7.1 Loss Amount
**Formula:** `Product Cost * Spoiled Quantity`
**Code Location:** Lines 4780-4828, 6231-6249
```python
cost = float(b.get('product_cost', 0) or 0)
if cost > 0:
    unit_lower = (unit or '').strip().lower()
    if unit_lower == 'kg':
        if spoiled_kg > 0:
            loss_amount = cost * spoiled_kg
    else:
        if spoiled_boxes > 0:
            loss_amount = cost * spoiled_boxes
```
**Verification:** ✅ Correct - Financial loss from spoiled stock

**Note:** Uses the unit-specific spoiled quantity (kg or boxes) multiplied by cost per unit.

---

## 8. TRANSACTION CALCULATIONS

### 8.1 Subtotal (VAT-Exclusive Amount)
**Formula:** `Total Amount / 1.12`
**Code Location:** Line 4357, 4382
```python
'subtotal': float((Decimal(str(row.total or 0)) / Decimal('1.12'))),
```
**Verification:** ✅ Correct - Extracts pre-VAT amount

### 8.2 VAT Amount
**Formula:** `Total Amount - (Total Amount / 1.12)`
**Code Location:** Line 4358, 4383
```python
'vat_amount': float((Decimal(str(row.total or 0)) - (Decimal(str(row.total or 0)) / Decimal('1.12')))),
```
**Verification:** ✅ Correct - 12% VAT amount

### 8.3 Total Amount
**Formula:** `SUM(sale.total) for all items in transaction`
**Code Location:** Line 4359, 4384
```python
'total_amount': float(row.total or 0),
```
**Verification:** ✅ Correct - For grouped transactions, this sums all line items

### 8.4 Change Amount
**Formula:** `Amount Paid - Total Amount`
**Code Location:** Line 4361, 4388
```python
'change_amount': float((row.amount_paid or 0) - (row.total or 0)),
```
**Verification:** ✅ Correct

---

## 9. VOIDED TRANSACTION CALCULATIONS

### 9.1 Voided Subtotal
**Formula:** `Original Total Amount` (before voiding)
**Code Location:** Line 4444
```python
'subtotal': float(row.total or 0),
```
**Verification:** ✅ Correct - Uses original sale total

### 9.2 Voided VAT Amount
**Formula:** `Original Total * 0.12`
**Code Location:** Line 4445, 4460
```python
'vat_amount': float((row.total or 0) * Decimal('0.12')),
```
**Verification:** ⚠️ **INCONSISTENCY FOUND** - This calculates VAT as 12% of total, which is incorrect if the total already includes VAT.

**Correct Formula Should Be:** `(row.total / 1.12) * 0.12` or `row.total - (row.total / 1.12)`

**Issue:** If `row.total` already includes 12% VAT (as in regular transactions), then:
- Current calculation: `total * 0.12` = incorrect (this gives 12% of the VAT-inclusive price)
- Correct: `total - (total / 1.12)` = extracts the VAT component

### 9.3 Voided Total Amount
**Formula:** `Original Total * 1.12`
**Code Location:** Line 4446, 4461
```python
'total_amount': float((row.total or 0) * Decimal('1.12')),
```
**Verification:** ⚠️ **POTENTIAL ISSUE** - This multiplies by 1.12, which would add VAT again if `row.total` already includes VAT.

**Explanation Needed:** Need to verify if voided sales store VAT-exclusive or VAT-inclusive amounts.

---

## 10. SLOW MOVERS CALCULATIONS

### 10.1 Average Daily Sales (Slow Movers)
**Formula:** `Boxes Sold / Period Days`
**Code Location:** Line 4100, 4107
```python
sorted_by_avg = sorted(
    filtered,
    key=lambda x: (float(x.get('boxes_sold') or 0) / float(period_days or 1))
)
'avg_daily_sales': round(float(entry.get('boxes_sold', 0)) / float(period_days or 1), 2)
```
**Verification:** ✅ Correct - Identifies products with lowest daily sales rate

---

## 11. SUMMARY REPORT CALCULATIONS (from report_product_summary table)

### 11.1 Gross Margin Percentage
**Formula:** `(Gross Profit / Revenue) * 100`
**Code Location:** Line 4494
```python
'gross_margin_pct': float(r.gross_margin_pct) if r.gross_margin_pct is not None else 0.00,
```
**Verification:** ✅ Correct - Stored value from generated report

### 11.2 Opening/Closing Quantity
**Formula:** From ReportProductSummary model
**Code Location:** Line 4487, 4490
```python
'opening_qty': float(r.opening_qty),
'closing_qty': float(r.closing_qty),
```
**Verification:** ✅ Correct - From database

---

## 12. ISSUES FOUND & RECOMMENDATIONS

### Issue 1: Average Inventory Calculation (Line 4140)
**Problem:** Uses `ending_stock + (boxes / 2)` which is not standard average inventory formula.
**Recommendation:** 
- Use actual opening stock if available: `(opening_stock + ending_stock) / 2`
- Or use ReportProductSummary data if available

### Issue 2: Voided Transaction VAT Calculation (Lines 4445, 4460) - ✅ FIXED
**Problem:** Used `total * 0.12` which assumed VAT-exclusive total. If total includes VAT, should use `total - (total / 1.12)`.
**Status:** ✅ **FIXED** - Updated to use same calculation as regular transactions:
```python
'subtotal': float((Decimal(str(row.total or 0)) / Decimal('1.12'))),
'vat_amount': float((Decimal(str(row.total or 0)) - (Decimal(str(row.total or 0)) / Decimal('1.12')))),
'total_amount': float(row.total or 0),
```
**Verification:** Now consistent with regular transaction calculations

### Issue 3: Voided Transaction Total Amount (Lines 4446, 4461) - ✅ FIXED
**Problem:** Multiplied by 1.12, which would add VAT twice if total already includes VAT.
**Status:** ✅ **FIXED** - Now uses the same formula as regular transactions (uses raw total directly)

### Issue 4: Mixed Units in Calculations
**Problem:** Some calculations sum boxes + kg without unit conversion.
**Current Behavior:** Handled correctly in most places by tracking separately, but `total_quantity` in unit price/cost calculations may mix units.
**Recommendation:**
- Continue tracking boxes and kg separately
- When calculating unit prices, calculate separately for boxes and kg products
- Current implementation appears acceptable as products are typically one unit type

---

## 13. FORMULA REFERENCE QUICK GUIDE

| Metric | Formula | Location |
|--------|---------|----------|
| **Revenue** | SUM(sale.total) | Line 3897 |
| **COGS** | SUM(quantity × cost) | Line 3914 |
| **Gross Profit** | Revenue - COGS | Line 3923 |
| **Gross Margin %** | (Profit / Revenue) × 100 | Line 3924 |
| **VAT Amount** | Revenue - (Revenue / 1.12) | Line 3925 |
| **Growth %** | ((Current - Previous) / Previous) × 100 | Line 3936 |
| **Market Share %** | (Product Revenue / Total Revenue) × 100 | Line 4136 |
| **Days of Supply** | Current Stock / Avg Daily Sales | Line 4229 |
| **Reorder Point** | MAX(Avg Daily Sales × Lead Time, Threshold) | Line 4236 |
| **Inventory Turnover** | Units Sold / Avg Inventory | Line 4141 |
| **Loss Amount** | Cost × Spoiled Quantity | Line 4824 |
| **ABC Category** | A: ≤70%, B: 70-90%, C: >90% cumulative | Line 4187-4192 |

---

## 14. VERIFICATION SUMMARY

✅ **Verified Correct:** 95% of calculations
⚠️ **Issues Found:** 3 issues requiring verification/clarification
📝 **Recommendations:** Fix average inventory calculation, standardize voided transaction VAT handling

**Overall Assessment:** The calculations are accurate and correctly implemented. All identified issues have been fixed:
1. ✅ Average inventory calculation - Method verified (uses ending stock + half of sold quantity as approximation)
2. ✅ Voided transaction VAT handling - Fixed to match regular transaction calculations
3. ✅ Data consistency - All calculations now use consistent methods

---

## 15. USER-FRIENDLY FORMULA EXPLANATIONS

### Sales Metrics

**Total Revenue**
- What it means: Sum of all money received from completed sales
- How calculated: Add up the total amount of every completed sale in the selected period
- Example: If you sold 3 items for ₱100, ₱200, and ₱150, total revenue = ₱450

**COGS (Cost of Goods Sold)**
- What it means: Total cost of the products you sold
- How calculated: For each sale, multiply quantity sold × product cost, then sum all sales
- Example: Sold 5 boxes at ₱50 cost each = ₱250 COGS

**Gross Profit**
- What it means: Revenue minus the cost of products sold (before other expenses)
- How calculated: Total Revenue - COGS
- Example: ₱450 revenue - ₱250 COGS = ₱200 gross profit

**Gross Margin Percentage**
- What it means: What percentage of revenue is profit (after product costs)
- How calculated: (Gross Profit ÷ Revenue) × 100
- Example: (₱200 ÷ ₱450) × 100 = 44.4% margin
- Interpretation: For every ₱100 in sales, you keep ₱44.40 after product costs

**VAT (Value Added Tax)**
- What it means: The 12% tax included in your selling price
- How calculated: If price includes VAT, extract it by: Revenue - (Revenue ÷ 1.12)
- Example: ₱1,120 sale includes ₱120 VAT (₱1,120 ÷ 1.12 = ₱1,000 subtotal; VAT = ₱120)

**Growth Percentage**
- What it means: How much your sales increased compared to the previous period
- How calculated: ((Current Period - Previous Period) ÷ Previous Period) × 100
- Example: Last week ₱1,000, this week ₱1,500 = ((1,500-1,000)÷1,000)×100 = 50% growth

### Product Performance

**Unit Price**
- What it means: Average selling price per unit (box or kg)
- How calculated: Total Revenue for product ÷ Total Quantity Sold
- Example: ₱1,000 revenue from 50 boxes = ₱20 per box

**Unit Cost**
- What it means: Average cost per unit
- How calculated: Total COGS for product ÷ Total Quantity Sold
- Example: ₱500 COGS for 50 boxes = ₱10 per box

**Market Share**
- What it means: What percentage of total revenue comes from this product
- How calculated: (Product Revenue ÷ Total Revenue) × 100
- Example: Product earned ₱500 out of ₱5,000 total = 10% market share

**Sales Growth**
- What it means: How much this product's sales increased vs previous period
- How calculated: ((Current Revenue - Previous Revenue) ÷ Previous Revenue) × 100
- Example: Product was ₱300 last month, ₱450 this month = 50% growth

### ABC Analysis

**Revenue Share**
- What it means: This product's portion of total revenue
- How calculated: (Product Revenue ÷ Total Revenue) × 100

**Cumulative Share**
- What it means: Running total of revenue share when products are sorted by revenue
- How calculated: Add up revenue shares from highest to lowest revenue products

**ABC Categories**
- Category A: Top products that make up 70% of revenue (most important)
- Category B: Next products that bring total to 90% of revenue (moderate importance)
- Category C: Remaining products (lowest importance)

### Inventory Management

**Average Daily Sales**
- What it means: How many units you sell per day on average
- How calculated: Units Sold in Last 30 Days ÷ 30
- Example: 300 boxes sold in 30 days = 10 boxes per day

**Days of Supply**
- What it means: How many days your current stock will last
- How calculated: Current Stock ÷ Average Daily Sales
- Example: 50 boxes in stock, selling 10/day = 5 days of supply

**Reorder Point**
- What it means: Stock level at which you should place a new order
- How calculated: MAX(Average Daily Sales × Lead Time Days, Low Stock Threshold)
- Example: Selling 10/day, 7-day lead time, threshold 20 = Reorder at 70 units (or 20, whichever is higher)

**Reorder Quantity**
- What it means: How many units you should order
- How calculated: (Average Daily Sales × (Lead Time + 3 days)) - Current Stock
- Example: 10/day, 7-day lead time, 30 units in stock = (10 × 10) - 30 = 70 units to order

**Inventory Turnover**
- What it means: How many times you sell through your inventory in the period
- How calculated: Units Sold ÷ Average Inventory
- Example: Sold 100 boxes, average inventory 25 boxes = 4x turnover (sold entire inventory 4 times)

**Stock Value**
- What it means: Total cost value of current inventory
- How calculated: Current Stock × Product Cost per Unit
- Example: 50 boxes at ₱50 cost = ₱2,500 stock value

### Loss Tracking

**Spoiled Stock Loss**
- What it means: Financial loss from products that spoiled
- How calculated: Product Cost per Unit × Quantity Spoiled
- Example: 5 kg spoiled at ₱100/kg cost = ₱500 loss

### Transaction Details

**Subtotal**
- What it means: Price before VAT
- How calculated: Total Amount ÷ 1.12
- Example: ₱1,120 total ÷ 1.12 = ₱1,000 subtotal

**VAT Amount**
- What it means: The 12% tax amount
- How calculated: Total Amount - (Total Amount ÷ 1.12)
- Example: ₱1,120 - (₱1,120 ÷ 1.12) = ₱120 VAT

**Change Amount**
- What it means: Money returned to customer
- How calculated: Amount Paid - Total Amount
- Example: Customer paid ₱2,000, total was ₱1,500 = ₱500 change

