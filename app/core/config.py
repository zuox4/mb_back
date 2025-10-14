import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # Database
    # DATABASE_URL: str = os.getenv("DATABASE_URL")

    # JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 0.5

    # School Info
    SCHOOL_NAME: str = os.getenv("SCHOOL_NAME")
    SCHOOL_DOMAIN: str = os.getenv("SCHOOL_DOMAIN")

    # Resend Email Service
    RESEND_API_KEY: str = os.getenv("RESEND_API_KEY")
    RESEND_FROM_EMAIL: str = os.getenv("RESEND_FROM_EMAIL")

    # Frontend
    FRONTEND_URL: str = os.getenv("FRONTEND_URL")

    # Verification
    VERIFICATION_TOKEN_EXPIRE_HOURS: int = 24



    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    REFRESH_TOKEN_SECRET_KEY: str = "your-refresh-token-secret-key"



    DB_HOST: str = os.getenv("DB_HOST")  # Например: "192.168.1.100"
    DB_PORT: int = os.getenv("DB_PORT")
    DB_NAME: str = os.getenv("DB_NAME")  # Например: "myapp_db"
    DB_USER: str = os.getenv("DB_USER")  # Например: "remote_user"
    DB_PASSWORD : str = os.getenv("DB_PASSWORD")  # Например: "secure_password123"

    # SMTP Settings
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", "noreply@school1298.ru")
    SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "True").lower() == "true"

    GOOGLE_CLIENT_ID=os.getenv("GOOGLE_CLIENT_ID", "")

settings = Settings()