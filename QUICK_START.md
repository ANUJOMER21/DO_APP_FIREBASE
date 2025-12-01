# Quick Start Guide

Get your AOC Dashboard running in 5 minutes!

## Prerequisites Checklist

- [ ] Python 3.8+ installed
- [ ] Firebase project created (`aoc-device-control`)
- [ ] Firebase Realtime Database enabled
- [ ] Firebase service account key downloaded

## Installation Steps

### 1. Install Dependencies

```bash
cd aoc_dashboard_backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Firebase

**Download Service Account Key:**
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select project: `aoc-device-control`
3. Settings ⚙️ → Project Settings → Service Accounts
4. Click "Generate New Private Key"
5. Save as `firebase-service-account.json` in project root

**Get Database URL:**
- Firebase Console → Realtime Database
- Copy URL: `https://aoc-device-control-default-rtdb.firebaseio.com/`

### 3. Create .env File

Create `.env` in project root:

```env
FLASK_APP=app.py
FLASK_ENV=development
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FIREBASE_CREDENTIALS_PATH=firebase-service-account.json
FIREBASE_DATABASE_URL=https://aoc-device-control-default-rtdb.firebaseio.com/
DASHBOARD_BASE_URL=http://localhost:5000
APK_STORAGE_PATH=uploads/apk
```

### 4. Start Dashboard

```bash
python app.py
```

Or use the startup script:
```bash
./run.sh
```

### 5. Access Dashboard

Open browser: `http://localhost:5000`

## First Steps

### Upload APK

1. Build Android app APK:
   ```bash
   cd ../AOC_DOAPP
   ./gradlew assembleDebug
   ```

2. Copy APK to dashboard (optional helper script):
   ```bash
   cd ../aoc_dashboard_backend
   ./copy_apk.sh
   ```

3. Or upload via dashboard UI:
   - Go to "APK Management" section
   - Choose file → Select APK
   - Click "Upload APK"

### Generate QR Code

1. Click "Generate" button in QR Code card
2. Scan QR code with Android device
3. Download and install APK

### Control Devices

Once Android app is installed on devices:
- Devices appear automatically in dashboard
- Send commands: Lock, Unlock, Set Wallpaper
- Use bulk actions for multiple devices

## Common Commands

### Lock Device
```json
POST /api/devices/{device_id}/command
{
  "command": "lock"
}
```

### Unlock Device
```json
POST /api/devices/{device_id}/command
{
  "command": "unlock"
}
```

### Set Wallpaper
```json
POST /api/devices/{device_id}/command
{
  "command": "wallpaper:https://example.com/image.jpg"
}
```

## Troubleshooting

**Firebase not connecting?**
- Check `firebase-service-account.json` exists
- Verify `FIREBASE_DATABASE_URL` in `.env`
- Ensure Realtime Database is enabled

**Devices not showing?**
- Verify Android app is running
- Check Firebase database rules
- Confirm devices are writing to `AOC/devices/{ANDROID_ID}`

**QR code not working?**
- Update `DASHBOARD_BASE_URL` to your server's IP/domain
- Ensure at least one APK is uploaded
- Check server is accessible from mobile network

## Production Deployment

1. Change `SECRET_KEY` in `.env`
2. Set `DASHBOARD_BASE_URL` to your domain
3. Use HTTPS (required for QR codes on mobile)
4. Configure Firebase database security rules
5. Set `FLASK_ENV=production`

## Next Steps

- Read `README.md` for detailed documentation
- See `SETUP.md` for detailed setup instructions
- Check `PROJECT_SUMMARY.md` for architecture overview

## Support

If you encounter issues:
1. Check Firebase Console for database activity
2. Check Flask server logs
3. Verify environment variables are set correctly
4. Ensure all dependencies are installed

