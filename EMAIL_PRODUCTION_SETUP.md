# Email OTP Production Setup Guide

## Overview
This guide explains how to configure email OTP (One-Time Password) functionality for production deployment, ensuring proper SSL/TLS certificate verification and avoiding antivirus/firewall blocking.

## Current Configuration

The system uses **Gmail SMTP** for sending OTP verification codes. The configuration is production-ready with proper SSL/TLS certificate verification.

### Key Settings (in `settings.py`)

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 465
EMAIL_USE_SSL = True
EMAIL_USE_TLS = False
```

## Production Deployment Requirements

### 1. SSL/TLS Certificate Verification

✅ **Production-Ready**: The system now uses proper SSL certificate verification by default.

- **No certificate bypass**: SSL certificates are properly verified
- **Antivirus-friendly**: Proper SSL verification prevents antivirus/firewall blocking
- **Secure**: Uses industry-standard SSL/TLS encryption

### 2. Gmail Configuration

For production with Gmail, you need:

#### Option A: Gmail App Password (Recommended)

1. **Enable 2-Step Verification** on your Gmail account:
   - Go to: https://myaccount.google.com/security
   - Enable "2-Step Verification"

2. **Generate App Password**:
   - Go to: https://myaccount.google.com/apppasswords
   - Select "Mail" and "Other (Custom name)"
   - Enter "StockWise" as the app name
   - Copy the generated 16-character password

3. **Set Environment Variables**:
   ```bash
   EMAIL_HOST_USER=your-email@gmail.com
   EMAIL_HOST_PASSWORD=your-16-char-app-password
   DEFAULT_FROM_EMAIL=your-email@gmail.com
   ```

#### Option B: OAuth2 (More Secure, Complex Setup)

For enterprise deployments, consider using OAuth2 instead of App Passwords.

### 3. Alternative Email Providers

If you prefer not to use Gmail, you can use other SMTP providers:

#### SendGrid
```bash
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=your-sendgrid-api-key
```

#### AWS SES
```bash
EMAIL_HOST=email-smtp.us-east-1.amazonaws.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=your-aws-access-key
EMAIL_HOST_PASSWORD=your-aws-secret-key
```

#### Microsoft 365 / Outlook
```bash
EMAIL_HOST=smtp.office365.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=your-email@outlook.com
EMAIL_HOST_PASSWORD=your-password
```

## Environment Variables

Set these in your production environment (`.env` file or environment variables):

```bash
# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=465
EMAIL_USE_SSL=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com

# SSL Verification (default: true - recommended for production)
EMAIL_SSL_VERIFY=true
```

## Testing Email in Production

### Test OTP Email Sending

1. **Login to the system**
2. **Enter your credentials**
3. **Check your email** for the OTP code
4. **Verify the email arrives** (check spam folder if needed)

### Troubleshooting

#### Email Not Sending

1. **Check credentials**:
   - Verify `EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD` are set correctly
   - For Gmail, ensure you're using an App Password (not your regular password)

2. **Check firewall/antivirus**:
   - Ensure port 465 (SSL) or 587 (TLS) is not blocked
   - Add exception for your application in antivirus software

3. **Check SSL verification**:
   - If you get SSL errors, verify certificates are properly installed
   - In development only, you can set `EMAIL_SSL_VERIFY=false` (NOT recommended for production)

4. **Check Gmail settings**:
   - Ensure "Less secure app access" is enabled (if not using App Passwords)
   - Or use App Passwords (recommended)

#### SSL Certificate Errors

If you encounter SSL certificate errors:

1. **Verify system certificates are up to date**:
   ```bash
   # On Linux
   sudo apt-get update && sudo apt-get install ca-certificates
   
   # On Windows
   # Certificates are usually managed automatically
   ```

2. **Check Python's certificate bundle**:
   - The system uses `certifi` package for certificate verification
   - Ensure `certifi` is installed: `pip install certifi`

#### Antivirus Blocking

If antivirus software blocks email sending:

1. **Add exception** for your application in antivirus settings
2. **Verify SSL certificates** are properly configured (antivirus may block unverified SSL)
3. **Check firewall rules** for outbound SMTP connections

## Security Best Practices

✅ **DO**:
- Use App Passwords for Gmail (not regular passwords)
- Keep email credentials in environment variables (never in code)
- Use proper SSL/TLS encryption (default)
- Regularly rotate email passwords/API keys

❌ **DON'T**:
- Use `EMAIL_SSL_VERIFY=false` in production
- Store email credentials in code or version control
- Use regular Gmail passwords (use App Passwords instead)
- Disable SSL/TLS encryption

## Production Checklist

Before deploying to production:

- [ ] Email credentials configured in environment variables
- [ ] Gmail App Password generated (if using Gmail)
- [ ] SSL certificate verification enabled (default)
- [ ] Firewall allows outbound SMTP (port 465 or 587)
- [ ] Antivirus exceptions configured (if needed)
- [ ] Test email sending works correctly
- [ ] OTP emails are received in inbox (not spam)

## Support

If you encounter issues:

1. Check the Django logs for email sending errors
2. Verify environment variables are set correctly
3. Test SMTP connection manually if needed
4. Contact your system administrator for firewall/antivirus configuration

