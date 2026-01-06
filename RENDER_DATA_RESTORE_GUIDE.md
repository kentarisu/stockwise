# Render Data Restore Guide

This guide explains how to restore your local database to Render hosting using the backup/restore system.

## Overview

Since Render's free tier doesn't provide shell access, we use the build command to automatically restore data from a backup file during deployment.

## Step-by-Step Instructions

### Step 1: Create a Fresh Backup from Local Database

Run this command in your local environment:

```bash
python manage.py backup_system
```

This will create a backup file in the `backups/` folder with a timestamp, like:
- `backups/stockwise_backup_20260107_050655.zip`

### Step 2: Copy Backup to Fixtures Folder

Copy the newest backup file to the fixtures folder and rename it:

```bash
# Windows PowerShell
Copy-Item backups\stockwise_backup_20260107_050655.zip fixtures\production_backup.zip

# Or manually copy and rename in File Explorer
```

**Important:** The file MUST be named `production_backup.zip` and placed in the `fixtures/` folder.

### Step 3: Commit and Push to Git

```bash
git add fixtures/production_backup.zip
git add core/management/commands/restore_from_fixture_backup.py
git commit -m "Add production database backup for deployment"
git push origin main
```

**Note:** Make sure your `.gitignore` doesn't exclude the fixtures folder or `.zip` files in fixtures.

### Step 4: Update Render Build Command

Go to your Render dashboard → Settings → Build & Deploy

**Replace your current build command with:**

```bash
pip install -r requirements.txt && python manage.py migrate --noinput && python manage.py restore_from_fixture_backup && python manage.py collectstatic --noinput
```

**What this does:**
1. Installs Python dependencies
2. Runs database migrations (creates/updates tables)
3. Restores data from `fixtures/production_backup.zip` 
4. Collects static files for serving

### Step 5: Deploy

Click "Manual Deploy" → "Deploy latest commit" in Render dashboard, or just push to your git repository if auto-deploy is enabled.

The restore will happen automatically during the build process!

## How It Works

### The Restore Process:

1. **`restore_from_fixture_backup` command** looks for `fixtures/production_backup.zip`
2. If found, it calls the existing `restore_backup` command with `--force` flag
3. The restore command:
   - Preserves existing user accounts (if any)
   - Clears all other data
   - Loads data from the backup JSON file
   - Restores media files
   - Fixes database sequences

### Important Notes:

- ✅ **User accounts are preserved** - Current production users won't be deleted
- ✅ **If backup file is missing** - Build continues without error (useful for first deployment)
- ✅ **All transactional data is replaced** - Sales, products, stock additions, etc.
- ⚠️ **Data is restored on EVERY deployment** - Only suitable if you want to overwrite production data

## Alternative: One-Time Data Restore

If you only want to restore data ONCE (not on every deployment), use this build command instead:

```bash
pip install -r requirements.txt && python manage.py migrate --noinput && python manage.py load_initial_data --force && python manage.py collectstatic --noinput
```

Then update your `fixtures/initial_data.json.zip` with a fresh export:

```bash
python manage.py dumpdata --natural-foreign --natural-primary --exclude auth.permission --exclude contenttypes --indent 2 > fixtures/initial_data.json

# Compress it (optional, for smaller git commits)
# Use 7zip, WinRAR, or PowerShell:
Compress-Archive -Path fixtures\initial_data.json -DestinationPath fixtures\initial_data.json.zip -Force
```

## Troubleshooting

### Backup file too large for Git?

If your backup exceeds GitHub's 100MB file limit:

1. Use Git LFS (Large File Storage):
   ```bash
   git lfs install
   git lfs track "fixtures/production_backup.zip"
   git add .gitattributes
   git add fixtures/production_backup.zip
   git commit -m "Add backup with Git LFS"
   git push
   ```

2. Or, host the backup file elsewhere (AWS S3, Dropbox, etc.) and download it in the build command:
   ```bash
   pip install -r requirements.txt && python manage.py migrate --noinput && curl -o /tmp/backup.zip https://your-backup-url.com/backup.zip && python manage.py restore_backup /tmp/backup.zip --force && python manage.py collectstatic --noinput
   ```

### "Backup file not found" error?

- Make sure the file is named exactly `production_backup.zip`
- Make sure it's in the `fixtures/` folder
- Make sure it was committed and pushed to git
- Check your `.gitignore` doesn't exclude it

### Restore taking too long?

If your database is very large, the restore might timeout. Consider:

1. Reducing backup size by excluding unnecessary data
2. Using a separate database restore service
3. Upgrading to a paid Render plan with shell access

## Files Modified

- `core/management/commands/backup_system.py` - Fixed Windows encoding issues
- `core/management/commands/restore_from_fixture_backup.py` - New command for automatic restore
- `fixtures/production_backup.zip` - Your production data backup (you create this)

## Updating Production Data Regularly

To keep your production data in sync with local:

1. Create a fresh backup locally
2. Copy to `fixtures/production_backup.zip`
3. Commit and push
4. Render will auto-deploy and restore the new data

You can automate this with a script if needed!

