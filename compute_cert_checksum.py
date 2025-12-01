#!/usr/bin/env python3
"""
Compute SHA-256 certificate checksum for Android APK (Device Owner provisioning).

This script extracts the signing certificate from an APK and computes its SHA-256
checksum in base64 format, which is required for Android Device Owner provisioning.

Usage:
    python compute_cert_checksum.py <path_to_apk>
    
Example:
    python compute_cert_checksum.py uploads/apk/aoc_doapp_20251201_210745.apk
"""
import sys
import os
import subprocess
import base64
import hashlib
import tempfile

def extract_certificate_using_apksigner(apk_path):
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
                import glob
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
        cert = x509.load_pem_x509_certificate(cert_pem.encode(), default_backend())
        return cert.public_bytes(default_backend())
        
    except subprocess.CalledProcessError as e:
        raise ValueError(f"apksigner failed: {e.stderr}")
    except Exception as e:
        raise ValueError(f"Error using apksigner: {str(e)}")


def extract_certificate_using_jarsigner(apk_path):
    """
    Extract certificate using jarsigner tool (Java JDK).
    Fallback method if apksigner is not available.
    """
    try:
        # Create temporary keystore
        with tempfile.NamedTemporaryFile(suffix='.jks', delete=False) as tmp_keystore:
            tmp_keystore_path = tmp_keystore.name
        
        try:
            # Use jarsigner to verify and extract certificate info
            result = subprocess.run(
                ['jarsigner', '-verify', '-verbose', '-certs', apk_path],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                raise ValueError("jarsigner verification failed")
            
            # Extract certificate using keytool (requires extracting from APK first)
            # This is more complex, so we'll use a different approach
            import zipfile
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
                    cert = x509.load_pem_x509_certificate(cert_pem.encode(), default_backend())
                    return cert.public_bytes(default_backend())
                    
                finally:
                    os.unlink(tmp_cert_path)
                    
        finally:
            if os.path.exists(tmp_keystore_path):
                os.unlink(tmp_keystore_path)
                
    except FileNotFoundError:
        raise ValueError("jarsigner or openssl not found")
    except Exception as e:
        raise ValueError(f"Error using jarsigner: {str(e)}")


def compute_certificate_checksum(apk_path):
    """
    Compute SHA-256 checksum of the APK's signing certificate.
    
    Returns:
        tuple: (base64_checksum, hex_checksum, certificate_info)
    """
    if not os.path.exists(apk_path):
        raise FileNotFoundError(f"APK file not found: {apk_path}")
    
    cert_der = None
    method_used = None
    
    # Try apksigner first (most reliable)
    try:
        cert_der = extract_certificate_using_apksigner(apk_path)
        method_used = "apksigner"
    except Exception as e1:
        # Fallback to jarsigner + openssl
        try:
            cert_der = extract_certificate_using_jarsigner(apk_path)
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
    
    # Encode as base64 (required by Android Device Owner provisioning)
    checksum_b64 = base64.b64encode(sha256_digest).decode('utf-8')
    checksum_hex = sha256_digest.hex()
    
    # Get certificate info
    from cryptography import x509
    from cryptography.hazmat.backends import default_backend
    cert = x509.load_der_x509_certificate(cert_der, default_backend())
    cert_info = {
        'subject': cert.subject.rfc4514_string(),
        'issuer': cert.issuer.rfc4514_string(),
        'serial_number': str(cert.serial_number),
        'not_valid_before': cert.not_valid_before.isoformat(),
        'not_valid_after': cert.not_valid_after.isoformat(),
        'extraction_method': method_used
    }
    
    return checksum_b64, checksum_hex, cert_info


def main():
    if len(sys.argv) < 2:
        print("Usage: python compute_cert_checksum.py <path_to_apk>")
        print("\nExample:")
        print("  python compute_cert_checksum.py uploads/apk/aoc_doapp_20251201_210745.apk")
        sys.exit(1)
    
    apk_path = sys.argv[1]
    
    try:
        checksum_b64, checksum_hex, cert_info = compute_certificate_checksum(apk_path)
        
        print("=" * 70)
        print("Android Device Owner Provisioning - Certificate Checksum")
        print("=" * 70)
        print(f"\nAPK File: {apk_path}")
        print(f"\nCertificate SHA-256 (Base64): {checksum_b64}")
        print(f"Certificate SHA-256 (Hex):     {checksum_hex}")
        print("\nCertificate Information:")
        print(f"  Subject:      {cert_info['subject']}")
        print(f"  Issuer:       {cert_info['issuer']}")
        print(f"  Serial:       {cert_info['serial_number']}")
        print(f"  Valid From:   {cert_info['not_valid_before']}")
        print(f"  Valid Until:  {cert_info['not_valid_after']}")
        print("\n" + "=" * 70)
        print("\nUse this checksum in your Device Owner QR code:")
        print(f'  "android.app.extra.PROVISIONING_DEVICE_ADMIN_SIGNATURE_CHECKSUM": "{checksum_b64}"')
        print("=" * 70)
        
    except Exception as e:
        print(f"ERROR: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

