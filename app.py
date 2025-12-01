"""
AOC Device Control Dashboard
Python Flask backend for managing Android devices via Firebase
"""
import os
import posixpath
from flask import Flask, render_template, jsonify, request, send_file, url_for, Response
from flask_cors import CORS
import qrcode
from io import BytesIO
import base64
import hashlib
import json
from datetime import datetime
from firebase_service import FirebaseService
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Load configuration from environment variables
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
base_url = os.getenv('DASHBOARD_BASE_URL', 'http://localhost:5001')
# Force HTTPS in production (required for Android Device Owner provisioning)
if os.getenv('FLASK_ENV') == 'production' or os.getenv('ENVIRONMENT') == 'production':
    if base_url.startswith('http://'):
        base_url = base_url.replace('http://', 'https://', 1)
        logger.warning(f"Converted BASE_URL to HTTPS: {base_url}")
app.config['BASE_URL'] = base_url
app.config['APK_STORAGE'] = os.getenv('APK_STORAGE_PATH', 'uploads/apk')

# Initialize Firebase service
firebase_service = FirebaseService()

# Ensure APK storage directory exists
os.makedirs(app.config['APK_STORAGE'], exist_ok=True)

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/devices', methods=['GET'])
def get_devices():
    """Get list of all registered devices"""
    try:
        devices = firebase_service.get_all_devices()
        return jsonify({
            'success': True,
            'devices': devices,
            'count': len(devices)
        })
    except Exception as e:
        logger.error(f"Error fetching devices: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/devices/<device_id>/status', methods=['GET'])
def get_device_status(device_id):
    """Get status of a specific device"""
    try:
        status = firebase_service.get_device_status(device_id)
        return jsonify({
            'success': True,
            'device_id': device_id,
            'status': status
        })
    except Exception as e:
        logger.error(f"Error fetching device status: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/devices/<device_id>/command', methods=['POST'])
def send_command(device_id):
    """Send command to a device"""
    try:
        data = request.get_json()
        command = data.get('command')
        
        if not command:
            return jsonify({
                'success': False,
                'error': 'Command is required'
            }), 400
        
        # Validate command format
        valid_commands = ['lock', 'unlock']
        is_wallpaper = command.startswith('wallpaper:')
        
        if command.lower() not in valid_commands and not is_wallpaper:
            return jsonify({
                'success': False,
                'error': f'Invalid command. Valid commands: lock, unlock, wallpaper:url'
            }), 400
        
        firebase_service.send_command(device_id, command)
        
        return jsonify({
            'success': True,
            'device_id': device_id,
            'command': command,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error sending command: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/devices/bulk-command', methods=['POST'])
def send_bulk_command():
    """Send command to multiple devices"""
    try:
        data = request.get_json()
        device_ids = data.get('device_ids', [])
        command = data.get('command')
        
        if not device_ids or not command:
            return jsonify({
                'success': False,
                'error': 'device_ids and command are required'
            }), 400
        
        results = []
        for device_id in device_ids:
            try:
                firebase_service.send_command(device_id, command)
                results.append({
                    'device_id': device_id,
                    'success': True
                })
            except Exception as e:
                results.append({
                    'device_id': device_id,
                    'success': False,
                    'error': str(e)
                })
        
        return jsonify({
            'success': True,
            'command': command,
            'results': results,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error sending bulk command: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/apk/upload', methods=['POST'])
def upload_apk():
    """Upload APK file"""
    try:
        if 'apk' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No APK file provided'
            }), 400
        
        file = request.files['apk']
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400
        
        if not file.filename.endswith('.apk'):
            return jsonify({
                'success': False,
                'error': 'File must be an APK file'
            }), 400
        
        # Save APK file
        filename = f"aoc_doapp_{datetime.now().strftime('%Y%m%d_%H%M%S')}.apk"
        filepath = os.path.join(app.config['APK_STORAGE'], filename)
        file.save(filepath)
        
        # Generate download URL - ensure HTTPS in production
        download_url = url_for('download_apk', filename=filename, _external=True)
        
        # Force HTTPS if in production (required for Device Owner provisioning)
        if (os.getenv('FLASK_ENV') == 'production' or os.getenv('ENVIRONMENT') == 'production') and download_url.startswith('http://'):
            download_url = download_url.replace('http://', 'https://', 1)
            logger.info(f"Converted download URL to HTTPS: {download_url}")
        
        return jsonify({
            'success': True,
            'filename': filename,
            'download_url': download_url,
            'message': 'APK uploaded successfully'
        })
    except Exception as e:
        logger.error(f"Error uploading APK: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/apk/download/<filename>', methods=['GET'])
def download_apk(filename):
    """
    Download APK file with correct MIME type and headers for Android Device Owner provisioning.
    
    Returns raw APK file bytes with NO redirect, NO JSON, NO HTML.
    Required headers:
    - Content-Type: application/vnd.android.package-archive
    - Content-Disposition: attachment; filename="<real_name>.apk"
    """
    # Security: Validate filename to prevent directory traversal
    filename = posixpath.basename(filename)
    if not filename or not filename.endswith('.apk'):
        return Response('Invalid filename', status=400, mimetype='text/plain')
    
    filepath = os.path.join(app.config['APK_STORAGE'], filename)
    
    # Validate file exists and is within allowed directory
    if not os.path.exists(filepath):
        return Response('APK file not found', status=404, mimetype='text/plain')
    
    # Ensure filepath is within APK_STORAGE (prevent directory traversal)
    real_storage = os.path.realpath(app.config['APK_STORAGE'])
    real_filepath = os.path.realpath(filepath)
    if not real_filepath.startswith(real_storage):
        return Response('Invalid file path', status=403, mimetype='text/plain')
    
    try:
        # Stream file in binary mode
        def generate():
            with open(filepath, 'rb') as f:
                while True:
                    chunk = f.read(8192)  # 8KB chunks
                    if not chunk:
                        break
                    yield chunk
        
        file_size = os.path.getsize(filepath)
        
        # Create response with binary streaming
        response = Response(
            generate(),
            mimetype='application/vnd.android.package-archive',
            headers={
                'Content-Type': 'application/vnd.android.package-archive',
                'Content-Disposition': f'attachment; filename="{filename}"',
                'Content-Length': str(file_size),
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0'
            }
        )
        
        return response
    except Exception as e:
        logger.error(f"Error downloading APK: {str(e)}")
        return Response(f'Server error: {str(e)}', status=500, mimetype='text/plain')

@app.route('/api/apk/qrcode', methods=['GET'])
def generate_qr_code():
    """Generate QR code for APK download"""
    try:
        # Get latest APK file
        apk_dir = app.config['APK_STORAGE']
        apk_files = [f for f in os.listdir(apk_dir) if f.endswith('.apk')]
        
        if not apk_files:
            return jsonify({
                'success': False,
                'error': 'No APK files found. Please upload an APK first.'
            }), 404
        
        # Get the most recent APK
        latest_apk = max(apk_files, key=lambda f: os.path.getmtime(os.path.join(apk_dir, f)))
        download_url = url_for('download_apk', filename=latest_apk, _external=True)
        
        # Force HTTPS if in production (required for Device Owner provisioning)
        if (os.getenv('FLASK_ENV') == 'production' or os.getenv('ENVIRONMENT') == 'production') and download_url.startswith('http://'):
            download_url = download_url.replace('http://', 'https://', 1)
            logger.info(f"Converted download URL to HTTPS: {download_url}")
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(download_url)
        qr.make(fit=True)
        
        # Create QR code image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return jsonify({
            'success': True,
            'qr_code': f'data:image/png;base64,{img_str}',
            'download_url': download_url,
            'filename': latest_apk
        })
    except Exception as e:
        logger.error(f"Error generating QR code: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def _get_latest_apk_info():
    """Helper to get latest APK filepath, filename and download URL"""
    apk_dir = app.config['APK_STORAGE']
    apk_files = [f for f in os.listdir(apk_dir) if f.endswith('.apk')]

    if not apk_files:
        return None, None, None

    latest_apk = max(apk_files, key=lambda f: os.path.getmtime(os.path.join(apk_dir, f)))
    filepath = os.path.join(apk_dir, latest_apk)
    
    # Generate download URL - ensure HTTPS in production
    download_url = url_for('download_apk', filename=latest_apk, _external=True)
    
    # Force HTTPS if in production (required for Device Owner provisioning)
    if (os.getenv('FLASK_ENV') == 'production' or os.getenv('ENVIRONMENT') == 'production') and download_url.startswith('http://'):
        download_url = download_url.replace('http://', 'https://', 1)
        logger.info(f"Converted download URL to HTTPS: {download_url}")
    
    return filepath, latest_apk, download_url


def _build_device_owner_payload():
    """
    Build Android Device Owner provisioning payload based on the latest APK.

    Uses:
    - com.aoc.aoc_doapp/.MyDeviceAdminReceiver as the device admin component
    - Latest uploaded APK as the package download location
    - SHA-256 (base64) of the APK as the signature checksum
    """
    filepath, filename, download_url = _get_latest_apk_info()
    if not filepath:
        raise FileNotFoundError('No APK files found. Please upload an APK first.')

    # Calculate SHA-256 and encode as base64 (required by Android for checksum)
    # Note: This calculates SHA-256 of the entire APK file.
    # For Device Owner provisioning, Android typically requires the certificate's SHA-256,
    # but some setups use the file's SHA-256. This matches: sha256sum <apk> | awk '{print $1}' | xxd -r -p | base64
    with open(filepath, 'rb') as f:
        apk_content = f.read()
        digest = hashlib.sha256(apk_content).digest()
    checksum_b64 = base64.b64encode(digest).decode()
    
    # Log checksum for debugging
    logger.info(f"Generated checksum for {filename}: {checksum_b64}")
    logger.info(f"APK file size: {len(apk_content)} bytes")

    payload = {
        "android.app.extra.PROVISIONING_DEVICE_ADMIN_COMPONENT_NAME": "com.aoc.aoc_doapp/.MyDeviceAdminReceiver",
        "android.app.extra.PROVISIONING_DEVICE_ADMIN_PACKAGE_DOWNLOAD_LOCATION": download_url,
        "android.app.extra.PROVISIONING_DEVICE_ADMIN_SIGNATURE_CHECKSUM": checksum_b64,
        "android.app.extra.PROVISIONING_LEAVE_ALL_SYSTEM_APPS_ENABLED": True
    }

    return payload, filename, download_url


@app.route('/api/apk/device-owner-provision', methods=['GET'])
def get_device_owner_provision():
    """
    Get Device Owner provisioning JSON for the latest uploaded APK.

    Response:
    {
      "success": true,
      "provisioning": { ... full payload ... },
      "apk_filename": "aoc_doapp_YYYYMMDD_HHMMSS.apk",
      "download_url": "http://.../api/apk/download/..."
    }
    """
    try:
        payload, filename, download_url = _build_device_owner_payload()
        return jsonify({
            'success': True,
            'provisioning': payload,
            'apk_filename': filename,
            'download_url': download_url
        })
    except FileNotFoundError as e:
        logger.error(str(e))
        return jsonify({
            'success': False,
            'error': str(e)
        }), 404
    except Exception as e:
        logger.error(f"Error building device owner provisioning payload: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/apk/device-owner-qr', methods=['GET'])
def get_device_owner_qr():
    """
    Generate a QR code for Device Owner provisioning.

    The QR encodes the full JSON payload required by Android's setup wizard.

    Response:
    {
      "success": true,
      "qr_code": "data:image/png;base64,...",
      "provisioning": { ... full payload ... },
      "apk_filename": "aoc_doapp_YYYYMMDD_HHMMSS.apk",
      "download_url": "http://.../api/apk/download/..."
    }
    """
    try:
        payload, filename, download_url = _build_device_owner_payload()

        # Encode the JSON payload (compact form) into QR
        payload_str = json.dumps(payload, separators=(',', ':'))

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(payload_str)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()

        return jsonify({
            'success': True,
            'qr_code': f'data:image/png;base64,{img_str}',
            'provisioning': payload,
            'apk_filename': filename,
            'download_url': download_url
        })
    except FileNotFoundError as e:
        logger.error(str(e))
        return jsonify({
            'success': False,
            'error': str(e)
        }), 404
    except Exception as e:
        logger.error(f"Error generating device owner QR code: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/apk/verify-checksum', methods=['GET'])
def verify_checksum():
    """
    Verify and display the checksum for the latest APK.
    Useful for debugging provisioning issues.
    """
    try:
        filepath, filename, download_url = _get_latest_apk_info()
        if not filepath:
            return jsonify({
                'success': False,
                'error': 'No APK files found. Please upload an APK first.'
            }), 404
        
        # Calculate checksum
        with open(filepath, 'rb') as f:
            apk_content = f.read()
            digest = hashlib.sha256(apk_content).digest()
        checksum_b64 = base64.b64encode(digest).decode()
        checksum_hex = digest.hex()
        
        file_size = len(apk_content)
        
        return jsonify({
            'success': True,
            'filename': filename,
            'file_size': file_size,
            'checksum_base64': checksum_b64,
            'checksum_hex': checksum_hex,
            'download_url': download_url,
            'verification_command': f'sha256sum {filename} | awk \'{{print $1}}\' | xxd -r -p | base64'
        })
    except Exception as e:
        logger.error(f"Error verifying checksum: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get dashboard statistics"""
    try:
        devices = firebase_service.get_all_devices()
        online_count = sum(1 for d in devices.values() if d.get('status') == 'online')
        offline_count = len(devices) - online_count
        
        return jsonify({
            'success': True,
            'stats': {
                'total_devices': len(devices),
                'online_devices': online_count,
                'offline_devices': offline_count
            }
        })
    except Exception as e:
        logger.error(f"Error fetching stats: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    # Railway and many PaaS providers expose the HTTP port via the PORT env var.
    # Fall back to FLASK_PORT, then to 5001 for local development.
    port = int(os.getenv('PORT', os.getenv('FLASK_PORT', 5001)))
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    debug = os.getenv('FLASK_ENV', 'development') == 'development'
    
    logger.info(f"Starting AOC Dashboard on {host}:{port}")
    app.run(host=host, port=port, debug=debug)

