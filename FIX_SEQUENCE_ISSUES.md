# Fix PostgreSQL Sequence Issues

## Problem
You're seeing errors like:
- `duplicate key value violates unique constraint "products_pkey" DETAIL: Key (product_id)=(307) already exists.`
- `duplicate key value violates unique constraint "stock_additions_pkey" DETAIL: Key (addition_id)=(104) already exists.`
- `duplicate key value violates unique constraint "sales_pkey" DETAIL: Key (sale_id)=(102) already exists.`

This happens when PostgreSQL sequences get out of sync with the actual data in your tables, usually after data migration or bulk imports.

## Solution 1: Use Django Management Command (Recommended)

Run this command on your hosting server:

```bash
python manage.py fix_sequences
```

This will automatically fix all sequences for all tables.

To fix a specific table:
```bash
python manage.py fix_sequences --table products
python manage.py fix_sequences --table sales
python manage.py fix_sequences --table stock_additions
```

## Solution 2: Direct SQL Fix (If command doesn't work)

Connect to your PostgreSQL database and run:

```sql
-- Fix products sequence
SELECT setval('products_product_id_seq', (SELECT COALESCE(MAX(product_id), 0) + 1 FROM products), false);

-- Fix stock_additions sequence
SELECT setval('stock_additions_addition_id_seq', (SELECT COALESCE(MAX(addition_id), 0) + 1 FROM stock_additions), false);

-- Fix sales sequence
SELECT setval('sales_sale_id_seq', (SELECT COALESCE(MAX(sale_id), 0) + 1 FROM sales), false);
```

## Solution 3: Fix All Sequences at Once (SQL)

```sql
-- Fix all sequences for core tables
DO $$
DECLARE
    r RECORD;
    max_id INTEGER;
    seq_name TEXT;
BEGIN
    FOR r IN 
        SELECT table_name, column_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
        AND column_default LIKE 'nextval%'
        AND table_name IN ('products', 'sales', 'stock_additions', 'action_logs')
    LOOP
        -- Get sequence name from column default
        SELECT pg_get_serial_sequence(r.table_name, r.column_name) INTO seq_name;
        
        IF seq_name IS NOT NULL THEN
            -- Get max ID
            EXECUTE format('SELECT COALESCE(MAX(%I), 0) FROM %I', r.column_name, r.table_name) INTO max_id;
            
            -- Reset sequence
            EXECUTE format('SELECT setval(%L, %s, false)', seq_name, max_id + 1);
            
            RAISE NOTICE 'Fixed sequence % for table %.% (max_id: %)', seq_name, r.table_name, r.column_name, max_id;
        END IF;
    END LOOP;
END $$;
```

## Prevention

The code already has automatic sequence reset when duplicate key errors occur, but it's better to fix sequences proactively. Consider:

1. Running `fix_sequences` after any bulk data operations
2. Running `fix_sequences` after database migrations
3. Setting up a periodic task to check and fix sequences

## Verification

After fixing, verify the sequences are correct:

```sql
-- Check current sequence values vs max IDs
SELECT 
    'products' as table_name,
    (SELECT last_value FROM products_product_id_seq) as sequence_value,
    (SELECT MAX(product_id) FROM products) as max_id
UNION ALL
SELECT 
    'sales',
    (SELECT last_value FROM sales_sale_id_seq),
    (SELECT MAX(sale_id) FROM sales)
UNION ALL
SELECT 
    'stock_additions',
    (SELECT last_value FROM stock_additions_addition_id_seq),
    (SELECT MAX(addition_id) FROM stock_additions);
```

The sequence_value should be >= max_id for each table.

