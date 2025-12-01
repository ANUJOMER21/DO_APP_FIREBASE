# Android Device Owner Provisioning Setup

## Fixed APK Download Endpoint

The `/api/apk/download/<filename>` endpoint has been fixed to:
- Return raw APK file bytes (NO redirect, NO JSON, NO HTML)
- Use correct headers: `Content-Type: application/vnd.android.package-archive`
- Stream files in binary mode
- Validate file paths for security

## Computing Certificate SHA-256 Checksum

### Method 1: Using Python Script (Recommended)

```bash
python compute_cert_checksum.py uploads/apk/aoc_doapp_20251201_210745.apk
```

**Requirements:**
- Android SDK build-tools (for `apksigner`) OR
- Java JDK + OpenSSL (for `jarsigner` + `openssl`)

The script will output:
- Certificate SHA-256 in Base64 (use this in QR code)
- Certificate SHA-256 in Hex
- Certificate information (subject, issuer, validity)

### Method 2: Using Command Line Tools

#### Using apksigner (Android SDK):
```bash
# Extract certificate
apksigner verify --print-certs your_app.apk > cert.pem

# Compute SHA-256
openssl x509 -in cert.pem -noout -fingerprint -sha256 | \
  cut -d'=' -f2 | tr -d ':' | xxd -r -p | base64
```

#### Using keytool (Java JDK):
```bash
# Extract APK as ZIP, get META-INF/*.RSA
unzip -p your_app.apk META-INF/*.RSA > cert.rsa

# Extract certificate
openssl pkcs7 -inform DER -in cert.rsa -print_certs -outform PEM > cert.pem

# Compute SHA-256
openssl x509 -in cert.pem -noout -fingerprint -sha256 | \
  cut -d'=' -f2 | tr -d ':' | xxd -r -p | base64
```

## Device Owner QR Code JSON Template

Use this JSON structure in your QR code:

```json
{
  "android.app.extra.PROVISIONING_DEVICE_ADMIN_COMPONENT_NAME": "com.aoc.aoc_doapp/.MyDeviceAdminReceiver",
  "android.app.extra.PROVISIONING_DEVICE_ADMIN_PACKAGE_DOWNLOAD_LOCATION": "https://your-domain.com/api/apk/download/aoc_doapp_20251201_210745.apk",
  "android.app.extra.PROVISIONING_DEVICE_ADMIN_SIGNATURE_CHECKSUM": "REPLACE_WITH_CERTIFICATE_SHA256_BASE64",
  "android.app.extra.PROVISIONING_LEAVE_ALL_SYSTEM_APPS_ENABLED": true
}
```

**Important Notes:**
1. **Download URL must be HTTPS** in production (required by Android)
2. **Certificate checksum** must match the APK's signing certificate (not file hash)
3. **Component name** format: `package.name/.ReceiverClassName`
4. **No spaces** in JSON (use compact format for QR code)

## Testing the Endpoint

```bash
# Test APK download
curl -I https://your-domain.com/api/apk/download/aoc_doapp_20251201_210745.apk

# Expected headers:
# Content-Type: application/vnd.android.package-archive
# Content-Disposition: attachment; filename="aoc_doapp_20251201_210745.apk"
# Content-Length: <file_size>
```

## Troubleshooting

**Error: "Can't setup device. Contact your IT admin."**
- ✅ Verify APK download URL returns raw file (not HTML/JSON)
- ✅ Verify `Content-Type: application/vnd.android.package-archive`
- ✅ Verify URL is HTTPS (required in production)
- ✅ Verify certificate checksum matches APK's signing certificate
- ✅ Verify component name matches your DeviceAdminReceiver

**Checksum Mismatch:**
- Use certificate SHA-256, NOT file SHA-256
- Run `compute_cert_checksum.py` to get correct value
- Ensure APK is signed with the same certificate used in checksum

