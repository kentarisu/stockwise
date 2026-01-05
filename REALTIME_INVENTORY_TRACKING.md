# Real-Time Inventory Tracking System - Detailed Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [Database Architecture](#database-architecture)
3. [FIFO Stock Management](#fifo-stock-management)
4. [Real-Time Tracking Components](#real-time-tracking-components)
5. [Stock Transaction Flow](#stock-transaction-flow)
6. [Low Stock Alerts](#low-stock-alerts)
7. [API Endpoints](#api-endpoints)
8. [Frontend Integration](#frontend-integration)
9. [Data Consistency & Atomicity](#data-consistency--atomicity)
10. [Performance Optimizations](#performance-optimizations)

---

## System Overview

The StockWise inventory tracking system provides **real-time, accurate stock tracking** using a combination of:
- **FIFO (First-In-First-Out) batch tracking**
- **Django signals for automatic updates**
- **Atomic database transactions**
- **RESTful API endpoints**
- **Frontend JavaScript refresh mechanisms**

### Key Features
✅ **Real-time stock updates** - Instant reflection of stock changes across all pages
✅ **FIFO batch management** - Track individual batches with dates, suppliers, and costs
✅ **Automatic low-stock alerts** - SMS notifications when stock falls below thresholds
✅ **Decimal precision** - Support for both kg (decimal) and box (integer) quantities
✅ **Transaction safety** - Atomic operations prevent data corruption
✅ **Audit trail** - Complete logging of all stock movements

---

## Database Architecture

### Core Tables

#### 1. **Products Table** (`products`)
Stores product master data with real-time stock levels.

```sql
product_id              INT PRIMARY KEY AUTO_INCREMENT
name                    VARCHAR(50)
variant                 VARCHAR(50)
status                  ENUM('active', 'discontinued')
stock                   DECIMAL(10, 2)  -- Real-time stock level
quantity_unit           VARCHAR(50)     -- 'kg', '10', '15', '20', etc.
low_stock_threshold     INT DEFAULT 10
price                   DECIMAL(10, 2)
cost                    DECIMAL(10, 2)
date_added              DATE
last_updated            DATETIME        -- Auto-updated on changes
```

**Key Field: `stock`**
- Updated in real-time on every addition/sale/void
- Calculated from sum of `remaining_quantity` in `stock_additions`
- Supports decimals for kg products (e.g., 15.50 kg)
- Supports integers for box products (e.g., 20 boxes)

---

#### 2. **Stock Additions Table** (`stock_additions`)
Tracks individual stock batches for FIFO management.

```sql
addition_id             INT PRIMARY KEY AUTO_INCREMENT
product_id              INT FOREIGN KEY -> products
quantity                DECIMAL(10, 2)     -- Original quantity added
remaining_quantity      DECIMAL(10, 2)     -- Current available quantity
spoiled                 DECIMAL(10, 2)     -- Manually removed/spoiled quantity
batch_id                VARCHAR(20)        -- e.g., "P286-STD-10-114"
date_added              DATETIME           -- Used for FIFO ordering
supplier                VARCHAR(100)
cost                    DECIMAL(10, 2)
price                   DECIMAL(10, 2)     -- Price for this batch
created_at              DATETIME
```

**FIFO Logic:**
- Batches ordered by: `date_added ASC, addition_id ASC`
- Oldest batches are consumed first
- `remaining_quantity` decreases as products are sold
- When batch is depleted, product price updates to next batch's price

**Indexes for Performance:**
```sql
INDEX idx_sa_product_date (product_id, date_added)
INDEX idx_sa_batch (batch_id)
```

---

#### 3. **Sales Table** (`sales`)
Records all sales transactions with FIFO breakdown.

```sql
sale_id                 INT PRIMARY KEY AUTO_INCREMENT
product_id              INT FOREIGN KEY -> products
quantity                DECIMAL(10, 2)
price                   DECIMAL(10, 2)
total                   DECIMAL(10, 2)
transaction_number      VARCHAR(32)         -- e.g., "TXN123456"
or_number               VARCHAR(32)         -- Official Receipt number
customer_name           VARCHAR(50)
recorded_at             DATETIME
status                  ENUM('completed', 'voided')
fifo_breakdown          TEXT                -- JSON with batch details
user_id                 INT FOREIGN KEY -> users
```

**FIFO Breakdown JSON Example:**
```json
[
  {
    "addition_id": 114,
    "batch_id": "P286-STD-10-114",
    "quantity": 15,
    "price": 120.00,
    "subtotal": 1800.00,
    "date_added": "2026-01-05"
  },
  {
    "addition_id": 115,
    "batch_id": "P286-STD-10-115",
    "quantity": 5,
    "price": 150.00,
    "subtotal": 750.00,
    "date_added": "2026-01-05"
  }
]
```

---

## FIFO Stock Management

### Overview
The system implements **strict FIFO** for cost accounting and inventory rotation.

### FIFO Deduction Process

#### Function: `deduct_stock_fifo(product_id, quantity)`
**Location:** `core/views.py:9610-9649`

```python
def deduct_stock_fifo(product_id, quantity):
    """Deduct stock using FIFO method (strict FIFO by date_added, then addition_id)"""
    
    # Get batches with remaining stock, ordered by date_added then addition_id
    batches = StockAddition.objects.filter(
        product_id=product_id,
        remaining_quantity__gt=0
    ).order_by('date_added', 'addition_id')  # FIFO order
    
    remaining_to_deduct = quantity
    
    # Deduct from each batch in FIFO order
    for batch in batches:
        if remaining_to_deduct <= 0:
            break
        
        deduct_amount = min(remaining_to_deduct, batch.remaining_quantity)
        batch.remaining_quantity -= deduct_amount
        batch.save()
        
        remaining_to_deduct -= deduct_amount
    
    # Raise error if insufficient stock
    if remaining_to_deduct > 0:
        raise ValueError(f"Insufficient stock in batches for product ID {product_id}.")
    
    # Update product stock from batch totals
    total_remaining = StockAddition.objects.filter(
        product_id=product_id
    ).aggregate(total=models.Sum('remaining_quantity'))['total'] or Decimal('0')
    
    Product.objects.filter(product_id=product_id).update(stock=total_remaining)
    
    # Update product price to next available batch
    update_product_price_from_fifo_batches(product_id)
```

### FIFO Features

1. **Strict Ordering**
   - Primary: `date_added` (oldest first)
   - Secondary: `addition_id` (lowest first)
   - Ensures consistent, predictable inventory rotation

2. **Multi-Batch Consumption**
   - A single sale can consume from multiple batches
   - Example: Selling 20 boxes when oldest batch has only 15
     - Deduct 15 from Batch A
     - Deduct 5 from Batch B

3. **Batch Depletion Handling**
   - When `remaining_quantity` reaches 0, batch is considered depleted
   - Product price automatically updates to next available batch's price
   - Maintains accurate costing for inventory valuation

4. **Stock Reconciliation**
   - Product stock = SUM(remaining_quantity) from all batches
   - Calculated after every FIFO deduction
   - Ensures data consistency between batches and product totals

---

## Real-Time Tracking Components

### 1. **Django Signals**
**Location:** `core/signals.py`

#### Signal: `check_low_stock_after_sale`
Triggered after every sale is recorded.

```python
@receiver(post_save, sender=Sale)
def check_low_stock_after_sale(sender, instance, created, **kwargs):
    """Check low stock after sale and send alert if needed"""
    if not created:
        return
    
    try:
        product = instance.product
        if product.stock <= 10 and product.status.lower() == 'active':
            send_low_stock_alert(product)
    except Exception as e:
        logger.error(f"Error scheduling low stock check: {str(e)}")
```

#### Signal: `check_low_stock_after_stock_update`
Triggered when product stock is updated.

```python
@receiver(post_save, sender=Product)
def check_low_stock_after_stock_update(sender, instance, created, **kwargs):
    """Automatically check for low stock alerts after stock is updated"""
    if not created:
        status_lower = str(instance.status or '').strip().lower()
        if instance.stock <= 10 and status_lower == 'active':
            send_low_stock_alert(instance)
```

**Signal Flow:**
```
Sale Created → Signal Fires → Check Stock → Send SMS Alert
Product Updated → Signal Fires → Check Stock → Send SMS Alert
```

---

### 2. **Atomic Transactions**
All stock operations use Django's `transaction.atomic()` to ensure data consistency.

#### Example: Stock Addition
```python
with transaction.atomic():
    # Create stock addition record
    StockAddition.objects.create(
        product=product,
        quantity=quantity_decimal,
        remaining_quantity=quantity_decimal,
        batch_id=batch_id,
        date_added=timezone.now()
    )
    
    # Update product stock atomically
    product.stock = models.F('stock') + quantity_decimal
    product.save()
    product.refresh_from_db(fields=['stock'])
```

**Why Atomic?**
- Prevents race conditions in concurrent transactions
- Ensures all-or-nothing operations (rollback on error)
- Maintains referential integrity between tables

---

### 3. **F() Expressions**
Django's `F()` expressions ensure database-level calculations.

```python
# Atomic increment (prevents race conditions)
product.stock = models.F('stock') + quantity_decimal
product.save()

# Instead of:
product.stock += quantity_decimal  # ❌ Race condition risk
product.save()
```

**Benefits:**
- Operations happen at database level
- Prevents "read-modify-write" race conditions
- Ensures accurate stock counts in high-concurrency scenarios

---

## Stock Transaction Flow

### Adding Stock

#### Endpoint: `POST /api/products/<product_id>/stock/add/`
**Location:** `core/views.py:2814-2889`

**Request:**
```json
{
  "quantity": "20",
  "supplier": "ABC Suppliers",
  "batch_id": "P286-STD-10-114"
}
```

**Process Flow:**
```
1. Validate product exists and is active
2. Convert quantity to Decimal
3. Generate batch_id if not provided
4. Create StockAddition record with:
   - quantity = input quantity
   - remaining_quantity = input quantity (all available)
   - date_added = current timestamp
5. Update product.stock atomically (+= quantity)
6. Refresh product from database
7. Check for low stock threshold
8. Log action with details
9. Return success response
```

**Response:**
```json
{
  "success": true,
  "message": "Stock added successfully",
  "new_stock": 45.5,
  "batch_id": "P286-STD-10-114"
}
```

**Real-Time Updates:**
- Product stock updated immediately in database
- `last_updated` timestamp auto-updated
- Signal fires to check if now above low-stock threshold
- Frontend refreshes via API call or page reload

---

### Recording Sale

#### Endpoint: `POST /record-sale/`
**Location:** `core/views.py:8251-8449`

**Request:**
```json
{
  "items": [
    {
      "product_id": 286,
      "quantity": 20,
      "price": 135.00
    }
  ],
  "customer_name": "John Doe",
  "address": "123 Main St",
  "contact_number": "09123456789",
  "amount_paid": 3500.00
}
```

**Process Flow:**
```
1. Validate all products and quantities
2. Calculate FIFO breakdown for each item:
   a. Fetch available batches (FIFO order)
   b. Allocate quantity across batches
   c. Build FIFO breakdown JSON
3. Begin atomic transaction
4. For each item:
   a. Create Sale record with FIFO breakdown
   b. Deduct stock using deduct_stock_fifo()
      - Updates batch remaining_quantity
      - Updates product.stock
      - Updates product.price if batch depleted
   c. Check for low stock alert
5. Calculate totals, VAT, discounts
6. Log transaction details
7. Commit transaction
8. Return receipt data
```

**FIFO Calculation Example:**
```python
# Selling 20 boxes when:
# Batch #114 (Jan 3): 15 boxes @ ₱120.00
# Batch #115 (Jan 5): 10 boxes @ ₱150.00

fifo_breakdown = [
  {
    "addition_id": 114,
    "batch_id": "P286-STD-10-114",
    "quantity": 15,        # Take all from oldest batch
    "price": 120.00,
    "subtotal": 1800.00,
    "date_added": "2026-01-03"
  },
  {
    "addition_id": 115,
    "batch_id": "P286-STD-10-115",
    "quantity": 5,         # Take remaining from next batch
    "price": 150.00,
    "subtotal": 750.00,
    "date_added": "2026-01-05"
  }
]

# Total: 15 + 5 = 20 boxes
# Total Cost: ₱1800 + ₱750 = ₱2550
# Average Cost: ₱2550 / 20 = ₱127.50 per box
```

**Response:**
```json
{
  "success": true,
  "message": "Sale recorded successfully",
  "sale_ids": [1234, 1235],
  "transaction_number": "TXN123456",
  "or_number": "OR123457",
  "total_amount": 3150.00,
  "items_sold": 2
}
```

---

### Voiding Sale (Stock Restoration)

#### Endpoint: `POST /sales/<sale_id>/void/`
**Location:** `core/views.py`

**Process Flow:**
```
1. Validate sale exists and not already voided
2. Parse FIFO breakdown from sale record
3. Begin atomic transaction
4. For each batch in FIFO breakdown:
   a. Restore quantity to batch.remaining_quantity
   b. Update batch record
5. Update product.stock (+= total_quantity)
6. Mark sale as voided
7. Set stock_restored = True
8. Log void action
9. Commit transaction
```

**Stock Restoration Logic:**
```python
# Original Sale: 20 boxes from 2 batches
# Batch #114: -15 boxes
# Batch #115: -5 boxes

# On Void:
# Batch #114: remaining_quantity += 15
# Batch #115: remaining_quantity += 5
# Product: stock += 20
```

---

### Manual Stock Decrease (Spoilage/Damage)

#### Endpoint: `POST /products/<product_id>/decrease/`
**Location:** `core/views.py:2120-2202`

**Request:**
```json
{
  "addition_id": 114,
  "amount": 5
}
```

**Process Flow:**
```
1. Fetch stock addition by addition_id
2. Validate sufficient remaining_quantity
3. Begin atomic transaction
4. Calculate decrease (min of amount and available)
5. Update batch:
   - remaining_quantity -= decrease
   - spoiled += decrease
6. Update product.stock -= decrease
7. If batch now depleted, update product price to next batch
8. Log decrease action
9. Commit transaction
```

**Use Cases:**
- Damaged goods
- Expired products
- Quality control removals
- Theft/loss reporting

---

## Low Stock Alerts

### Alert System Components

1. **Threshold Configuration**
   - Default: 10 units (boxes or kg)
   - Configurable per product: `product.low_stock_threshold`
   - System-wide setting: `SMSNotificationSettings.stock_threshold`

2. **Alert Triggers**
   - After every sale (via signal)
   - After stock addition/decrease
   - Manual product update

3. **Alert Conditions**
   ```python
   if product.stock <= low_stock_threshold and product.status == 'active':
       send_low_stock_alert(product)
   ```

### SMS Alert Function
**Location:** `core/signals.py:55+`

```python
def send_low_stock_alert(product):
    """Send low stock SMS alert"""
    # Get SMS settings
    settings = SMSNotificationSettings.get_settings()
    
    if not settings.stock_enabled:
        return  # Alerts disabled
    
    # Format message
    unit = 'kg' if product.quantity_unit == 'kg' else 'boxes'
    message = f"LOW STOCK ALERT: {product.name} - {product.stock} {unit} remaining"
    
    # Send SMS via Semaphore API
    send_sms(recipient_numbers, message)
    
    # Log SMS sent
    SMS.objects.create(
        product=product,
        message_type='stock_alert',
        message_content=message,
        sent_at=timezone.now()
    )
```

### Alert Dashboard
- Real-time badge on sidebar: "Restock Alerts: 5"
- Inventory page highlights low-stock items in orange/red
- Dashboard widget shows critical stock levels

---

## API Endpoints

### Product APIs

#### 1. **Get Active Products**
```
GET /api/products/active/
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "product_id": 286,
      "name": "Pomegranate",
      "variant": "Standard",
      "stock": 25.5,
      "quantity_unit": "10",
      "price": 135.00,
      "cost": 100.00,
      "status": "active",
      "low_stock_threshold": 10,
      "last_updated": "2026-01-05T14:30:00Z"
    }
  ]
}
```

**Usage:**
- Product selection dropdowns
- Real-time stock availability checks
- Pricing information

---

#### 2. **Get Stock Details (FIFO Batches)**
```
GET /api/products/<product_id>/stock/?page=1&page_size=10
```

**Response:**
```json
{
  "success": true,
  "meta": {
    "product_name": "Pomegranate (Standard) (10)",
    "quantity_unit": "10",
    "added_total": 100,
    "available_total": 45,
    "spoiled_total": 5,
    "latest_date": "2026-01-05",
    "earliest_date": "2026-01-01"
  },
  "groups": [
    {
      "addition_id": 115,
      "batch_id": "P286-STD-10-115",
      "quantity": 20,
      "remaining_quantity": 15,
      "spoiled": 0,
      "date_added": "2026-01-05",
      "supplier": "ABC Suppliers",
      "cost": 100.00,
      "price": 150.00
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 10,
    "total_pages": 3,
    "total_items": 25
  }
}
```

**Usage:**
- Stock details modal
- FIFO batch tracking
- Supplier history

---

#### 3. **Get Product Details**
```
GET /api/products/<product_id>/details/
```

**Response:**
```json
{
  "success": true,
  "data": {
    "product_id": 286,
    "name": "Pomegranate",
    "variant": "Standard",
    "stock": 25.5,
    "quantity_unit": "10",
    "price": 135.00,
    "cost": 100.00,
    "status": "active",
    "supplier": "ABC Suppliers",
    "low_stock_threshold": 10,
    "date_added": "2025-12-01",
    "last_updated": "2026-01-05T14:30:00Z",
    "sku": "POM-STD-10"
  }
}
```

---

### Stock Transaction APIs

#### 4. **Add Stock**
```
POST /api/products/<product_id>/stock/add/
```

**Request:**
```json
{
  "quantity": "20",
  "supplier": "ABC Suppliers",
  "cost": "100.00",
  "price": "150.00",
  "batch_id": "P286-STD-10-115"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Stock added successfully",
  "new_stock": 45.5,
  "batch_id": "P286-STD-10-115"
}
```

---

#### 5. **Decrease Stock (Spoilage)**
```
POST /products/<product_id>/decrease/
```

**Request:**
```json
{
  "addition_id": 114,
  "amount": 5
}
```

**Response:**
```json
{
  "success": true,
  "decreased": 5,
  "remaining": 10,
  "spoiled_total": 5
}
```

---

#### 6. **Record Sale**
```
POST /record-sale/
```

**Request:**
```json
{
  "items": [
    {
      "product_id": 286,
      "quantity": 20,
      "price": 135.00
    }
  ],
  "customer_name": "John Doe",
  "address": "123 Main St",
  "contact_number": "09123456789",
  "amount_paid": 3500.00,
  "discount_pct": 0,
  "discount_amount": 0
}
```

**Response:**
```json
{
  "success": true,
  "sale_ids": [1234],
  "transaction_number": "TXN123456",
  "or_number": "OR123457",
  "total_amount": 3150.00,
  "items_sold": 1
}
```

---

## Frontend Integration

### Real-Time Updates

#### 1. **Inventory Page Refresh**
**Location:** `templates/products_inventory_full.html`

```javascript
// Refresh data every 30 seconds
setInterval(() => {
    loadProducts();
}, 30000);

function loadProducts() {
    fetch('/api/products/active/')
        .then(r => r.json())
        .then(data => {
            updateProductTable(data.data);
            updateDashboardStats(data.stats);
        });
}
```

#### 2. **Stock Details Modal**
**Location:** `templates/stock_details.html`

```javascript
function loadStockDetails(productId, page = 1) {
    fetch(`/api/products/${productId}/stock/?page=${page}&page_size=10`)
        .then(r => r.json())
        .then(resp => {
            updateProductInfo(resp.meta);
            updateSummaryStats(resp.meta);
            renderStockBatches(resp.groups);
            updatePagination(resp.pagination);
        });
}
```

#### 3. **Product Selection (Sales)**
**Location:** `templates/record_sale.html`

```javascript
// Load active products on page load
function loadActiveProducts() {
    return fetch('/api/products/active/')
        .then(r => r.json())
        .then(data => {
            products = data.data;
            populateProductDropdowns();
        });
}

// Real-time stock check on quantity input
$('.stock-quantity').on('input', function() {
    const productId = $(this).closest('.item-row').find('.product-select').val();
    const quantity = parseFloat($(this).val()) || 0;
    const product = products.find(p => p.product_id == productId);
    
    if (product && quantity > product.stock) {
        showError('Insufficient stock available');
        $(this).addClass('is-invalid');
    }
});
```

---

### UI Indicators

#### Stock Level Colors
```javascript
function getStockStatusClass(stock, threshold) {
    if (stock === 0) return 'stock-out';        // Red
    if (stock <= threshold) return 'stock-low'; // Orange
    return 'stock-normal';                       // Green
}
```

**CSS:**
```css
.stock-out {
    color: #dc3545;
    font-weight: bold;
}

.stock-low {
    color: #fd7e14;
    font-weight: bold;
}

.stock-normal {
    color: #28a745;
}
```

#### Real-Time Badges
```html
<!-- Sidebar Badge -->
<span class="badge bg-danger">{{ restock_alerts }}</span>

<!-- Dashboard Widget -->
<div class="stat-card">
    <span class="stat-value" id="restockAlerts">{{ restock_alerts }}</span>
    <span class="stat-label">Restock Alerts</span>
</div>
```

---

## Data Consistency & Atomicity

### Transaction Guarantees

#### 1. **ACID Properties**
- **Atomicity**: All-or-nothing operations
- **Consistency**: Database constraints enforced
- **Isolation**: Concurrent transactions don't interfere
- **Durability**: Committed changes persist

#### 2. **Django Transaction Management**
```python
from django.db import transaction

@transaction.atomic
def record_sale_transaction(items, customer_data):
    """All operations succeed or all fail"""
    try:
        for item in items:
            # Create sale record
            sale = Sale.objects.create(...)
            
            # Deduct stock (FIFO)
            deduct_stock_fifo(item.product_id, item.quantity)
            
            # Update product
            product.refresh_from_db()
        
        # All succeeded, commit
        return {'success': True}
    except Exception as e:
        # Any failure, rollback all
        raise  # Transaction will rollback
```

#### 3. **Race Condition Prevention**
```python
# ❌ BAD: Race condition possible
product = Product.objects.get(pk=product_id)
product.stock += 10  # Read current value
product.save()       # Write new value
# If two requests happen simultaneously, one update is lost!

# ✅ GOOD: Database-level operation
product = Product.objects.get(pk=product_id)
product.stock = F('stock') + 10  # Database-level increment
product.save()
# Database handles concurrency correctly
```

---

### Data Validation

#### Stock Validation Rules
```python
# 1. Cannot sell more than available stock
if requested_quantity > product.stock:
    raise ValueError("Insufficient stock")

# 2. Cannot decrease more than batch remaining
if decrease_amount > batch.remaining_quantity:
    raise ValueError("Insufficient quantity in batch")

# 3. Stock cannot go negative
product.stock = max(Decimal('0'), calculated_stock)

# 4. Remaining quantity matches sum of batches
total_remaining = StockAddition.objects.filter(
    product_id=product_id
).aggregate(total=Sum('remaining_quantity'))['total']
assert product.stock == total_remaining
```

---

## Performance Optimizations

### 1. **Database Indexes**
```python
class StockAddition(models.Model):
    class Meta:
        indexes = [
            # FIFO queries: ORDER BY date_added, addition_id
            models.Index(fields=['product', 'date_added'], 
                        name='idx_sa_product_date'),
            
            # Batch lookups
            models.Index(fields=['batch_id'], 
                        name='idx_sa_batch'),
        ]
```

### 2. **Query Optimization**
```python
# ❌ BAD: N+1 query problem
products = Product.objects.all()
for product in products:
    latest_batch = product.stockaddition_set.latest('date_added')  # Extra query per product!

# ✅ GOOD: Prefetch related data
products = Product.objects.prefetch_related('stockaddition_set').all()
for product in products:
    latest_batch = product.stockaddition_set.all()[0]  # No extra query
```

### 3. **Pagination**
```python
# Stock details endpoint uses pagination
page_size = 10  # Only load 10 batches at a time
offset = (page - 1) * page_size
batches = StockAddition.objects.filter(
    product_id=product_id
).order_by('-date_added')[offset:offset+page_size]
```

### 4. **Caching Strategy**
```python
# Cache active products list for 5 minutes
from django.core.cache import cache

def get_active_products():
    cache_key = 'active_products_list'
    products = cache.get(cache_key)
    
    if products is None:
        products = Product.objects.filter(status='active').all()
        cache.set(cache_key, products, timeout=300)  # 5 min
    
    return products

# Invalidate cache on product update
@receiver(post_save, sender=Product)
def invalidate_products_cache(sender, instance, **kwargs):
    cache.delete('active_products_list')
```

### 5. **Async Low Stock Checks**
```python
# Check low stock asynchronously to avoid blocking main request
from threading import Thread

def async_low_stock_check(product_id):
    def check():
        product = Product.objects.get(pk=product_id)
        if product.stock <= product.low_stock_threshold:
            send_low_stock_alert(product)
    
    thread = Thread(target=check)
    thread.daemon = True
    thread.start()
```

---

## System Flow Diagrams

### Stock Addition Flow
```
User Input (Add Stock Page)
          ↓
POST /api/products/<id>/stock/add/
          ↓
Validate Product & Quantity
          ↓
[BEGIN TRANSACTION]
          ↓
Create StockAddition Record
  - quantity: 20
  - remaining_quantity: 20
  - batch_id: P286-STD-10-115
  - date_added: 2026-01-05
          ↓
Update Product.stock
  - stock = F('stock') + 20
          ↓
Refresh Product from DB
          ↓
Check Low Stock Threshold
          ↓
Log Action
          ↓
[COMMIT TRANSACTION]
          ↓
Signal: post_save(Product) → Check if alert needed
          ↓
Return Success Response
          ↓
Frontend Refreshes Data
```

---

### Sale Recording Flow
```
User Input (Record Sale Page)
          ↓
Select Products & Quantities
          ↓
Proceed to Payment
          ↓
Calculate FIFO Breakdown for Each Item
  - Fetch batches (FIFO order)
  - Allocate quantities
  - Calculate costs
          ↓
Confirm Payment
          ↓
POST /record-sale/
          ↓
[BEGIN TRANSACTION]
          ↓
For Each Item:
  ├─ Create Sale Record
  │   - quantity: 20
  │   - price: 135.00
  │   - fifo_breakdown: [...]
  │   - transaction_number: TXN123456
  ├─ Deduct Stock FIFO
  │   ├─ Update Batch #114: remaining -= 15
  │   ├─ Update Batch #115: remaining -= 5
  │   └─ Update Product: stock -= 20
  └─ Check Low Stock
          ↓
Calculate Totals, VAT, Discounts
          ↓
Log Transaction
          ↓
[COMMIT TRANSACTION]
          ↓
Signals Fire:
  ├─ post_save(Sale) → Check low stock
  └─ post_save(Product) → Check low stock
          ↓
Return Receipt Data
          ↓
Display Receipt
```

---

### FIFO Batch Consumption Flow
```
Sell 20 Boxes
          ↓
deduct_stock_fifo(product_id=286, quantity=20)
          ↓
Fetch Available Batches (FIFO Order):
  - Batch #114 (Jan 3): 15 boxes remaining
  - Batch #115 (Jan 5): 25 boxes remaining
          ↓
Deduct from Batch #114:
  - deduct_amount = min(20, 15) = 15
  - remaining_quantity = 15 - 15 = 0
  - Save batch
  - remaining_to_deduct = 20 - 15 = 5
          ↓
Deduct from Batch #115:
  - deduct_amount = min(5, 25) = 5
  - remaining_quantity = 25 - 5 = 20
  - Save batch
  - remaining_to_deduct = 5 - 5 = 0
          ↓
Update Product Stock:
  - stock = SUM(remaining_quantity) = 0 + 20 = 20
          ↓
Update Product Price:
  - Batch #114 depleted, use Batch #115 price
  - product.price = 150.00
          ↓
Return FIFO Breakdown:
  [
    {batch: 114, qty: 15, price: 120, subtotal: 1800},
    {batch: 115, qty: 5, price: 150, subtotal: 750}
  ]
```

---

## Best Practices & Guidelines

### 1. **Always Use Atomic Transactions**
```python
# For any multi-step operation
with transaction.atomic():
    # Create records
    # Update stock
    # Log actions
```

### 2. **Always Refresh After F() Expressions**
```python
product.stock = F('stock') + quantity
product.save()
product.refresh_from_db(fields=['stock'])  # Get actual value
```

### 3. **Validate Stock Before Operations**
```python
# Check availability before deducting
if product.stock < requested_quantity:
    raise ValueError("Insufficient stock")
```

### 4. **Log All Stock Movements**
```python
log_action(
    request,
    'Stock decreased',
    f'Removed {quantity} boxes from product {product.name}'
)
```

### 5. **Handle Decimal vs Integer Units**
```python
quantity_unit = (product.quantity_unit or '').lower()
if quantity_unit == 'kg':
    # Handle as decimal (15.50 kg)
    quantity = Decimal(str(quantity))
else:
    # Handle as integer (20 boxes)
    quantity = int(quantity)
```

### 6. **Test Concurrent Operations**
```python
# Test race conditions
from threading import Thread

def test_concurrent_sales():
    threads = []
    for i in range(10):
        t = Thread(target=record_sale, args=(product_id, 1))
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    # Verify stock is correct
    product.refresh_from_db()
    assert product.stock == initial_stock - 10
```

---

## Monitoring & Debugging

### Key Metrics to Track

1. **Stock Accuracy**
   - Product.stock vs SUM(StockAddition.remaining_quantity)
   - Should always match
   - Run periodic reconciliation jobs

2. **Low Stock Alerts**
   - Number of products below threshold
   - SMS delivery rate
   - Alert response time

3. **Transaction Performance**
   - Average sale recording time
   - FIFO calculation duration
   - Database query counts

4. **FIFO Integrity**
   - Batch depletion order (should be chronological)
   - No negative remaining_quantity
   - Price updates on batch depletion

### Debugging Tools

#### Stock Reconciliation Script
```python
def reconcile_stock():
    """Verify product stock matches batch totals"""
    products = Product.objects.all()
    discrepancies = []
    
    for product in products:
        batch_total = StockAddition.objects.filter(
            product=product
        ).aggregate(total=Sum('remaining_quantity'))['total'] or 0
        
        if product.stock != batch_total:
            discrepancies.append({
                'product': product.name,
                'product_stock': product.stock,
                'batch_total': batch_total,
                'difference': product.stock - batch_total
            })
    
    return discrepancies
```

#### FIFO Order Verification
```python
def verify_fifo_order():
    """Ensure batches are depleted in FIFO order"""
    products = Product.objects.all()
    violations = []
    
    for product in products:
        batches = StockAddition.objects.filter(
            product=product
        ).order_by('date_added', 'addition_id')
        
        found_depleted = False
        for batch in batches:
            if found_depleted and batch.remaining_quantity > 0:
                violations.append({
                    'product': product.name,
                    'issue': 'Non-FIFO depletion detected'
                })
                break
            if batch.remaining_quantity == 0:
                found_depleted = True
    
    return violations
```

---

## Summary

The StockWise real-time inventory tracking system provides:

✅ **Accurate FIFO Inventory Management**
- Strict date-based batch ordering
- Automatic price updates on batch depletion
- Full traceability of stock movements

✅ **Real-Time Stock Updates**
- Atomic database transactions
- Signal-based automatic alerts
- Frontend refresh mechanisms

✅ **Comprehensive Data Integrity**
- Transaction safety with rollbacks
- Race condition prevention
- Validation at every step

✅ **Performance & Scalability**
- Database indexes for fast queries
- Pagination for large datasets
- Async operations for non-blocking tasks

✅ **Audit Trail & Logging**
- Complete action logs
- FIFO breakdown storage
- User attribution for all changes

This system ensures that stock levels are always accurate, up-to-date, and properly tracked across all operations, from receiving inventory to recording sales and handling returns.

---

**Last Updated:** January 5, 2026  
**System Version:** StockWise v2.0  
**Documentation Author:** AI Assistant

