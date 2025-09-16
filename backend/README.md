# 🚀 RoyalPrompts Backend

## ✨ Overview

Clean, feature-wise FastAPI backend for RoyalPrompts mobile app and admin panel with anonymous login support.

## 🏗️ Architecture

```
backend/
├── app/                      # Main application
│   ├── api/                  # Feature-wise API endpoints
│   │   ├── mobile/           # 📱 Mobile app endpoints
│   │   │   ├── auth.py       # Anonymous login
│   │   │   ├── prompts.py    # Browse, detail, unlock
│   │   │   └── favorites.py  # Favorites management
│   │   ├── admin/            # 🛡️ Admin panel endpoints
│   │   │   ├── auth.py       # Admin login
│   │   │   ├── dashboard.py  # Dashboard stats
│   │   │   ├── prompts.py    # Prompts CRUD
│   │   │   ├── categories.py # Categories CRUD
│   │   │   └── users.py      # Users management
│   │   ├── shared/           # 🔄 Shared endpoints
│   │   │   └── upload.py     # File upload
│   │   └── v1/               # Legacy compatibility
│   │       └── endpoints/device.py
│   ├── core/                 # Core framework components
│   ├── models/               # Database models
│   ├── schemas/              # API contracts
│   ├── services/             # Business logic
│   └── utils/                # Utilities
├── scripts/                  # Utility scripts
├── uploads/                  # File storage
├── requirements.txt          # Dependencies
├── docker-compose.yml        # Container setup
└── start.sh                  # Startup script
```

## 🚀 Quick Start

### 1. Setup Environment
```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp env.example .env
# Edit .env with your MongoDB connection
```

### 2. Database Setup
```bash
# Create admin user
python scripts/create_admin.py

# Create sample data (optional)
python scripts/create_sample_data.py
```

### 3. Run Application
```bash
# Development
python main.py

# Production
./start.sh
```

### 4. Access
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 📱 Mobile App Endpoints

### Anonymous Login (No Registration Required)
```
POST /api/mobile/auth/anonymous-login    # Start anonymous session
```

### Browse Prompts
```
GET /api/mobile/prompts?category=new     # "New" tab
GET /api/mobile/prompts?category=trending # "Trending" tab  
GET /api/mobile/prompts?category=cinematic # "Cinematic" tab
GET /api/mobile/prompts?category=portra   # "Portra" tab
GET /api/mobile/prompts/{id}             # Prompt detail
POST /api/mobile/prompts/{id}/unlock     # Unlock prompt
```

### Favorites
```
GET  /api/mobile/favorites               # Get favorites
POST /api/mobile/favorites/{id}          # Toggle favorite
```

## 🛡️ Admin Panel Endpoints

### Authentication
```
POST /api/admin/auth/login               # Admin login
GET  /api/admin/auth/me                  # Admin profile
```

### Management
```
GET /api/admin/dashboard                 # Dashboard stats
GET /api/admin/manage                    # List prompts
POST /api/admin/manage                   # Create prompt
PUT /api/admin/manage/{id}               # Update prompt
DELETE /api/admin/manage/{id}            # Delete prompt
POST /api/admin/manage/upload-image      # Upload prompt image
```

## 🔧 Features

- ✅ **Anonymous Login**: No registration required for mobile users
- ✅ **Anonymous Browsing**: Browse prompts with anonymous login
- ✅ **Device Sessions**: 30-day anonymous sessions with device tokens
- ✅ **Favorites Management**: Save favorites per device
- ✅ **Content Unlocking**: Unlock premium prompts
- ✅ **Admin Management**: Full CRUD operations for content
- ✅ **File Upload**: Image upload for prompts
- ✅ **Rate Limiting**: API rate limiting per device
- ✅ **MongoDB Integration**: Scalable document database
- ✅ **Docker Support**: Containerized deployment

## 🔐 Authentication

### Mobile App (Anonymous)
- No user registration required
- Device-based anonymous sessions
- Automatic device ID generation
- 30-day session tokens
- Favorites and unlocks tied to device

### Admin Panel (Secure)
- Email/password authentication
- JWT tokens for admin sessions
- Role-based access control

## 📊 Database Models

- **Device**: Anonymous mobile users
- **Admin**: Admin panel users
- **Prompt**: AI prompts with categories
- **Category**: Prompt categories
- **Favorite**: User favorite prompts

## 🐳 Docker Deployment

```bash
# Start with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f
```

## 🔧 Development

### Add New Mobile Feature
1. Create `app/api/mobile/new_feature.py`
2. Add to `app/api/mobile/__init__.py`
3. Available at `/api/mobile/new_feature/`

### Add New Admin Feature
1. Create `app/api/admin/new_feature.py`
2. Add to `app/api/admin/__init__.py`
3. Available at `/api/admin/new_feature/`

## 📚 Documentation

- **Feature Architecture**: `FEATURE_WISE_ARCHITECTURE.md`
- **Cleanup Summary**: `CLEANUP_SUMMARY.md`
- **Clean Architecture**: `CLEAN_ARCHITECTURE.md`

## 🎯 Production Ready

- ✅ Clean feature-wise architecture
- ✅ Anonymous login for mobile apps
- ✅ Secure admin authentication
- ✅ Scalable database design
- ✅ Docker containerization
- ✅ Rate limiting and security
- ✅ File upload support
- ✅ Comprehensive API documentation

**Perfect for building Royal Prompts mobile app and admin panel!** 🚀
