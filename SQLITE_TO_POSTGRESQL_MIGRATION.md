# SQLite to PostgreSQL Migration Guide

This guide shows you how to migrate your data from SQLite (`db.sqlite3`) to PostgreSQL on DigitalOcean.

## Method 1: Using Django dumpdata/loaddata (Recommended)

This is the cleanest method using Django's built-in commands.

### Step 1: Export Data from SQLite

On your DigitalOcean service (where SQLite is currently active):

```bash
# Export all data to JSON
python manage.py dumpdata --exclude auth.permission --exclude contenttypes > sqlite_export.json

# Or exclude more system tables if needed
python manage.py dumpdata --exclude auth.permission --exclude contenttypes --exclude admin.logentry > sqlite_export.json
```

**Note**: The `--exclude` flags skip system tables that Django will recreate automatically.

### Step 2: Switch to PostgreSQL

1. **Get your PostgreSQL connection string** from DigitalOcean Dashboard:
   - Go to your Managed Database
   - Copy the **Connection String** or **Internal Connection URL**

2. **Set DATABASE_URL environment variable** in your DigitalOcean App Platform:
   - Go to your App → Settings → Environment Variables
   - Add or update `DATABASE_URL` with your PostgreSQL connection string
   - Format: `postgresql://user:password@host:port/database`

3. **Redeploy your app** (or restart) so it picks up the new database URL

### Step 3: Run Migrations on PostgreSQL

```bash
# Create all tables in PostgreSQL
python manage.py migrate
```

This will create all the necessary tables in your PostgreSQL database.

### Step 4: Import Data into PostgreSQL

```bash
# Load the exported data
python manage.py loaddata sqlite_export.json
```

### Step 5: Fix Sequences

**IMPORTANT**: Always run this after importing data to prevent duplicate key errors:

```bash
python manage.py fix_sequences
```

### Step 6: Verify Migration

```bash
python manage.py shell
```

Then in the Python shell:
```python
from core.models import Product, Sale, AppUser, ActionLog

print(f"Products: {Product.objects.count()}")
print(f"Sales: {Sale.objects.count()}")
print(f"Users: {AppUser.objects.count()}")
print(f"Action Logs: {ActionLog.objects.count()}")
```

---

## Method 2: Using Backup/Restore System

If you prefer using the backup system:

### Step 1: Create Backup from SQLite

```bash
python manage.py backup_system
```

This creates a ZIP file in `backups/` directory.

### Step 2: Switch to PostgreSQL

1. Set `DATABASE_URL` environment variable to your PostgreSQL connection string
2. Redeploy/restart your app

### Step 3: Run Migrations

```bash
python manage.py migrate
```

### Step 4: Restore Backup

```bash
# Restore from the backup ZIP
python manage.py restore_backup backups/stockwise_backup_YYYYMMDD_HHMMSS.zip
```

### Step 5: Fix Sequences

```bash
python manage.py fix_sequences
```

---

## Method 3: Direct SQLite File Access (If SQLite file is accessible)

If you can access the SQLite file directly on the server:

### Step 1: Temporarily Use SQLite

Make sure your `DATABASE_URL` is not set (or points to SQLite), so Django uses SQLite.

### Step 2: Export Data

```bash
python manage.py dumpdata --exclude auth.permission --exclude contenttypes > sqlite_export.json
```

### Step 3: Switch to PostgreSQL

1. Set `DATABASE_URL` to PostgreSQL connection string
2. Redeploy/restart

### Step 4: Import Data

```bash
python manage.py migrate
python manage.py loaddata sqlite_export.json
python manage.py fix_sequences
```

---

## Quick Command Reference

```bash
# 1. Export from SQLite
python manage.py dumpdata --exclude auth.permission --exclude contenttypes > sqlite_export.json

# 2. Switch DATABASE_URL to PostgreSQL (in environment variables)

# 3. Create tables in PostgreSQL
python manage.py migrate

# 4. Import data
python manage.py loaddata sqlite_export.json

# 5. Fix sequences (CRITICAL!)
python manage.py fix_sequences

# 6. Verify
python manage.py shell
# Then: Product.objects.count(), Sale.objects.count(), etc.
```

---

## Troubleshooting

### "No such table" errors during dumpdata

If you get errors about missing tables:
```bash
# Run migrations first on SQLite
python manage.py migrate

# Then export
python manage.py dumpdata --exclude auth.permission --exclude contenttypes > sqlite_export.json
```

### "Duplicate key" errors after import

Always run `fix_sequences`:
```bash
python manage.py fix_sequences
```

### Large database export issues

If your database is very large:
```bash
# Export in chunks by app
python manage.py dumpdata core > core_data.json
python manage.py dumpdata auth > auth_data.json
# etc.

# Then load each separately
python manage.py loaddata core_data.json
python manage.py loaddata auth_data.json
```

### Connection errors to PostgreSQL

1. **Check DATABASE_URL format:**
   ```
   postgresql://username:password@host:port/database
   ```

2. **Verify database is accessible:**
   - Check database status in DigitalOcean Dashboard
   - Ensure database is not paused
   - Verify network/firewall settings

3. **Test connection:**
   ```bash
   python manage.py dbshell
   ```

### Foreign key constraint errors

If you get foreign key errors during import:
```bash
# Disable foreign key checks temporarily (PostgreSQL)
python manage.py shell
```

Then in shell:
```python
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute("SET session_replication_role = 'replica';")
    
# Then run loaddata
# Then re-enable:
with connection.cursor() as cursor:
    cursor.execute("SET session_replication_role = 'origin';")
```

Or use the `--natural-foreign` flag:
```bash
python manage.py dumpdata --natural-foreign --exclude auth.permission --exclude contenttypes > sqlite_export.json
```

---

## Important Notes

1. **Always backup before migration**: Keep a copy of your SQLite file
2. **Test in staging first**: If possible, test the migration on a test database
3. **Fix sequences**: Always run `fix_sequences` after importing data
4. **Verify data**: Check record counts and test critical features after migration
5. **Keep SQLite file**: Don't delete the SQLite file until you've verified everything works

---

## After Migration

Once migration is complete and verified:

1. **Remove SQLite file** (optional, after verification):
   ```bash
   rm db.sqlite3
   ```

2. **Update .gitignore** to exclude SQLite if needed:
   ```
   db.sqlite3
   *.sqlite3
   ```

3. **Monitor for issues**: Watch logs for any database-related errors

4. **Set up automated backups** for PostgreSQL:
   - Use DigitalOcean's automated backups
   - Or schedule regular backups using `backup_system` command

