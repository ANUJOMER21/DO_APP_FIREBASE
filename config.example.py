"""
Configuration example file
Copy this to config.py and update with your values
"""
import os

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-in-production'
    
    # Firebase Configuration
    FIREBASE_CREDENTIALS_PATH = os.environ.get('FIREBASE_CREDENTIALS_PATH', 'firebase-service-account.json')
    FIREBASE_DATABASE_URL = os.environ.get('FIREBASE_DATABASE_URL', 
                                          'https://aoc-device-control-default-rtdb.firebaseio.com/')
    
    # Flask Configuration
    FLASK_HOST = os.environ.get('FLASK_HOST', '0.0.0.0')
    FLASK_PORT = int(os.environ.get('FLASK_PORT', 5000))
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
    
    # Dashboard Configuration
    DASHBOARD_BASE_URL = os.environ.get('DASHBOARD_BASE_URL', 'http://localhost:5000')
    APK_STORAGE_PATH = os.environ.get('APK_STORAGE_PATH', 'uploads/apk')
    
    # Upload Configuration
    MAX_APK_SIZE = 50 * 1024 * 1024  # 50MB max APK size

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

