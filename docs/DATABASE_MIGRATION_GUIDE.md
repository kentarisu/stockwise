# Database Migration Guide: Local to DigitalOcean

This guide walks you through migrating your StockWise database from local SQLite to DigitalOcean PostgreSQL.

## Prerequisites

1. **DigitalOcean Database Created**
   - Create a PostgreSQL database cluster in DigitalOcean
   - Note down the connection details (host, port, database name, username, password)

2. **Local Tools Installed**
   - `pg_dump` and `psql` (PostgreSQL client tools)
   - Or use Python scripts (included below)

## Method 1: Using Django's dumpdata/loaddata (Recommended)

This is the safest method as it uses Django's native serialization.

### Step 1: Export Data from Local Database

On your local machine:

```bash
# Export all data to JSON
python manage.py dumpdata --exclude auth.permission --exclude contenttypes > local_db_backup.json

# Or export specific apps only (faster, smaller file)
python manage.py dumpdata core stockwise_qr.qrstock > local_db_backup.json
```

### Step 2: Configure DigitalOcean Database Connection

On your DigitalOcean server, set the `DATABASE_URL` environment variable:

```bash
# SSH into your DigitalOcean droplet
ssh your_user@your_droplet_ip

# Edit your .env file or set environment variable
nano .env

# Add this line (replace with your actual database credentials):
DATABASE_URL=postgresql://username:password@host:port/database_name?sslmode=require
```

**Example:**
```
DATABASE_URL=postgresql://doadmin:your_password@db-postgresql-nyc1-12345.db.ondigitalocean.com:25060/defaultdb?sslmode=require
```

### Step 3: Run Migrations on Production

```bash
# On your DigitalOcean server
cd /path/to/your/project
python manage.py migrate
```

### Step 4: Load Data into Production Database

```bash
# Transfer the backup file to your server first
# Using SCP from your local machine:
scp local_db_backup.json your_user@your_droplet_ip:/path/to/your/project/

# Then on the server, load the data:
python manage.py loaddata local_db_backup.json
```

### Step 5: Verify Migration

```bash
# Check data counts
python manage.py shell
```

```python
from core.models import Product, Sale, AppUser
print(f"Products: {Product.objects.count()}")
print(f"Sales: {Sale.objects.count()}")
print(f"Users: {AppUser.objects.count()}")
```

---

## Method 2: Direct SQLite to PostgreSQL Migration

If you prefer a direct database-to-database migration:

### Step 1: Install Required Tools

```bash
# Install pgloader (handles SQLite to PostgreSQL conversion)
# On Ubuntu/Debian:
sudo apt-get update
sudo apt-get install pgloader

# Or use Python script (see below)
```

### Step 2: Export SQLite Schema and Data

```bash
# Create a SQL dump from SQLite
sqlite3 db.sqlite3 .dump > sqlite_dump.sql
```

### Step 3: Convert and Import to PostgreSQL

**Option A: Using pgloader**

```bash
pgloader sqlite:///path/to/db.sqlite3 postgresql://username:password@host:port/database_name
```

**Option B: Using Python Script**

Create a migration script:

```python
# migrate_db.py
import sqlite3
import psycopg2
from psycopg2.extras import execute_values

# SQLite connection
sqlite_conn = sqlite3.connect('db.sqlite3')
sqlite_cur = sqlite_conn.cursor()

# PostgreSQL connection (from DATABASE_URL)
import os
from dj_database_url import parse
db_url = os.getenv('DATABASE_URL')
db_config = parse(db_url)

pg_conn = psycopg2.connect(
    host=db_config['HOST'],
    port=db_config['PORT'],
    database=db_config['NAME'],
    user=db_config['USER'],
    password=db_config['PASSWORD'],
    sslmode='require'
)
pg_cur = pg_conn.cursor()

# Migrate data table by table
tables = ['core_product', 'core_sale', 'core_appuser', 'core_stockaddition', 
          'core_pricingrecommendation', 'core_pricechangehistory']

for table in tables:
    # Get data from SQLite
    sqlite_cur.execute(f'SELECT * FROM {table}')
    rows = sqlite_cur.fetchall()
    
    if rows:
        # Get column names
        sqlite_cur.execute(f'PRAGMA table_info({table})')
        columns = [col[1] for col in sqlite_cur.fetchall()]
        
        # Insert into PostgreSQL
        cols_str = ', '.join(columns)
        placeholders = ', '.join(['%s'] * len(columns))
        insert_query = f'INSERT INTO {table} ({cols_str}) VALUES ({placeholders})'
        
        pg_cur.executemany(insert_query, rows)
        print(f'Migrated {len(rows)} rows from {table}')

pg_conn.commit()
pg_cur.close()
pg_conn.close()
sqlite_cur.close()
sqlite_conn.close()
```

---

## Method 3: Using Django's Database Router (Advanced)

For zero-downtime migration:

### Step 1: Configure Multiple Databases

In `settings.py`, temporarily add:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'production_db',
        # ... PostgreSQL config
    },
    'sqlite': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

### Step 2: Copy Data Using Django ORM

```python
# migrate_data.py
from django.db import connections
from core.models import Product, Sale

# Read from SQLite
Product.objects.using('sqlite').all()
Sale.objects.using('sqlite').all()

# Write to PostgreSQL
for product in Product.objects.using('sqlite').all():
    Product.objects.using('default').create(**product.__dict__)
```

---

## Troubleshooting

### Issue: "relation does not exist"
**Solution:** Run migrations first:
```bash
python manage.py migrate
```

### Issue: "column already exists" / "DuplicateColumn" error
**Error:** `psycopg2.errors.DuplicateColumn: column "pricing_time" of relation "sms_notification_settings" already exists`

**Solution:** This happens when migrations try to add columns that already exist. The migration `0041_add_pricing_fields_to_sms_notification_settings` has been fixed to check for existing columns. 

**Quick Fix Options:**

**Option 1: Mark migration as applied (if columns already exist)**
```bash
# Check if columns exist in database
python manage.py dbshell
```
```sql
SELECT column_name FROM information_schema.columns 
WHERE table_name='sms_notification_settings' 
AND column_name IN ('pricing_time', 'pricing_frequency_days');
-- If both columns exist, mark migration as fake:
```
```bash
python manage.py migrate core 0041 --fake
```

**Option 2: Manually add missing columns (if only some exist)**
```sql
-- In PostgreSQL shell
ALTER TABLE sms_notification_settings 
ADD COLUMN IF NOT EXISTS pricing_time VARCHAR(5) DEFAULT '08:00';

ALTER TABLE sms_notification_settings 
ADD COLUMN IF NOT EXISTS pricing_frequency_days INTEGER DEFAULT 3;
```
Then mark migration as applied:
```bash
python manage.py migrate core 0041 --fake
```

**Option 3: Remove duplicate columns and re-run migration**
```sql
-- Only if you're sure the columns are duplicates
ALTER TABLE sms_notification_settings DROP COLUMN IF EXISTS pricing_time;
ALTER TABLE sms_notification_settings DROP COLUMN IF EXISTS pricing_frequency_days;
```
Then run migration normally:
```bash
python manage.py migrate
```

### Issue: "duplicate key value violates unique constraint"
**Solution:** Clear existing data or reset sequences:
```sql
-- In PostgreSQL
TRUNCATE TABLE core_product, core_sale CASCADE;
ALTER SEQUENCE core_product_product_id_seq RESTART WITH 1;
```

### Issue: "SSL connection required"
**Solution:** Ensure `?sslmode=require` is in your DATABASE_URL

### Issue: "authentication failed"
**Solution:** Verify credentials and ensure your DigitalOcean droplet's IP is whitelisted in the database firewall

### Issue: Data type mismatches
**Solution:** SQLite is more lenient. Check for:
- Boolean fields (SQLite uses 0/1, PostgreSQL uses true/false)
- Date formats
- Decimal precision

### Issue: Migration conflicts or out-of-order migrations
**Solution:** If migrations are out of sync:
```bash
# Show migration status
python manage.py showmigrations

# Fake migrations that are already applied
python manage.py migrate core 0041 --fake

# Or reset specific app migrations (CAREFUL - backup first!)
python manage.py migrate core zero  # Unapplies all migrations
python manage.py migrate core       # Reapplies all migrations
```

---

## Post-Migration Checklist

- [ ] Verify all tables exist: `python manage.py showmigrations`
- [ ] Check data counts match local database
- [ ] Test critical functionality (login, sales, inventory)
- [ ] Update `ALLOWED_HOSTS` in settings.py
- [ ] Set `DEBUG=False` for production
- [ ] Configure static files serving
- [ ] Set up database backups on DigitalOcean
- [ ] Test database connection from application

---

## DigitalOcean Specific Notes

1. **Connection String Format:**
   ```
   postgresql://username:password@host:port/database?sslmode=require
   ```

2. **Firewall Configuration:**
   - Go to DigitalOcean Dashboard → Databases → Your Database → Settings
   - Add your droplet's IP to "Trusted Sources"

3. **Backup Configuration:**
   - DigitalOcean automatically backs up managed databases
   - Configure backup retention in database settings

4. **Connection Pooling:**
   - For high traffic, consider using PgBouncer
   - Update `DATABASE_URL` to point to PgBouncer port

---

## Quick Reference Commands

```bash
# Export local data
python manage.py dumpdata > backup.json

# Transfer to server
scp backup.json user@server:/path/

# On server: Load data
python manage.py loaddata backup.json

# Check migration status
python manage.py showmigrations

# Run migrations
python manage.py migrate

# Create superuser (if needed)
python manage.py createsuperuser
```

---

## Need Help?

If you encounter issues:
1. Check Django logs: `tail -f /var/log/django/error.log`
2. Check PostgreSQL logs in DigitalOcean dashboard
3. Verify environment variables: `python manage.py shell` → `import os; print(os.getenv('DATABASE_URL'))`
4. Test connection: `python manage.py dbshell`
