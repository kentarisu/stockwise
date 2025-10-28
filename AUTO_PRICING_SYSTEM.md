# 🤖 Automatic AI Pricing System

## 🎯 Overview
StockWise now has an **automatic AI pricing recommendation system** that analyzes your sales every 3 days and sends SMS recommendations to optimize your profits!

Just like how the system automatically alerts you about:
- ⚠️ **Low stock** (when inventory drops below 10 boxes)
- 📊 **Daily sales** (sent every evening at 8 PM)

Now it will also automatically send:
- 💰 **AI Pricing recommendations** (every 3 days at 9 AM)

---

## 🔄 How It Works

### Automatic Schedule:
```
Every 3 days at 9:00 AM → AI analyzes 30 days of sales → Sends SMS recommendations
```

### What the AI Does:
1. **Collects sales data** - Last 30 days of transactions
2. **Analyzes demand patterns** - Identifies high/low demand products
3. **Calculates optimal prices** - Uses demand elasticity & profit margins
4. **Sends recommendations** - Top 3 pricing changes via SMS

### Business Rules:
- ✅ **Minimum margin:** 10% profit above cost
- ✅ **Maximum change:** ±20% per recommendation
- ✅ **Cooldown period:** 3 days between price changes
- ✅ **Minimum data:** 3 sales required per product
- ✅ **Planning horizon:** 7-day forecast

---

## 📱 SMS Messages You'll Receive

### Example 1: Price INCREASE Recommendation
```
STOCKWISE AI Pricing Alert
Automatic 3-Day Analysis

==== RECOMMENDATION 1 ====
Product: Apple (120)

Current: PHP 150.00
Suggested: PHP 165.00
Action: INCREASE 10.0%

Why: Strong demand: 15 sales in past 30 days (125 boxes sold). 
Customers are buying frequently - you can increase price to 
boost profit margin.

Sales: 15 transactions
Volume: 125 boxes

==== RECOMMENDATION 2 ====
Product: Banana (130)

Current: PHP 120.00
Suggested: PHP 138.00
Action: INCREASE 15.0%

Why: Good sales: 10 transactions in past 30 days (85 boxes). 
Price increase of 15.0% can improve your profit while 
maintaining demand.

Sales: 10 transactions
Volume: 85 boxes

* 5 total recommendations available
Check dashboard for full details

- STOCKWISE AI Analytics
```

---

### Example 2: Price DECREASE Recommendation
```
STOCKWISE AI Pricing Alert
Automatic 3-Day Analysis

==== RECOMMENDATION 1 ====
Product: Orange (110)

Current: PHP 200.00
Suggested: PHP 170.00
Action: DECREASE 15.0%

Why: Low demand: Only 3 sales in past 30 days (12 boxes). 
Lowering price by 15.0% can attract more customers and 
increase total revenue.

Sales: 3 transactions
Volume: 12 boxes

- STOCKWISE AI Analytics
```

---

### Example 3: All Prices Optimal
```
STOCKWISE AI Pricing Report
Automatic 3-Day Analysis

==== STATUS ====
All products are optimally priced!

No pricing changes recommended at this time.
Your current prices are well-balanced.

- STOCKWISE AI Analytics
```

---

## 🕐 Automatic Schedule

| Event | Frequency | Time | Description |
|-------|-----------|------|-------------|
| **Daily Sales Summary** | Every day | 8:00 PM | Today's revenue, top products, remaining stock |
| **Low Stock Alert** | Every 6 hours | 6 AM, 12 PM, 6 PM, 12 AM | Products below 10 boxes |
| **AI Pricing Analysis** | Every 3 days | 9:00 AM | AI-powered price optimization |

---

## 🎨 Message Format - Before vs After

### ❌ Old Format (Manual Test Only)
```
Revenue StockWise Pricing Recommendation Stats 
Based on 30 days of sales data 1. Up Cherry (Red) 
Current: PHP 850.00 Suggested: PHP 1020.00 (20.0% increase) 
Reason: Stable demand; elasticity 0.36; R =1.00; n=3
```

**Problems:**
- ❌ No clear sections
- ❌ Technical jargon ("elasticity", "R²")
- ❌ Cramped formatting
- ❌ Not user-friendly

### ✅ New Format (Automatic + Manual)
```
STOCKWISE AI Pricing Alert
Automatic 3-Day Analysis

==== RECOMMENDATION 1 ====
Product: Up Cherry (Red)

Current: PHP 850.00
Suggested: PHP 1020.00
Action: INCREASE 20.0%

Why: Good sales: 3 transactions in past 30 days (15 boxes). 
Price increase of 20.0% can improve your profit while 
maintaining demand.

Sales: 3 transactions
Volume: 15 boxes

- STOCKWISE AI Analytics
```

**Improvements:**
- ✅ Clear sections with headers
- ✅ Plain English explanations
- ✅ Actual sales data shown
- ✅ Business-focused reasoning
- ✅ Professional spacing
- ✅ Actionable advice

---

## 🚀 How to Use

### Automatic (No Action Needed):
1. **Wait for SMS** - Every 3 days at 9 AM
2. **Read recommendations** - Review AI suggestions
3. **Check dashboard** - See full details if needed
4. **Apply prices** - Update products that make sense

### Manual (Anytime):
1. **Dashboard** → **SMS Settings**
2. Click **"Test Pricing SMS"**
3. Get instant AI recommendations
4. Review and apply

---

## 🔧 Technical Implementation

### Files Created/Modified:

#### 1. `core/management/commands/send_auto_pricing.py`
**New file** - Automatic pricing command
- Analyzes 30 days of sales
- Generates AI recommendations
- Sends formatted SMS
- Handles errors gracefully

#### 2. `core/views.py` (lines 3219-3264)
**Updated** - Test pricing messages
- Uses AI-generated reasons
- Better formatting with sections
- Shows sales data clearly
- Calculates revenue impact

#### 3. `stockwise_py/settings.py` (line 178)
**Updated** - Cron job configuration
```python
# AI Pricing recommendations automatically every 3 days at 9 AM
('0 9 */3 * *', 'django.core.management.call_command', ['send_auto_pricing']),
```

#### 4. `core/pricing_ai.py` (lines 274-313)
**Updated** - User-friendly reasons
- Plain English explanations
- Actual sales numbers
- Business context
- Removed jargon

---

## 📊 AI Analysis Process

### Step 1: Data Collection (30 Days)
```python
sales_data = {
    'product_id': ...,
    'date': ...,
    'quantity': ...,
    'price': ...,
    'revenue': ...
}
```

### Step 2: Demand Analysis
- **High demand (ratio ≥ 1.2):** Recent sales increasing → Recommend INCREASE
- **Stable demand (0.8-1.2):** Consistent sales → Small adjustments
- **Low demand (ratio ≤ 0.8):** Recent sales declining → Recommend DECREASE

### Step 3: Price Optimization
- Test multiple price points
- Calculate expected demand at each price
- Maximize revenue while respecting constraints
- Rank by potential revenue increase

### Step 4: Generate Recommendations
- Top 3 actionable changes
- User-friendly explanations
- Sales data included
- Revenue impact calculated

### Step 5: Send SMS
- Format professionally
- Include business reasoning
- Show actual numbers
- Provide dashboard link for details

---

## 🎯 What Makes It "AI"?

### Machine Learning Components:

1. **Demand Elasticity Learning**
   - Learns how customers respond to price changes
   - Adapts to your specific market
   - Uses historical sales patterns

2. **Predictive Modeling**
   - Forecasts future demand at different prices
   - Estimates revenue for next 7 days
   - Calculates confidence levels

3. **Optimization Algorithm**
   - Searches best price point automatically
   - Balances profit vs volume
   - Respects business constraints

4. **Continuous Learning**
   - Updates every 3 days with new data
   - Improves accuracy over time
   - Adapts to seasonal trends

---

## 🧪 Testing

### Test Automatic Pricing Now:
```bash
# Run the command manually
.\venv\Scripts\python.exe manage.py send_auto_pricing

# Force send even if no recommendations
.\venv\Scripts\python.exe manage.py send_auto_pricing --force
```

### Test Via SMS Settings:
1. **Dashboard** → **SMS Settings**
2. Click **"Test Pricing SMS"**
3. Receive instant recommendations

### Check Cron Jobs:
```bash
# List all scheduled tasks
python manage.py crontab show

# Add cron jobs to system
python manage.py crontab add

# Remove cron jobs
python manage.py crontab remove
```

---

## 📋 Comparison with Other Alerts

| Feature | Low Stock Alert | Daily Sales | AI Pricing |
|---------|----------------|-------------|------------|
| **Trigger** | Stock ≤ 10 | Every day 8PM | Every 3 days 9AM |
| **Frequency** | Immediate | Daily | Every 3 days |
| **Purpose** | Inventory warning | Performance review | Profit optimization |
| **Action** | Restock now | Monitor trends | Update prices |
| **Data Used** | Current stock | Today's sales | 30-day analysis |
| **Intelligence** | Rule-based | Aggregation | AI/Machine Learning |

---

## 💡 Business Benefits

### For You:
1. **Automated optimization** - No need to manually analyze prices
2. **Data-driven decisions** - Based on actual sales, not guesses
3. **Time savings** - AI does the analysis for you
4. **Profit maximization** - Increase margins where possible
5. **Volume optimization** - Lower prices to boost slow movers
6. **Stay competitive** - Adapt to market demand automatically

### For Your Business:
1. **Increased revenue** - Optimal pricing = more profit
2. **Better inventory turnover** - Slow movers get price cuts
3. **Market responsiveness** - Prices adapt to demand
4. **Professional management** - Data-driven pricing strategy
5. **Competitive advantage** - AI-powered insights
6. **Growth potential** - Continuous optimization

---

## ⚙️ Configuration

### In `stockwise_py/settings.py`:

```python
# Cron schedule (change if needed)
CRONJOBS = [
    # Change time or frequency here
    ('0 9 */3 * *', 'django.core.management.call_command', ['send_auto_pricing']),
]
```

### Cron Format:
```
* * * * *
│ │ │ │ │
│ │ │ │ └─── Day of week (0-7, Sunday = 0 or 7)
│ │ │ └───── Month (1-12)
│ │ └─────── Day of month (1-31)
│ └───────── Hour (0-23)
└─────────── Minute (0-59)
```

### Examples:
```python
# Every day at 9 AM
('0 9 * * *', ...)

# Every 3 days at 9 AM (current)
('0 9 */3 * *', ...)

# Every Monday at 9 AM
('0 9 * * 1', ...)

# Twice a week (Monday & Thursday at 9 AM)
('0 9 * * 1,4', ...)
```

---

## 🎉 Summary

**Your StockWise system now has:**
- ✅ **Automatic AI pricing** - Every 3 days
- ✅ **User-friendly messages** - Plain English, no jargon
- ✅ **Professional formatting** - Clear sections with headers
- ✅ **Actual sales data** - Transactions and volumes shown
- ✅ **Business reasoning** - Understand WHY to change prices
- ✅ **Revenue impact** - See potential profit increase
- ✅ **Continuous optimization** - Adapts to your market

**The system automatically:**
1. 📊 **Analyzes** 30 days of sales data
2. 🤖 **Calculates** optimal prices using AI
3. 📱 **Sends** SMS recommendations every 3 days
4. 💰 **Helps** you maximize profits effortlessly!

---

## 🆘 Troubleshooting

### No SMS Received:
- Check admin phone number is configured
- Verify IPROG API token is set
- Check SMS credits in iProg dashboard
- Run manual test: `python manage.py send_auto_pricing --force`

### "Insufficient data" Message:
- Need at least 3 sales per product
- Recommend having 30+ days of history
- Keep selling, data will accumulate!

### "All optimal" Every Time:
- Your prices are already good! 
- System respects cooldown (3 days)
- Market may be stable (good thing!)

---

*Last Updated: October 23, 2025*  
*Status: ✅ Automatic AI Pricing ACTIVE*  
*Next Automatic Analysis: Every 3 days at 9:00 AM*

