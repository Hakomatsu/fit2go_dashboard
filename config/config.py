import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    # Environment configuration
    ENV = os.environ.get("FLASK_ENV", "development")

    # Basic Flask configuration
    SECRET_KEY = os.environ.get("SECRET_KEY")
    if not SECRET_KEY:
        if os.environ.get("FLASK_ENV") == "production":
            raise ValueError("SECRET_KEY must be set in production")
        SECRET_KEY = "dev-key-please-change-in-production"

    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    if not SQLALCHEMY_DATABASE_URI:
        if os.environ.get("FLASK_ENV") == "production":
            raise ValueError("DATABASE_URL must be set in production")
        SQLALCHEMY_DATABASE_URI = "sqlite:///fit2go.db"  # SQLiteを使用

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Timezone configuration
    TIMEZONE = "Asia/Tokyo"

    # API configuration
    API_TOKEN = os.environ.get("API_TOKEN")
    if not API_TOKEN:
        if os.environ.get("FLASK_ENV") == "production":
            raise ValueError("API_TOKEN must be set in production")
        API_TOKEN = "dev-token-please-change-in-production"

    # Google Fit OAuth 2.0 configuration
    GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "your-client-id")
    GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "your-client-secret")
    GOOGLE_REDIRECT_URI = os.environ.get("GOOGLE_REDIRECT_URI", "http://localhost:5000/google-fit/callback")


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False

    def __init__(self):
        super().__init__()
        required_vars = ["SECRET_KEY", "DATABASE_URL", "API_TOKEN"]
        missing = [var for var in required_vars if not os.environ.get(var)]
        if missing:
            raise ValueError(
                f'The following environment variables are required in production: {", ".join(missing)}'
            )


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "postgresql://localhost/fit2go_dashboard_test"


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
