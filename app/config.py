import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-please-change')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///jobmatch.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = False
    TESTING = False
    BCRYPT_LOG_ROUNDS = 13
    
    # Gemini API Configuration
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    GEMINI_ENABLED = bool(os.environ.get('GEMINI_API_KEY'))

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    BCRYPT_LOG_ROUNDS = 4

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///test.db'
    BCRYPT_LOG_ROUNDS = 4
    WTF_CSRF_ENABLED = False

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    # Set to a secure key in production
    SECRET_KEY = os.environ.get('SECRET_KEY', 'prod-key-please-change')

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
} 