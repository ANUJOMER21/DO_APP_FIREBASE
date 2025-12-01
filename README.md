# AOC Device Control Dashboard

A Python Flask-based dashboard for managing and controlling Android devices via Firebase Realtime Database. This dashboard allows you to:

- Monitor all registered Android devices
- Send commands to devices (lock, unlock, set wallpaper)
- Upload and host APK files
- Generate QR codes for easy app installation
- Manage multiple devices with bulk operations

## Features

- 🎯 **Device Management**: View all registered devices and their status (online/offline)
- 🔐 **Remote Control**: Lock/unlock devices remotely via Firebase
- 🖼️ **Wallpaper Control**: Set wallpapers on devices with image URLs
- 📱 **APK Hosting**: Upload and host APK files for distribution
- 📲 **QR Code Generation**: Generate QR codes for easy app installation
- 📊 **Real-time Stats**: View dashboard statistics (total devices, online/offline counts)
- ⚡ **Bulk Operations**: Send commands to multiple devices simultaneously

## Prerequisites

- Python 3.8 or higher
- Firebase project with Realtime Database enabled
- Firebase service account credentials (JSON file)

## Installation

1. **Clone or navigate to the project directory:**
   ```bash
   cd aoc_dashboard_backend
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up Firebase:**
   
   a. Go to [Firebase Console](https://console.firebase.google.com/)
   
   b. Select your project (or create a new one)
   
   c. Go to Project Settings → Service Accounts
   
   d. Click "Generate New Private Key" and download the JSON file
   
   e. Save the JSON file as `firebase-service-account.json` in the project root
   
   f. Note your Realtime Database URL (format: `https://YOUR-PROJECT-ID-default-rtdb.firebaseio.com/`)

5. **Configure environment variables:**
   
   Create a `.env` file in the project root (copy from `.env.example`):
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and update:
   - `FIREBASE_CREDENTIALS_PATH`: Path to your Firebase service account JSON file
   - `FIREBASE_DATABASE_URL`: Your Firebase Realtime Database URL
   - `DASHBOARD_BASE_URL`: Your dashboard URL (for QR code generation)

6. **Create required directories:**
   ```bash
   mkdir -p uploads/apk
   ```

## Usage

1. **Start the Flask server:**
   ```bash
   python app.py
   ```
   
   Or with environment variables:
   ```bash
   export FLASK_PORT=5000
   export FLASK_HOST=0.0.0.0
   python app.py
   ```

2. **Access the dashboard (local):**
   
   Open your browser and navigate to:
   ```
   http://localhost:5000
   ```

3. **Upload an APK:**
   - Click on "APK Management" section
   - Select an APK file
   - Click "Upload APK"

4. **Generate QR Code:**
   - Click the "Generate" button in the QR Code stat card
   - Scan the QR code with your Android device to download the app

5. **Control Devices:**
   - View all registered devices in the table
   - Click action buttons (Lock/Unlock/Wallpaper) for individual devices
   - Select multiple devices and use bulk actions for group operations

## Firebase Database Structure

The dashboard expects the following Firebase Realtime Database structure:

```
AOC/
  devices/
    {ANDROID_ID}/
      status: "online" | "offline"
      command: "lock" | "unlock" | "wallpaper:url"
      lastUpdated: timestamp
```

Devices automatically register themselves when the Android app connects to Firebase.

## API Endpoints

### Devices
- `GET /api/devices` - Get all registered devices
- `GET /api/devices/<device_id>/status` - Get device status
- `POST /api/devices/<device_id>/command` - Send command to device
- `POST /api/devices/bulk-command` - Send command to multiple devices

### APK Management
- `POST /api/apk/upload` - Upload APK file
- `GET /api/apk/download/<filename>` - Download APK file
- `GET /api/apk/qrcode` - Generate QR code for APK download

### Statistics
- `GET /api/stats` - Get dashboard statistics

## Configuration

### Environment Variables

- `FLASK_APP`: Flask application file (default: `app.py`)
- `FLASK_ENV`: Environment (development/production)
- `FLASK_HOST`: Host to bind to (default: `0.0.0.0`)
- `PORT`: Port provided by hosting platform (e.g. Railway). If set, the app will listen on this.
- `FLASK_PORT`: Port to run on locally (default: `5001` in this repo)
- `FIREBASE_CREDENTIALS_PATH`: Path to Firebase service account JSON
- `FIREBASE_DATABASE_URL`: Firebase Realtime Database URL
- `DASHBOARD_BASE_URL`: Base URL for dashboard (for QR codes)
- `APK_STORAGE_PATH`: Path to store uploaded APK files

## Deploying to Railway

1. **Push this project to GitHub** (see `.gitignore` for excluded secrets like `firebase-service-account.json` and `.env`).
2. **Create a new project on Railway** and select "Deploy from GitHub", choosing this repo.
3. Railway will auto-detect Python; ensure the service **start command** is:
   ```bash
   python app.py
   ```
4. In Railway → Variables, set at least:
   - `FIREBASE_CREDENTIALS_PATH=firebase-service-account.json`
   - `FIREBASE_DATABASE_URL=https://YOUR-PROJECT-ID-default-rtdb.firebaseio.com/`
   - `SECRET_KEY=some-long-random-string`
   - `DASHBOARD_BASE_URL=https://your-railway-domain.up.railway.app`
5. In Railway → Files (or through your workflow), upload `firebase-service-account.json` to the project root so the backend can read it.
6. After deploy, open the Railway-generated URL (or custom domain) to access the dashboard and use the Device Owner QR feature.

## Commands Supported

- `lock`: Lock the device immediately
- `unlock`: Unlock the device (clears password)
- `wallpaper:<url>`: Download and set wallpaper from URL

## Troubleshooting

### Firebase Connection Issues
- Verify your Firebase service account JSON file is in the correct location
- Check that the Firebase Realtime Database URL is correct
- Ensure Firebase Realtime Database is enabled in your Firebase project

### QR Code Not Generating
- Make sure at least one APK file has been uploaded
- Check that `DASHBOARD_BASE_URL` is correctly configured

### Devices Not Appearing
- Verify that devices are connecting to Firebase with the correct structure
- Check Firebase database rules allow read/write access
- Ensure the Android app is properly configured with Firebase

## Security Considerations

- **Production Deployment**: Change the `SECRET_KEY` in production
- **Firebase Rules**: Set up proper Firebase Realtime Database security rules
- **HTTPS**: Use HTTPS in production for secure communication
- **Authentication**: Consider adding authentication to the dashboard
- **File Upload**: Implement file size limits and validation

## License

This project is part of the AOC Device Control system.

## Support

For issues or questions, please check:
- Firebase Console for database connectivity
- Android app logs for device-side issues
- Flask server logs for backend issues

