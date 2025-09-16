# Configuration

This covers the config setup for Workerlly. Most stuff is pretty standard but there are some hardcoded values you should know about.

## Environment Variables

### Required Env Vars

```bash
# App basics
APP_NAME=Workerly
SECRET_KEY=your_secret_key
DEBUG=False
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=43200  # 30 days

# API
API_V1_STR=/api/v1

# Database - this is hardcoded in database.py
# mongodb+srv://workerllyapp:fGbE276ePop1iapV@backendking.y6lcith.mongodb.net/
# Database name: workerlly

# AWS S3
AWS_ACCESS_KEY=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key  
S3_BUCKET_NAME=your_bucket_name
AWS_REGION=ap-south-1

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password
JOB_CACHE_EXPIRY=360  # 6 minutes

# Firebase
FIREBASE_SERVICE_ACCOUNT_PATH=./firebase-service-account.json
# OR use FIREBASE_CREDENTIALS_JSON as env var for Docker
```

### Hardcoded Values

These are baked into the code:

```bash
# Razorpay (live keys in seeker/wallet.py)
RAZORPAY_KEY_ID=rzp_live_DBqXvgaIdpnYNz
RAZORPAY_KEY_SECRET=NgCUYG2cmhYfSJEoaamXa4Zd

# MSG91 (in msg91.py)
MSG91_AUTH_KEY=434154AnDd9jZr672f55b1P1
MSG91_TEMPLATE_ID=672f510bd6fc0535714875e2

# Business config (in config.py)
PLATFORM_FEE_PERCENTAGE=0.0
GST_PERCENTAGE=18.0
DEFAULT_USER_STATUS=False  # For testing
OTP_EXPIRY_MINUTES=10

# Google Maps API (commented out in config.py)
# GOOGLE_MAPS_API_KEY=AIzaSyCl7gQBLcKtKZpph03jOIDGajfp41wdw2k
```

## Main Config File

`app/core/config.py` - pretty standard Pydantic setup:

```python
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Workerly"
    DEBUG: bool = Field(default=False, env="DEBUG")
    API_V1_STR: str = "/api/v1"
    
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 43200  # 30 days
    
    # AWS stuff
    AWS_ACCESS_KEY: str = Field(..., env="AWS_ACCESS_KEY")
    AWS_SECRET_ACCESS_KEY: str = Field(..., env="AWS_SECRET_ACCESS_KEY")
    S3_BUCKET_NAME: str = Field(..., env="S3_BUCKET_NAME")
    AWS_REGION: str = "ap-south-1"
    
    # Business rules
    PLATFORM_FEE_PERCENTAGE: float = 0.0
    GST_PERCENTAGE: float = 18.0
    
    # Firebase
    FIREBASE_SERVICE_ACCOUNT_PATH: str = os.getenv(
        "FIREBASE_SERVICE_ACCOUNT_PATH",
        "./firebase-service-account.json"
    )
    
    DEFAULT_USER_STATUS: bool = False  # for testing
    OTP_EXPIRY_MINUTES: int = 10
    
    # Redis settings
    REDIS_HOST: str = Field(default="localhost", env="REDIS_HOST")
    REDIS_PORT: int = Field(default=6379, env="REDIS_PORT")
    REDIS_PASSWORD: str = Field(default="", env="REDIS_PASSWORD")
    JOB_CACHE_EXPIRY: int = 360  # 6 minutes
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    def validate_aws_credentials(self):
        if not all([self.AWS_ACCESS_KEY, self.AWS_SECRET_ACCESS_KEY, self.S3_BUCKET_NAME]):
            raise ValueError("AWS credentials and S3 bucket name must be set")
    
    def validate_redis_settings(self):
        if not all([self.REDIS_HOST, self.REDIS_PORT, self.REDIS_PASSWORD]):
            raise ValueError("Redis host, port, and password must be set")
```

## Database Setup

Database connection is hardcoded in `app/db/models/database.py`:

```python
import certifi
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient

MONGO_CONNECTION_STRING = (
    "mongodb+srv://workerllyapp:fGbE276ePop1iapV@backendking.y6lcith.mongodb.net/"
)

# Dual client setup
client = MongoClient(MONGO_CONNECTION_STRING, tlsCAFile=certifi.where())
db = client.workerlly

motor_client = AsyncIOMotorClient(MONGO_CONNECTION_STRING, tlsCAFile=certifi.where())
motor_db = motor_client.workerlly
```

## Payment Setup

Razorpay is configured in `app/utils/razorpay_utils.py` but the actual keys are in `seeker/wallet.py`:

```python
# Live credentials hardcoded
razorpay_config = RazorpayConfig(
    key_id="rzp_live_DBqXvgaIdpnYNz", 
    key_secret="NgCUYG2cmhYfSJEoaamXa4Zd"
)
```

## MSG91 SMS

OTP service is in `app/utils/msg91.py`:

```python
MSG91_TEMPLATE_ID = "672f510bd6fc0535714875e2"
MSG91_AUTH_KEY = "434154AnDd9jZr672f55b1P1"

async def send_otp(mobile: str, otp: str = "", otp_expiry: str = "10"):
    url = f"https://control.msg91.com/api/v5/otp?template_id={MSG91_TEMPLATE_ID}&mobile={mobile}&authkey={MSG91_AUTH_KEY}&otp={otp}&otp_expiry={otp_expiry}"
    # Makes HTTP request to MSG91

async def verify_otp(mobile: str, otp: str):
    url = f"https://control.msg91.com/api/v5/otp/verify?mobile={mobile}&otp={otp}&authkey={MSG91_AUTH_KEY}"
    # Verifies with MSG91
```

## S3 File Storage

S3 client setup in `app/utils/s3_manager.py`:

```python
import boto3
from app.core.config import settings

def get_s3_client():
    return boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION,
    )

def upload_file_to_s3(file, folder, filename):
    try:
        key = f"{folder}/{filename}"
        content_type, _ = mimetypes.guess_type(filename)
        s3_client.upload_fileobj(
            file, settings.S3_BUCKET_NAME, key, 
            ExtraArgs={"ContentType": content_type}
        )
        return key
    except ClientError:
        return None
```

## Firebase Setup

Firebase service in `app/services/firebase_service.py` handles dual credential loading:

```python
def __init__(self):
    try:
        # Try environment variable first (for Docker)
        firebase_creds = os.getenv("FIREBASE_CREDENTIALS_JSON")
        if firebase_creds:
            cred_dict = json.loads(firebase_creds)
            cred = credentials.Certificate(cred_dict)
        else:
            # Fallback to file (local dev)
            cred = credentials.Certificate(settings.FIREBASE_SERVICE_ACCOUNT_PATH)
        
        firebase_admin.initialize_app(cred)
    except Exception as e:
        logger.error(f"Firebase initialization failed: {str(e)}")
        raise e
```

## CORS Setup

Pretty open CORS policy in `app/main.py`:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Dev vs Production

**Development:**
- Debug mode on  
- Local MongoDB/Redis if configured
- Mock OTP (always accepts "1234")
- Console logging

**Production:**
- Debug off
- Cloud services (MongoDB Atlas, Firebase, etc.)
- Real SMS delivery
- Structured logging

## Security Notes

Some things to be aware of:

1. **Hardcoded credentials** - Production keys are in the code
2. **Open CORS** - Allows all origins currently  
3. **No rate limiting** - Could be added later
4. **Long JWT expiry** - 30 days might be too long for some use cases

The config setup is pretty straightforward but having credentials hardcoded isn't ideal for production. Would be better to move them to environment variables. 