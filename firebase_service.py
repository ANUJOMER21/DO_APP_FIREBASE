"""
Firebase Service for AOC Device Control
Handles all Firebase Realtime Database operations
"""
import os
import json
import firebase_admin
from firebase_admin import credentials, db
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class FirebaseService:
    """Service for interacting with Firebase Realtime Database"""

    def __init__(self):
        """Initialize Firebase Admin SDK

        Render / cloud-friendly initialization:
        - Prefer credentials passed via FIREBASE_CREDENTIALS_JSON (env var)
        - Fallback to FIREBASE_CREDENTIALS_PATH pointing to a JSON file
        """
        self.database_url = os.getenv(
            'FIREBASE_DATABASE_URL',
            'https://aoc-device-control-default-rtdb.firebaseio.com/'
        )
        self.credentials_path = os.getenv(
            'FIREBASE_CREDENTIALS_PATH',
            'firebase-service-account.json'
        )
        self.credentials_json = os.getenv('FIREBASE_CREDENTIALS_JSON')

        # Initialize Firebase if not already initialized
        if not firebase_admin._apps:
            try:
                cred = None

                # 1. Prefer JSON from environment (best for platforms like Render)
                if self.credentials_json:
                    try:
                        cred_info = json.loads(self.credentials_json)
                        cred = credentials.Certificate(cred_info)
                        logger.info("Initializing Firebase from FIREBASE_CREDENTIALS_JSON")
                    except Exception as e:
                        logger.error(f"Failed to parse FIREBASE_CREDENTIALS_JSON: {e}")

                # 2. Fallback to credentials file path
                if cred is None and os.path.exists(self.credentials_path):
                    cred = credentials.Certificate(self.credentials_path)
                    logger.info(f"Initializing Firebase from credentials file at {self.credentials_path}")

                if cred is not None:
                    firebase_admin.initialize_app(cred, {
                        'databaseURL': self.database_url
                    })
                    logger.info("Firebase Admin SDK initialized successfully")
                else:
                    logger.warning(
                        "Firebase credentials not provided. "
                        "Set FIREBASE_CREDENTIALS_JSON or FIREBASE_CREDENTIALS_PATH."
                    )
            except Exception as e:
                logger.error(f"Failed to initialize Firebase: {str(e)}")
    
    def _get_devices_ref(self):
        """Get reference to devices node"""
        try:
            ref = db.reference('AOC/devices')
            return ref
        except Exception as e:
            logger.error(f"Error getting devices reference: {str(e)}")
            raise
    
    def _get_device_ref(self, device_id: str):
        """Get reference to a specific device"""
        try:
            ref = db.reference(f'AOC/devices/{device_id}')
            return ref
        except Exception as e:
            logger.error(f"Error getting device reference: {str(e)}")
            raise
    
    def get_all_devices(self) -> Dict:
        """Get all registered devices"""
        try:
            devices_ref = self._get_devices_ref()
            devices = devices_ref.get()
            return devices if devices else {}
        except Exception as e:
            logger.error(f"Error fetching all devices: {str(e)}")
            # Return empty dict if Firebase is not configured
            return {}
    
    def get_device_status(self, device_id: str) -> Optional[str]:
        """Get status of a specific device"""
        try:
            device_ref = self._get_device_ref(device_id)
            status_ref = device_ref.child('status')
            status = status_ref.get()
            return status
        except Exception as e:
            logger.error(f"Error fetching device status: {str(e)}")
            return None
    
    def send_command(self, device_id: str, command: str) -> bool:
        """Send command to a device
        
        Args:
            device_id: The Android device ID
            command: Command to send (lock, unlock, wallpaper:url)
        
        Returns:
            True if command sent successfully
        """
        try:
            device_ref = self._get_device_ref(device_id)
            command_ref = device_ref.child('command')
            command_ref.set(command)
            logger.info(f"Command '{command}' sent to device {device_id}")
            return True
        except Exception as e:
            logger.error(f"Error sending command to device {device_id}: {str(e)}")
            raise
    
    def get_device_info(self, device_id: str) -> Optional[Dict]:
        """Get full information about a device"""
        try:
            device_ref = self._get_device_ref(device_id)
            device_info = device_ref.get()
            return device_info
        except Exception as e:
            logger.error(f"Error fetching device info: {str(e)}")
            return None
    
    def update_device_status(self, device_id: str, status: str) -> bool:
        """Update device status (usually done by the device itself)"""
        try:
            device_ref = self._get_device_ref(device_id)
            status_ref = device_ref.child('status')
            status_ref.set(status)
            return True
        except Exception as e:
            logger.error(f"Error updating device status: {str(e)}")
            return False
    
    def delete_device(self, device_id: str) -> bool:
        """Remove a device from the database"""
        try:
            device_ref = self._get_device_ref(device_id)
            device_ref.delete()
            logger.info(f"Device {device_id} removed from database")
            return True
        except Exception as e:
            logger.error(f"Error deleting device {device_id}: {str(e)}")
            return False

