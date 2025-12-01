# AOC Device Control Dashboard - Project Summary

## Overview

This Python Flask-based dashboard provides a comprehensive web interface for managing and controlling Android devices via Firebase Realtime Database. It's designed to work with the AOC DO (Device Owner) Android app.

## Project Structure

```
aoc_dashboard_backend/
├── app.py                 # Main Flask application
├── firebase_service.py    # Firebase Admin SDK integration
├── requirements.txt       # Python dependencies
├── README.md             # Complete documentation
├── SETUP.md              # Quick setup guide
├── run.sh                # Startup script
├── .gitignore           # Git ignore rules
├── config.example.py     # Configuration example
├── env_setup.txt        # Environment variables template
├── templates/
│   └── dashboard.html   # Main dashboard UI
├── static/
│   ├── css/
│   │   └── dashboard.css # Dashboard styling
│   └── js/
│       └── dashboard.js  # Frontend JavaScript
└── uploads/
    └── apk/             # APK file storage
```

## Key Features

### 1. Device Management
- Real-time device listing with status (online/offline)
- Device search and filtering
- Statistics dashboard (total, online, offline counts)

### 2. Remote Device Control
- **Lock**: Remotely lock any device
- **Unlock**: Remotely unlock devices
- **Wallpaper**: Set custom wallpapers via image URL
- **Bulk Operations**: Control multiple devices simultaneously

### 3. APK Distribution
- Upload APK files through web interface
- Host APK files for download
- Generate QR codes for easy installation
- Direct download links

### 4. Firebase Integration
- Real-time device status monitoring
- Command broadcasting via Firebase Realtime Database
- Automatic device registration tracking

## Technology Stack

- **Backend**: Python 3.8+, Flask 3.0
- **Database**: Firebase Realtime Database
- **Frontend**: Bootstrap 5, Vanilla JavaScript
- **QR Code**: qrcode library with PIL
- **APIs**: RESTful API architecture

## Firebase Database Structure

The dashboard expects this structure in Firebase:

```
AOC/
  devices/
    {ANDROID_ID}/
      status: "online" | "offline"
      command: "lock" | "unlock" | "wallpaper:url"
      lastUpdated: timestamp (optional)
```

## API Endpoints

### Device Management
- `GET /api/devices` - List all devices
- `GET /api/devices/<id>/status` - Get device status
- `POST /api/devices/<id>/command` - Send command to device
- `POST /api/devices/bulk-command` - Send command to multiple devices

### APK Management
- `POST /api/apk/upload` - Upload APK file
- `GET /api/apk/download/<filename>` - Download APK
- `GET /api/apk/qrcode` - Generate QR code

### Statistics
- `GET /api/stats` - Get dashboard statistics

## Setup Requirements

1. **Python Environment**
   - Python 3.8 or higher
   - Virtual environment (recommended)

2. **Firebase Setup**
   - Firebase project with Realtime Database
   - Service account credentials (JSON file)

3. **Dependencies**
   - Flask and Flask-CORS
   - Firebase Admin SDK
   - QR code generation library

## Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure Firebase:
   - Download service account JSON
   - Set environment variables

3. Run the dashboard:
   ```bash
   python app.py
   ```

4. Access at `http://localhost:5000`

## Integration with Android App

The dashboard is designed to work with the AOC DO app located at:
`/Users/anujomer/AndroidStudioProjects/AOC_DOAPP`

**Key Integration Points:**

1. **Firebase Project**: Both apps use the same Firebase project (`aoc-device-control`)
2. **Database Path**: Devices register at `AOC/devices/{ANDROID_ID}`
3. **Commands**: Dashboard sends commands, Android app listens and executes
4. **Status**: Android app updates status, dashboard displays it

## Usage Workflow

1. **Initial Setup**
   - Deploy dashboard on a server
   - Build Android APK from the Android project
   - Upload APK to dashboard

2. **Device Installation**
   - Generate QR code in dashboard
   - Scan QR code with Android device
   - Install APK (requires device owner mode)

3. **Device Management**
   - Devices automatically register in dashboard
   - Monitor device status in real-time
   - Send commands individually or in bulk

## Security Considerations

- **Production**: Change SECRET_KEY, use HTTPS
- **Firebase Rules**: Configure proper database security rules
- **Authentication**: Consider adding login/auth to dashboard
- **File Validation**: APK upload validation and size limits

## Future Enhancements

Potential improvements:
- User authentication and authorization
- Device grouping and tagging
- Command history and logging
- Scheduled commands
- Device location tracking
- Advanced statistics and analytics
- Push notifications for device events

## Support

For setup help, see:
- `SETUP.md` for quick setup guide
- `README.md` for complete documentation

## License

Part of the AOC Device Control system.

