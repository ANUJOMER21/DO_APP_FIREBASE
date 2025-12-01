# Quick Setup Guide

Follow these steps to get your AOC Dashboard up and running quickly.

## Step 1: Install Python Dependencies

```bash
cd aoc_dashboard_backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Step 2: Configure Firebase

1. **Get Firebase Service Account Key:**
   - Go to [Firebase Console](https://console.firebase.google.com/)
   - Select your project: `aoc-device-control`
   - Click on the gear icon ⚙️ → Project Settings
   - Go to "Service Accounts" tab
   - Click "Generate New Private Key"
   - Save the downloaded JSON file as `firebase-service-account.json` in this directory

2. **Get Firebase Database URL:**
   - In Firebase Console, go to Realtime Database
   - Copy the database URL (usually: `https://aoc-device-control-default-rtdb.firebaseio.com/`)

## Step 3: Create Environment File

Create a `.env` file in the project root with the following content:

```env
# Flask Configuration
FLASK_APP=app.py
FLASK_ENV=development
FLASK_HOST=0.0.0.0
FLASK_PORT=5000

# Firebase Configuration
FIREBASE_CREDENTIALS_PATH=firebase-service-account.json
FIREBASE_DATABASE_URL=https://aoc-device-control-default-rtdb.firebaseio.com/

# Dashboard Configuration  
DASHBOARD_BASE_URL=http://localhost:5000
APK_STORAGE_PATH=uploads/apk
```

**Important:** Replace `DASHBOARD_BASE_URL` with your actual server URL if deploying to a server (e.g., `http://your-server-ip:5000`)

## Step 4: Create Required Directories

```bash
mkdir -p uploads/apk
```

## Step 5: Run the Dashboard

### Option 1: Using the startup script
```bash
./run.sh
```

### Option 2: Manual start
```bash
source venv/bin/activate  # If not already activated
python app.py
```

## Step 6: Access the Dashboard

Open your browser and go to:
```
http://localhost:5000
```

## Step 7: Upload APK and Generate QR Code

1. In the dashboard, scroll to "APK Management"
2. Click "Choose File" and select your APK file
3. Click "Upload APK"
4. Click the "Generate" button in the QR Code card to create a QR code
5. Scan the QR code with an Android device to download and install the app

## Troubleshooting

### Firebase Connection Errors

If you see Firebase connection errors:

1. Verify `firebase-service-account.json` exists in the project root
2. Check that `FIREBASE_DATABASE_URL` in `.env` matches your Firebase database URL
3. Ensure Firebase Realtime Database is enabled in Firebase Console
4. Check Firebase database rules allow read/write access

### Port Already in Use

If port 5000 is already in use:

```bash
export FLASK_PORT=5001
python app.py
```

Then access the dashboard at `http://localhost:5001`

### Devices Not Showing Up

1. Check that your Android app is connected to the same Firebase project
2. Verify devices are writing to `AOC/devices/{ANDROID_ID}` path
3. Check Firebase database rules allow reading from the devices path

## Next Steps

- Upload your APK file through the dashboard
- Generate QR codes for easy installation
- Start controlling devices via the dashboard
- Monitor device status in real-time

For more details, see the main [README.md](README.md) file.

