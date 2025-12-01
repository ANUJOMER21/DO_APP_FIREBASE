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
import subprocess
import tempfile
import glob
import zipfile

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
app.config['CHECKSUM_STORAGE'] = os.path.join(app.config['APK_STORAGE'], 'checksums.json')

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
    """
    Upload APK file with optional checksum.
    
    Accepts:
    - 'apk': APK file (required)
    - 'checksum': SHA-256 checksum in base64url format (optional)
    """
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
        
        # Get optional checksum from form data
        provided_checksum = request.form.get('checksum', '').strip()
        
        # Save APK file
        filename = f"aoc_doapp_{datetime.now().strftime('%Y%m%d_%H%M%S')}.apk"
        filepath = os.path.join(app.config['APK_STORAGE'], filename)
        file.save(filepath)
        
        # Store checksum if provided (normalize to base64url format)
        if provided_checksum:
            try:
                normalized_checksum = _normalize_checksum_to_base64url(provided_checksum)
                _set_checksum_for_apk(filename, normalized_checksum)
                logger.info(f"APK uploaded with provided checksum (normalized): {filename}")
                logger.info(f"Original checksum: {provided_checksum}")
                logger.info(f"Normalized checksum (base64url): {normalized_checksum}")
            except ValueError as e:
                logger.error(f"Invalid checksum format: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': f'Invalid checksum format: {str(e)}. Please provide checksum in base64url, base64, or hex format.'
                }), 400
        else:
            logger.info(f"APK uploaded without checksum (will be computed): {filename}")
        
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
            'checksum_provided': bool(provided_checksum),
            'checksum': provided_checksum if provided_checksum else None,
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


def _load_checksums():
    """Load checksums from storage file"""
    checksum_file = app.config['CHECKSUM_STORAGE']
    if os.path.exists(checksum_file):
        try:
            with open(checksum_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Error loading checksums: {str(e)}")
            return {}
    return {}


def _save_checksums(checksums):
    """Save checksums to storage file"""
    checksum_file = app.config['CHECKSUM_STORAGE']
    try:
        with open(checksum_file, 'w') as f:
            json.dump(checksums, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving checksums: {str(e)}")
        raise


def _get_checksum_for_apk(filename):
    """Get stored checksum for an APK file"""
    checksums = _load_checksums()
    return checksums.get(filename)


def _set_checksum_for_apk(filename, checksum):
    """Store checksum for an APK file"""
    checksums = _load_checksums()
    checksums[filename] = checksum
    _save_checksums(checksums)
    logger.info(f"Stored checksum for {filename}: {checksum}")


def _extract_certificate_using_apksigner(apk_path):
    """
    Extract certificate using apksigner tool (Android SDK).
    This is the most reliable method.
    """
    try:
        # Try to find apksigner in common locations
        apksigner_paths = [
            'apksigner',
            os.path.expanduser('~/Library/Android/sdk/build-tools/*/apksigner'),
            os.path.expanduser('~/Android/Sdk/build-tools/*/apksigner'),
            '/opt/android-sdk/build-tools/*/apksigner',
        ]
        
        apksigner = None
        for path in apksigner_paths:
            if '*' in path:
                matches = glob.glob(path)
                if matches:
                    apksigner = sorted(matches)[-1]  # Use latest version
                    break
            elif os.path.exists(path):
                apksigner = path
                break
        
        if not apksigner:
            # Try to find it in PATH
            result = subprocess.run(['which', 'apksigner'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                apksigner = result.stdout.strip()
        
        if not apksigner:
            raise FileNotFoundError("apksigner not found. Install Android SDK build-tools.")
        
        # Extract certificate using apksigner
        result = subprocess.run(
            [apksigner, 'verify', '--print-certs', apk_path],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Parse certificate from output
        # apksigner outputs certificates in PEM format
        cert_pem = result.stdout
        if '-----BEGIN CERTIFICATE-----' not in cert_pem:
            raise ValueError("Could not extract certificate from apksigner output")
        
        # Extract first certificate
        cert_start = cert_pem.find('-----BEGIN CERTIFICATE-----')
        cert_end = cert_pem.find('-----END CERTIFICATE-----', cert_start) + len('-----END CERTIFICATE-----')
        cert_pem = cert_pem[cert_start:cert_end]
        
        # Convert PEM to DER
        from cryptography import x509
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives import serialization
        cert = x509.load_pem_x509_certificate(cert_pem.encode(), default_backend())
        return cert.public_bytes(serialization.Encoding.DER)
        
    except subprocess.CalledProcessError as e:
        raise ValueError(f"apksigner failed: {e.stderr}")
    except Exception as e:
        raise ValueError(f"Error using apksigner: {str(e)}")


def _extract_certificate_using_jarsigner(apk_path):
    """
    Extract certificate using jarsigner tool (Java JDK).
    Fallback method if apksigner is not available.
    """
    try:
        # Extract certificate from APK META-INF
        with zipfile.ZipFile(apk_path, 'r') as apk:
            cert_files = [f for f in apk.namelist() 
                         if f.startswith('META-INF/') and (f.endswith('.RSA') or f.endswith('.DSA'))]
            
            if not cert_files:
                raise ValueError("No certificate found in APK")
            
            cert_file = cert_files[0]
            cert_data = apk.read(cert_file)
            
            # Try to extract certificate from PKCS#7 structure
            # Use openssl if available
            with tempfile.NamedTemporaryFile(suffix='.rsa', delete=False) as tmp_cert:
                tmp_cert.write(cert_data)
                tmp_cert_path = tmp_cert.name
            
            try:
                # Use openssl to extract certificate
                result = subprocess.run(
                    ['openssl', 'pkcs7', '-inform', 'DER', '-in', tmp_cert_path, 
                     '-print_certs', '-outform', 'PEM'],
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                cert_pem = result.stdout
                if '-----BEGIN CERTIFICATE-----' not in cert_pem:
                    raise ValueError("Could not extract certificate")
                
                # Extract first certificate
                cert_start = cert_pem.find('-----BEGIN CERTIFICATE-----')
                cert_end = cert_pem.find('-----END CERTIFICATE-----', cert_start) + len('-----END CERTIFICATE-----')
                cert_pem = cert_pem[cert_start:cert_end]
                
                from cryptography import x509
                from cryptography.hazmat.backends import default_backend
                from cryptography.hazmat.primitives import serialization
                cert = x509.load_pem_x509_certificate(cert_pem.encode(), default_backend())
                return cert.public_bytes(serialization.Encoding.DER)
                
            finally:
                os.unlink(tmp_cert_path)
                
    except FileNotFoundError:
        raise ValueError("jarsigner or openssl not found")
    except Exception as e:
        raise ValueError(f"Error using jarsigner: {str(e)}")


def _compute_certificate_checksum(apk_path):
    """
    Compute SHA-256 checksum of the APK's signing certificate.
    
    Returns:
        tuple: (base64_checksum, base64url_checksum, hex_checksum)
    """
    if not os.path.exists(apk_path):
        raise FileNotFoundError(f"APK file not found: {apk_path}")
    
    cert_der = None
    method_used = None
    
    # Try apksigner first (most reliable)
    try:
        cert_der = _extract_certificate_using_apksigner(apk_path)
        method_used = "apksigner"
    except Exception as e1:
        # Fallback to jarsigner + openssl
        try:
            cert_der = _extract_certificate_using_jarsigner(apk_path)
            method_used = "jarsigner+openssl"
        except Exception as e2:
            raise ValueError(
                f"Could not extract certificate. Tried:\n"
                f"  1. apksigner: {str(e1)}\n"
                f"  2. jarsigner+openssl: {str(e2)}\n\n"
                f"Please install Android SDK build-tools (for apksigner) or "
                f"Java JDK + OpenSSL (for jarsigner+openssl)."
            )
    
    # Compute SHA-256 of the certificate
    sha256_digest = hashlib.sha256(cert_der).digest()
    
    # Encode as base64 and base64url
    checksum_b64 = base64.b64encode(sha256_digest).decode('utf-8')
    checksum_b64url = _base64_to_base64url(checksum_b64)
    checksum_hex = sha256_digest.hex()
    
    logger.info(f"Certificate extracted using: {method_used}")
    
    return checksum_b64, checksum_b64url, checksum_hex


def _base64_to_base64url(b64_string):
    """
    Convert standard base64 encoding to base64url encoding.
    Base64url uses '-' instead of '+', '_' instead of '/', and removes padding '='.
    This is required by Android Device Owner provisioning.
    """
    # Replace characters
    b64url = b64_string.replace('+', '-').replace('/', '_')
    # Remove padding
    b64url = b64url.rstrip('=')
    return b64url


def _normalize_checksum_to_base64url(checksum_input):
    """
    Normalize checksum input to base64url format.
    Accepts:
    - Base64url format (already correct)
    - Standard base64 format (with +, /, =)
    - Hex format (64 character hex string)
    
    Returns base64url formatted checksum (no +, /, =, or other invalid chars).
    """
    import urllib.parse
    
    checksum = checksum_input.strip()
    
    if not checksum:
        raise ValueError("Checksum cannot be empty")
    
    # Remove any URL encoding artifacts (like %3D for =, etc.)
    # First try to decode if it looks URL encoded
    if '%' in checksum:
        try:
            checksum = urllib.parse.unquote(checksum)
        except Exception:
            pass  # If decoding fails, continue with original
    
    # Remove any whitespace or invalid characters
    checksum = checksum.strip().rstrip('=%')  # Remove trailing = or % that might be artifacts
    
    if not checksum:
        raise ValueError("Checksum is empty after cleaning")
    
    # Check if it's hex format (64 character hex string)
    if len(checksum) == 64 and all(c in '0123456789abcdefABCDEF' for c in checksum):
        # It's hex format - convert to base64url
        try:
            digest = bytes.fromhex(checksum)
            checksum_b64 = base64.b64encode(digest).decode()
            return _base64_to_base64url(checksum_b64)
        except ValueError:
            raise ValueError(f"Invalid hex checksum format: {checksum}")
    
    # Check if it's standard base64 (has +, /, or =)
    if '+' in checksum or '/' in checksum or '=' in checksum:
        # Convert from standard base64 to base64url
        # First validate it's valid base64
        try:
            # Try to decode to validate
            base64.b64decode(checksum + '==')  # Add padding for validation
        except Exception:
            raise ValueError(f"Invalid base64 format: {checksum}")
        return _base64_to_base64url(checksum)
    
    # Check if it looks like base64url (43-44 chars, alphanumeric + - and _)
    if len(checksum) >= 40 and len(checksum) <= 44:
        # Validate it only contains base64url characters
        valid_chars = set('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_')
        if all(c in valid_chars for c in checksum):
            # Remove any trailing padding characters
            return checksum.rstrip('=')
    
    # If we get here, try to validate and convert
    # Remove any invalid trailing characters
    checksum = checksum.rstrip('=%')
    
    # Final validation - should be 43 characters for SHA-256 in base64url
    if len(checksum) == 43:
        return checksum
    
    raise ValueError(f"Invalid checksum format or length: {checksum} (length: {len(checksum)})")


def _build_device_owner_payload():
    """
    Build Android Device Owner provisioning payload based on the latest APK.

    Uses:
    - com.aoc.aoc_doapp/.MyDeviceAdminReceiver as the device admin component
    - Latest uploaded APK as the package download location
    - SHA-256 (base64url) of the APK file as the signature checksum
    - Uses provided checksum if available, otherwise computes it
    """
    filepath, filename, download_url = _get_latest_apk_info()
    if not filepath:
        raise FileNotFoundError('No APK files found. Please upload an APK first.')

    # Check if checksum was provided during upload
    stored_checksum = _get_checksum_for_apk(filename)
    
    checksum_b64url = None
    
    if stored_checksum:
        # Use provided checksum (should already be normalized to base64url format)
        # But normalize again just in case to handle any edge cases
        try:
            logger.info(f"Raw stored checksum for {filename}: {repr(stored_checksum)}")
            checksum_b64url = _normalize_checksum_to_base64url(stored_checksum)
            logger.info(f"Normalized checksum (base64url) for {filename}: {checksum_b64url}")
            logger.info(f"Checksum length: {len(checksum_b64url)} (should be 43 for SHA-256)")
            
            # Final validation - ensure it's exactly 43 characters and valid base64url
            if len(checksum_b64url) != 43:
                raise ValueError(f"Checksum length is {len(checksum_b64url)}, expected 43 for SHA-256 base64url")
            
            # Check for invalid characters
            invalid_chars = set(checksum_b64url) - set('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_')
            if invalid_chars:
                raise ValueError(f"Checksum contains invalid characters: {invalid_chars}")
                
        except ValueError as e:
            logger.error(f"Stored checksum validation failed for {filename}: {str(e)}")
            logger.warning(f"Falling back to computing checksum from APK file")
            stored_checksum = None
            checksum_b64url = None
    
    if not checksum_b64url:
        # Calculate SHA-256 of the APK file itself (like: shasum -a 256 your_app.apk)
        # Then convert to base64url format (required by Android Device Owner provisioning)
        with open(filepath, 'rb') as f:
            apk_content = f.read()
            digest = hashlib.sha256(apk_content).digest()
        
        # Encode as base64, then convert to base64url
        checksum_b64 = base64.b64encode(digest).decode()
        checksum_b64url = _base64_to_base64url(checksum_b64)
        checksum_hex = digest.hex()
        
        # Log checksum for debugging
        logger.info(f"Computed APK file checksum (hex) for {filename}: {checksum_hex}")
        logger.info(f"Computed APK file checksum (base64) for {filename}: {checksum_b64}")
        logger.info(f"Computed APK file checksum (base64url) for {filename}: {checksum_b64url}")
        logger.info(f"Checksum length: {len(checksum_b64url)} (should be 43 for SHA-256)")
        logger.info(f"APK file size: {len(apk_content)} bytes")
        
        # Final validation
        if len(checksum_b64url) != 43:
            logger.error(f"WARNING: Computed checksum length is {len(checksum_b64url)}, expected 43!")

    # Final validation before using checksum in payload
    if len(checksum_b64url) != 43:
        raise ValueError(f"Invalid checksum length: {len(checksum_b64url)}, expected 43 for SHA-256 base64url")
    
    # Ensure no invalid characters
    invalid_chars = set(checksum_b64url) - set('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_')
    if invalid_chars:
        raise ValueError(f"Checksum contains invalid characters: {invalid_chars}")
    
    logger.info(f"Final checksum to use in payload: {checksum_b64url}")

    payload = {
        "android.app.extra.PROVISIONING_DEVICE_ADMIN_COMPONENT_NAME": "com.aoc.aoc_doapp/com.aoc.aoc_doapp.MyDeviceAdminReceiver",
        "android.app.extra.PROVISIONING_DEVICE_ADMIN_PACKAGE_DOWNLOAD_LOCATION": download_url,
        "android.app.extra.PROVISIONING_DEVICE_ADMIN_SIGNATURE_CHECKSUM": checksum_b64url,
        "android.app.extra.PROVISIONING_LEAVE_ALL_SYSTEM_APPS_ENABLED": True,
        "android.app.extra.PROVISIONING_SKIP_ENCRYPTION": False
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
    Verify and display the checksum for the latest APK file.
    Useful for debugging provisioning issues.
    Returns the SHA-256 of the APK file itself (like: shasum -a 256 your_app.apk).
    """
    try:
        filepath, filename, download_url = _get_latest_apk_info()
        if not filepath:
            return jsonify({
                'success': False,
                'error': 'No APK files found. Please upload an APK first.'
            }), 404
        
        # Calculate SHA-256 of the APK file itself
        with open(filepath, 'rb') as f:
            apk_content = f.read()
            digest = hashlib.sha256(apk_content).digest()
        
        checksum_b64 = base64.b64encode(digest).decode()
        checksum_b64url = _base64_to_base64url(checksum_b64)
        checksum_hex = digest.hex()
        
        file_size = len(apk_content)
        
        return jsonify({
            'success': True,
            'filename': filename,
            'file_size': file_size,
            'checksum_type': 'apk_file_sha256',
            'checksum_base64': checksum_b64,
            'checksum_base64url': checksum_b64url,
            'checksum_hex': checksum_hex,
            'download_url': download_url,
            'verification_command': f'shasum -a 256 {filename}',
            'note': 'This is the SHA-256 of the APK file itself, converted to base64url format for Device Owner provisioning',
            'stored_checksum': _get_checksum_for_apk(filename)
        })
    except Exception as e:
        logger.error(f"Error verifying checksum: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/apk/set-checksum', methods=['POST'])
def set_checksum():
    """
    Set or update the checksum for an APK file.
    
    Accepts JSON:
    {
        "filename": "aoc_doapp_20251201_174056.apk",
        "checksum": "base64url_checksum_here"
    }
    
    Or for latest APK:
    {
        "checksum": "base64url_checksum_here"
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400
        
        checksum = data.get('checksum', '').strip()
        if not checksum:
            return jsonify({
                'success': False,
                'error': 'Checksum is required'
            }), 400
        
        filename = data.get('filename')
        
        # If filename not provided, use latest APK
        if not filename:
            _, latest_filename, _ = _get_latest_apk_info()
            if not latest_filename:
                return jsonify({
                    'success': False,
                    'error': 'No APK files found and no filename provided'
                }), 404
            filename = latest_filename
        
        # Validate that the APK file exists
        filepath = os.path.join(app.config['APK_STORAGE'], filename)
        if not os.path.exists(filepath):
            return jsonify({
                'success': False,
                'error': f'APK file not found: {filename}'
            }), 404
        
        # Normalize checksum to base64url format
        try:
            normalized_checksum = _normalize_checksum_to_base64url(checksum)
            _set_checksum_for_apk(filename, normalized_checksum)
            
            return jsonify({
                'success': True,
                'filename': filename,
                'checksum_original': checksum,
                'checksum_normalized': normalized_checksum,
                'message': f'Checksum stored for {filename}'
            })
        except ValueError as e:
            return jsonify({
                'success': False,
                'error': f'Invalid checksum format: {str(e)}. Please provide checksum in base64url, base64, or hex format.'
            }), 400
    except Exception as e:
        logger.error(f"Error setting checksum: {str(e)}")
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

