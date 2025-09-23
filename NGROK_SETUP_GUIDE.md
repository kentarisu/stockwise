# Complete ngrok Setup Guide for StockWise

## 🚀 Quick Setup Steps

### Step 1: Download ngrok
1. **Go to:** https://ngrok.com/download
2. **Click "Download for Windows"**
3. **Save the file** (ngrok-v3-stable-windows-amd64.zip)

### Step 2: Extract ngrok
1. **Extract the zip file**
2. **Move `ngrok.exe` to:** `C:\ngrok\ngrok.exe`
3. **Or extract directly to:** `C:\ngrok\`

### Step 3: Create ngrok Account
1. **Visit:** https://ngrok.com/
2. **Click "Sign up"** (free account)
3. **Verify your email**

### Step 4: Get Your Auth Token
1. **Login to ngrok dashboard:** https://dashboard.ngrok.com/
2. **Go to:** https://dashboard.ngrok.com/get-started/your-authtoken
3. **Copy your authtoken** (long string of characters)

### Step 5: Configure ngrok
Open Command Prompt as Administrator and run:
```cmd
C:\ngrok\ngrok.exe config add-authtoken YOUR_AUTH_TOKEN_HERE
```

### Step 6: Start StockWise Server
```cmd
cd C:\Users\Orly\stockwise
python manage.py runserver 8000
```

### Step 7: Start ngrok Tunnel
```cmd
C:\ngrok\ngrok.exe http 8000
```

## 📱 Access from iOS

1. **ngrok will show a URL like:** `https://abc123.ngrok.io`
2. **Copy this URL**
3. **Open Safari on your iOS device**
4. **Navigate to the ngrok URL**
5. **Login to StockWise**
6. **Test the QR scanner feature!**

## 🔧 Alternative: Use the Batch Files

I've created batch files to make this easier:

1. **Run setup_ngrok.bat** (enter your authtoken when prompted)
2. **Start Django server:** `python manage.py runserver 8000`
3. **Run start_ngrok.bat** (starts the tunnel)

## 📊 ngrok Dashboard

- **Local dashboard:** http://localhost:4040
- **View all requests and traffic**
- **Inspect and replay requests**

## ⚠️ Important Notes

- **Free ngrok limits:** 40 connections/minute, 1 tunnel
- **Session timeout:** 2 hours (then need to restart)
- **Random URL:** Changes each time you restart
- **Security:** Your system will be publicly accessible

## 🎯 Testing the QR Scanner

Once connected via ngrok:
1. **Go to Add Stock page**
2. **Click "Scan QR Code" button**
3. **Allow camera permissions**
4. **Test with any QR code**

## 🔄 Troubleshooting

### If ngrok won't start:
- Check if port 8000 is already in use
- Try a different port: `ngrok http 8080`
- Make sure your authtoken is correct

### If can't access from iOS:
- Make sure ngrok is running
- Check the ngrok URL is correct
- Try refreshing the page

### If QR scanner doesn't work:
- Allow camera permissions in Safari
- Make sure you're using Safari (not Chrome)
- Try refreshing the page

## 🚀 Quick Start Commands

```cmd
# 1. Start Django server
python manage.py runserver 8000

# 2. Start ngrok (in another terminal)
C:\ngrok\ngrok.exe http 8000

# 3. Access from iOS using the ngrok URL
```

## 📞 Support

If you need help:
1. Check ngrok dashboard at http://localhost:4040
2. Make sure both Django and ngrok are running
3. Verify your authtoken is configured correctly

