# AOC Device Control Dashboard Backend

A Python Flask-based backend for managing and controlling Android devices via Firebase Realtime Database. This backend provides APIs for device management, APK hosting, and **Android Device Owner provisioning** with QR code generation.

## 🚀 Features

- 🎯 **Device Management**: View all registered devices and their status (online/offline)
- 🔐 **Remote Control**: Lock/unlock devices remotely via Firebase
- 🖼️ **Wallpaper Control**: Set wallpapers on devices with image URLs
- 📱 **APK Hosting**: Upload and host APK files for distribution
- 📲 **QR Code Generation**: Generate QR codes for easy app installation
- 🔧 **Device Owner Provisioning**: Generate provisioning JSON and QR codes for Android Device Owner setup
- 📊 **Real-time Stats**: View dashboard statistics (total devices, online/offline counts)
- ⚡ **Bulk Operations**: Send commands to multiple devices simultaneously

## 📋 Prerequisites

- Python 3.8 or higher
- Firebase project with Realtime Database enabled
- Firebase service account credentials (JSON)

## 🛠️ Installation

### Local Development

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd aoc_dashboard_backend
   ```

2. **Create a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up Firebase credentials:**
   
   **Option A: Using Environment Variable (Recommended for Production)**
   
   Get your Firebase service account JSON:
   - Go to [Firebase Console](https://console.firebase.google.com/)
   - Select your project → Project Settings → Service Accounts
   - Click "Generate New Private Key" and download the JSON file
   - Copy the entire JSON content and set it as an environment variable:
   
   ```bash
   export FIREBASE_CREDENTIALS_JSON='{"type":"service_account","project_id":"...",...}'
   ```
   
   **Option B: Using JSON File (Local Development)**
   
   Save the JSON file as `firebase-service-account.json` in the project root.

5. **Configure environment variables:**
   
   Create a `.env` file (optional for local development):
   ```bash
   SECRET_KEY=your-secret-key-change-in-production
   FIREBASE_DATABASE_URL=https://YOUR-PROJECT-ID-default-rtdb.firebaseio.com/
   DASHBOARD_BASE_URL=http://localhost:5001
   APK_STORAGE_PATH=uploads/apk
   FLASK_ENV=development
   ```

6. **Create required directories:**
   ```bash
   mkdir -p uploads/apk
   ```

7. **Run the application:**
   ```bash
   python app.py
   ```
   
   The server will start on `http://localhost:5001`

## 🌐 Deployment to Render

### Step 1: Prepare Your Repository

1. **Push your code to GitHub** (ensure `.gitignore` excludes sensitive files)
2. Make sure `Procfile` exists with: `web: python app.py`

### Step 2: Create Render Service

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Render will auto-detect Python

### Step 3: Configure Environment Variables

In Render → Environment Variables, set:

| Variable | Value | Description |
|----------|-------|-------------|
| `SECRET_KEY` | `your-long-random-string` | Flask secret key |
| `FIREBASE_CREDENTIALS_JSON` | `{"type":"service_account",...}` | **Full JSON content** from Firebase service account |
| `FIREBASE_DATABASE_URL` | `https://YOUR-PROJECT-ID-default-rtdb.firebaseio.com/` | Firebase Realtime Database URL |
| `DASHBOARD_BASE_URL` | `https://your-service.onrender.com` | Your Render service URL |
| `APK_STORAGE_PATH` | `uploads/apk` | Path to store APK files |
| `ENVIRONMENT` | `production` | Enables HTTPS enforcement |

### Step 4: Get Firebase Credentials JSON

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project
3. Go to **Project Settings** → **Service Accounts**
4. Click **"Generate New Private Key"**
5. Download the JSON file
6. **Copy the entire JSON content** (all of it, including `{` and `}`)
7. Paste it as the value for `FIREBASE_CREDENTIALS_JSON` in Render

**Important:** The JSON must be on a single line or properly escaped. You can:
- Remove all newlines and spaces (minify it)
- Or use a JSON minifier tool
- Or paste it as-is if Render supports multi-line values

### Step 5: Deploy

1. Click "Create Web Service" in Render
2. Render will build and deploy automatically
3. Once deployed, your service URL will be available

### Step 6: Verify Deployment

1. Visit your Render service URL
2. Upload an APK via the dashboard or API
3. Test the Device Owner provisioning endpoint:
   ```
   GET https://your-service.onrender.com/api/apk/device-owner-provision
   ```

## 📡 API Endpoints

### Device Management

- `GET /api/devices` - Get all registered devices
- `GET /api/devices/<device_id>/status` - Get device status
- `POST /api/devices/<device_id>/command` - Send command to device
  ```json
  {
    "command": "lock" | "unlock" | "wallpaper:https://example.com/image.jpg"
  }
  ```
- `POST /api/devices/bulk-command` - Send command to multiple devices
  ```json
  {
    "device_ids": ["device1", "device2"],
    "command": "lock"
  }
  ```

### APK Management

- `POST /api/apk/upload` - Upload APK file
  - Form data: `apk` (file)
  - Returns: `filename`, `download_url`

- `GET /api/apk/download/<filename>` - Download APK file
  - Serves APK with correct MIME type for Android provisioning
  - Uses HTTPS in production
  - Sets proper headers (`Content-Type: application/vnd.android.package-archive`)

- `GET /api/apk/qrcode` - Generate QR code for APK download URL

### Device Owner Provisioning

- `GET /api/apk/device-owner-provision` - Get Device Owner provisioning JSON
  ```json
  {
    "success": true,
    "provisioning": {
      "android.app.extra.PROVISIONING_DEVICE_ADMIN_COMPONENT_NAME": "com.aoc.aoc_doapp/.MyDeviceAdminReceiver",
      "android.app.extra.PROVISIONING_DEVICE_ADMIN_PACKAGE_DOWNLOAD_LOCATION": "https://...",
      "android.app.extra.PROVISIONING_DEVICE_ADMIN_SIGNATURE_CHECKSUM": "base64-encoded-sha256",
      "android.app.extra.PROVISIONING_LEAVE_ALL_SYSTEM_APPS_ENABLED": true
    },
    "apk_filename": "aoc_doapp_20251201_163727.apk",
    "download_url": "https://..."
  }
  ```

- `GET /api/apk/device-owner-qr` - Generate QR code for Device Owner provisioning
  - Returns QR code image (base64) + provisioning JSON
  - Scan this QR code during Android setup on a factory-reset device

- `GET /api/apk/verify-checksum` - Verify checksum for latest APK
  - Useful for debugging provisioning issues
  - Returns checksum in both base64 and hex format

### Statistics

- `GET /api/stats` - Get dashboard statistics
  ```json
  {
    "success": true,
    "stats": {
      "total_devices": 10,
      "online_devices": 8,
      "offline_devices": 2
    }
  }
  ```

## 🔧 Android Device Owner Provisioning

This backend is specifically configured for **Android Device Owner** provisioning, which allows you to set up devices as managed devices during initial setup.

### Requirements

1. **Factory Reset Device**: Device Owner provisioning only works on factory-reset devices
2. **HTTPS**: All APK download URLs must use HTTPS (automatically enforced in production)
3. **Correct Headers**: APK downloads include proper MIME type and headers
4. **Valid Checksum**: SHA-256 checksum of the APK (automatically calculated)

### Component Name

The default component name is: `com.aoc.aoc_doapp/.MyDeviceAdminReceiver`

**Important:** Ensure your APK's manifest matches this exactly:
- Package name: `com.aoc.aoc_doapp`
- Device Admin Receiver: `MyDeviceAdminReceiver`
- Must be exported and enabled

### Usage

1. **Upload your APK:**
   ```bash
   curl -X POST -F "apk=@your-app.apk" https://your-service.onrender.com/api/apk/upload
   ```

2. **Get provisioning JSON:**
   ```bash
   curl https://your-service.onrender.com/api/apk/device-owner-provision
   ```

3. **Generate QR code:**
   - Visit: `https://your-service.onrender.com/api/apk/device-owner-qr`
   - Or use the dashboard UI

4. **Provision device:**
   - Factory reset your Android device
   - During setup, scan the QR code when prompted
   - Device will be enrolled as Device Owner

## 🔒 Security Considerations

- **Production Deployment**: Always change `SECRET_KEY` in production
- **Firebase Rules**: Set up proper Firebase Realtime Database security rules
- **HTTPS**: Automatically enforced in production for Device Owner provisioning
- **Credentials**: Use environment variables (`FIREBASE_CREDENTIALS_JSON`) instead of files in production
- **File Upload**: APK files are stored locally; consider cloud storage for production scale

## 🗂️ Firebase Database Structure

The backend expects the following Firebase Realtime Database structure:

```
AOC/
  devices/
    {ANDROID_ID}/
      status: "online" | "offline"
      command: "lock" | "unlock" | "wallpaper:url"
      lastUpdated: timestamp
```

Devices automatically register themselves when the Android app connects to Firebase.

## 🐛 Troubleshooting

### Firebase Connection Issues

- **Check credentials**: Verify `FIREBASE_CREDENTIALS_JSON` is set correctly (full JSON, no newlines if minified)
- **Database URL**: Ensure `FIREBASE_DATABASE_URL` matches your Firebase project
- **Database rules**: Check Firebase Realtime Database rules allow read/write access

### Device Owner Provisioning Fails

1. **Check HTTPS**: Ensure download URL uses `https://` (automatic in production)
2. **Verify checksum**: Use `/api/apk/verify-checksum` to verify the checksum matches
3. **Component name**: Ensure `com.aoc.aoc_doapp/.MyDeviceAdminReceiver` matches your APK manifest
4. **Factory reset**: Device Owner only works on factory-reset devices
5. **Network**: Device must have internet access during provisioning
6. **APK headers**: Check that download endpoint returns `Content-Type: application/vnd.android.package-archive`

### QR Code Not Generating

- Ensure at least one APK file has been uploaded
- Check that `DASHBOARD_BASE_URL` is correctly configured
- Verify the service is running and accessible

### Devices Not Appearing

- Verify devices are connecting to Firebase with the correct structure
- Check Firebase database rules allow read/write access
- Ensure the Android app is properly configured with Firebase
- Check Firebase service logs for connection errors

## 📝 Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | Yes | - | Flask secret key |
| `FIREBASE_CREDENTIALS_JSON` | Yes* | - | Firebase service account JSON (full content) |
| `FIREBASE_CREDENTIALS_PATH` | Yes* | `firebase-service-account.json` | Path to Firebase credentials file (fallback) |
| `FIREBASE_DATABASE_URL` | Yes | - | Firebase Realtime Database URL |
| `DASHBOARD_BASE_URL` | Yes | `http://localhost:5001` | Base URL for the dashboard |
| `APK_STORAGE_PATH` | No | `uploads/apk` | Path to store uploaded APK files |
| `ENVIRONMENT` | No | - | Set to `production` to enable HTTPS enforcement |
| `FLASK_ENV` | No | `development` | Flask environment |
| `PORT` | Auto | `5001` | Port (auto-set by Render) |

*Either `FIREBASE_CREDENTIALS_JSON` or `FIREBASE_CREDENTIALS_PATH` must be set.

## 📦 Project Structure

```
aoc_dashboard_backend/
├── app.py                 # Main Flask application
├── firebase_service.py    # Firebase service layer
├── requirements.txt       # Python dependencies
├── Procfile              # Render deployment config
├── README.md             # This file
├── templates/
│   └── dashboard.html    # Dashboard UI
├── static/
│   ├── css/
│   │   └── dashboard.css
│   └── js/
│       └── dashboard.js
└── uploads/
    └── apk/              # APK storage directory
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is part of the AOC Device Control system.

## 🆘 Support

For issues or questions:
- Check Firebase Console for database connectivity
- Review Android app logs for device-side issues
- Check Flask server logs for backend issues
- Verify environment variables are set correctly
- Use `/api/apk/verify-checksum` endpoint for debugging provisioning issues

---

**Note:** This backend is specifically optimized for Android Device Owner provisioning with proper HTTPS enforcement, MIME types, and checksum calculation required by Android's provisioning system.
