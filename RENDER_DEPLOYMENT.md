# Render Deployment Guide for StockWise

This guide will help you deploy StockWise to Render hosting.

## Prerequisites

1. A Render account (sign up at https://render.com)
2. Your code pushed to a Git repository (GitHub, GitLab, or Bitbucket)
3. A backup of your database from DigitalOcean (if migrating)

## Step 1: Create a PostgreSQL Database on Render

1. Go to your Render Dashboard
2. Click "New +" → "PostgreSQL"
3. Configure:
   - **Name**: `stockwise-db`
   - **Database**: `stockwise`
   - **User**: `stockwise_user`
   - **Plan**: Starter (or higher based on your needs)
4. Note the **Internal Database URL** (you'll need this later)

## Step 2: Deploy the Web Service

### Option A: Using render.yaml (Recommended)

1. Connect your Git repository to Render
2. Render will automatically detect the `render.yaml` file
3. The web service and worker will be created automatically

### Option B: Manual Setup

1. Go to Render Dashboard → "New +" → "Web Service"
2. Connect your Git repository
3. Configure:
   - **Name**: `stockwise-web`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt && python manage.py collectstatic --noinput`
   - **Start Command**: `gunicorn stockwise_py.wsgi --bind 0.0.0.0:$PORT --workers 3`
4. Add Environment Variables (see Step 4 below)

## Step 3: Create Background Worker

1. Go to Render Dashboard → "New +" → "Background Worker"
2. Connect the same Git repository
3. Configure:
   - **Name**: `stockwise-worker`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python sms_scheduler.py`
4. Add Environment Variables (see Step 4 below)

## Step 4: Environment Variables

Add these environment variables to **both** the web service and worker:

### Required Variables

- `SECRET_KEY`: Generate a secure Django secret key (Render can auto-generate this)
- `DEBUG`: Set to `false` for production
- `MAINTENANCE_MODE`: Set to `false` for production
- `DATABASE_URL`: This will be automatically set if you link the database in render.yaml, or manually add the Internal Database URL from Step 1
- `PYTHON_VERSION`: `3.11.0`

### Optional Variables (if you use these features)

- `GOOGLE_CLIENT_ID`: Your Google OAuth client ID
- `GOOGLE_CLIENT_SECRET`: Your Google OAuth client secret
- `GOOGLE_REDIRECT_BASE`: Your Google OAuth redirect URL
- `IPROG_API_KEY`: Your IPROG SMS API key
- `IPROG_SENDER_ID`: Your IPROG SMS sender ID
- `PRINTER_WEBHOOK_URL`: If using webhook-based printing
- `MEDIA_ROOT`: Path for media files (defaults to `/opt/render/project/src/media`)

### SMS Service Variables (if using SMS features)

- `IPROG_API_KEY`: Your IPROG API key
- `IPROG_SENDER_ID`: Your SMS sender ID

## Step 5: Migrate Database

After deployment, run database migrations:

1. Go to your web service in Render Dashboard
2. Click on "Shell" tab
3. Run:
   ```bash
   python manage.py migrate
   ```

## Step 6: Create Superuser (if needed)

If you need to create admin accounts:

1. Use the Shell tab in Render Dashboard
2. Run:
   ```bash
   python manage.py create_users
   ```

## Step 7: Restore Data from DigitalOcean (if migrating)

If you're migrating from DigitalOcean:

1. Download your backup from DigitalOcean
2. Upload it to Render using the Shell:
   ```bash
   # Upload your backup file (use Render's file upload or SCP)
   python manage.py restore_backup /path/to/backup.zip
   ```

## Step 8: Fix Database Sequences (Important!)

After restoring data, fix the database sequences to prevent duplicate key errors:

```bash
python manage.py fix_sequences
```

Or fix just the action_logs table:

```bash
python manage.py fix_sequences --table action_logs
```

## Step 9: Verify Deployment

1. Visit your Render service URL (e.g., `https://stockwise-web.onrender.com`)
2. Test login functionality
3. Check that the worker is running (check logs)

## Troubleshooting

### Database Connection Issues

- Ensure `DATABASE_URL` is set correctly
- Check that the database is in the same region as your services
- Verify the database is not paused (free tier databases pause after inactivity)

### Static Files Not Loading

- Ensure `collectstatic` runs during build
- Check that `WHITENOISE` is properly configured
- Verify `STATIC_ROOT` is set correctly

### Worker Not Running

- Check worker logs in Render Dashboard
- Ensure `DATABASE_URL` is set in worker environment variables
- Verify the worker service is not paused

### CSRF Errors

- Ensure your Render domain is in `CSRF_TRUSTED_ORIGINS`
- Check that `USE_X_FORWARDED_HOST` is enabled
- Verify `SECURE_PROXY_SSL_HEADER` is configured

## Notes

- **Free Tier Limitations**: Render's free tier has limitations (services spin down after inactivity, database pauses, etc.)
- **Custom Domain**: You can add a custom domain in Render Dashboard → Settings → Custom Domains
- **Environment Variables**: Keep sensitive data in environment variables, never commit to Git
- **Backups**: Regularly backup your database using the `backup_system` management command

## Support

For Render-specific issues, check:
- Render Documentation: https://render.com/docs
- Render Community: https://community.render.com

For StockWise-specific issues, check your application logs in Render Dashboard.

