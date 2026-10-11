import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent

# Load environment variables from .env file
load_dotenv(BASE_DIR / '.env')


class Config:
    """Base application configuration."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'default-dev-secret-key-change-in-production')
    
    # Session security
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = False  # Set to True when using HTTPS in production
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours in seconds

    # Persistent SQLite database kept inside the project.
    DATA_FOLDER = BASE_DIR / 'data'
    SQLITE_DATABASE_PATH = DATA_FOLDER / 'smart_food_court.sqlite3'
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL', f"sqlite:///{SQLITE_DATABASE_PATH.as_posix()}"
    )
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {}

    # Food Court Business Defaults
    FOOD_COURT_NAME = "Campus Smart Food Court"
    DEFAULT_AVG_PREP_TIME_MINS = 8  # minutes per order
    CANCELLATION_TIME_LIMIT_MINS = 5  # minutes within which an order can be cancelled if still Pending

    # Storage paths
    STATIC_FOLDER = BASE_DIR / 'app' / 'static'
    QR_FOLDER = STATIC_FOLDER / 'qr_codes'
    IMAGE_UPLOAD_FOLDER = STATIC_FOLDER / 'images' / 'menu'

    # CSRF Protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 7200  # 2 hours


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    ENV = 'development'


class TestingConfig(Config):
    """Testing configuration with SQLite in-memory database."""
    TESTING = True
    DEBUG = False
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_ENGINE_OPTIONS = {}


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    ENV = 'production'
    SESSION_COOKIE_SECURE = True


config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
