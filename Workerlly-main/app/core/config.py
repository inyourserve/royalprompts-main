import os

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application settings
    APP_NAME: str = "Workerly"
    DEBUG: bool = Field(default=False, env="DEBUG")

    # API settings
    API_V1_STR: str = "/api/v1"

    # Security settings
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 43200  # 30 days

    # AWS settings
    AWS_ACCESS_KEY: str = Field(..., env="AWS_ACCESS_KEY")
    AWS_SECRET_ACCESS_KEY: str = Field(..., env="AWS_SECRET_ACCESS_KEY")
    S3_BUCKET_NAME: str = Field(..., env="S3_BUCKET_NAME")
    AWS_REGION: str = (
        "ap-south-1"  # Make sure this matches your actual S3 bucket region
    )

    # Platform Fee
    PLATFORM_FEE_PERCENTAGE: float = 0.0  # Defined directly
    GST_PERCENTAGE: float = 18.0  # Defined directly

    # Firebase Configuration
    FIREBASE_SERVICE_ACCOUNT_PATH: str = os.getenv(
        "FIREBASE_SERVICE_ACCOUNT_PATH",
        "./firebase-service-account.json"
    )
    # FIREBASE_PROJECT_ID: str = os.getenv("FIREBASE_PROJECT_ID", "workerlly-notifications")

    # MSG91_TEMPLATE_ID = "672f510bd6fc0535714875e2"
    # MSG91_AUTH_KEY = "434154AnDd9jZr672f55b1P1"
    # GOOGLE_MAPS_API_KEY = "AIzaSyCl7gQBLcKtKZpph03jOIDGajfp41wdw2k"

    # # Platform Fee .env
    # PLATFORM_FEE_PERCENTAGE: float = Field(20.0, env="PLATFORM_FEE_PERCENTAGE")
    # GST_PERCENTAGE: float = Field(18.0, env="GST_PERCENTAGE")

    # Database settings
    # MONGO_URI: str = Field(default=None, env="MONGO_URI")

    # External services
    # MSG91_AUTH_KEY: str = Field(default=None, env="MSG91_AUTH_KEY")
    # MSG91_TEMPLATE_ID: str = Field(default=None, env="MSG91_TEMPLATE_ID")

    # Logging
    # LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")

    # User settings
    DEFAULT_USER_STATUS: bool = False  # for testing purpose

    # OTP settings
    OTP_EXPIRY_MINUTES: int = 10

    # Redis settings
    REDIS_HOST: str = Field(default="localhost", env="REDIS_HOST")
    REDIS_PORT: int = Field(default=6379, env="REDIS_PORT")
    REDIS_PASSWORD: str = Field(default="", env="REDIS_PASSWORD")

    # Redis job setup

    JOB_CACHE_EXPIRY: int = 360  # 6 minutes in seconds

    class Config:
        env_file = ".env"
        case_sensitive = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.validate_aws_credentials()
        self.validate_redis_settings()

    def validate_aws_credentials(self):
        if not all(
                [self.AWS_ACCESS_KEY, self.AWS_SECRET_ACCESS_KEY, self.S3_BUCKET_NAME]
        ):
            raise ValueError("AWS credentials and S3 bucket name must be set")

    def validate_redis_settings(self):
        if not all([self.REDIS_HOST, self.REDIS_PORT, self.REDIS_PASSWORD]):
            raise ValueError("Redis host, port, and password must be set")


settings = Settings()
