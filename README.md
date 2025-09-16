# RoyalPrompts - Complete Project

A full-stack application for managing AI prompts with an admin dashboard and backend API.

## Project Structure

```
royalprompts-main/
├── admin/                  # Next.js Admin Dashboard (Frontend)
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── ...
├── backend/                # FastAPI Backend (API)
│   ├── main.py
│   ├── requirements.txt
│   └── ...
└── README.md              # This file
```

## Components

### 🎨 Frontend (admin)
- **Technology**: Next.js 15, TypeScript, Tailwind CSS
- **Features**: 
  - Admin dashboard for managing prompts and categories
  - CRUD operations for prompts and categories
  - Dark/Light theme support
  - Responsive design
  - File upload functionality

### 🚀 Backend (backend)
- **Technology**: FastAPI, Python
- **Features**:
  - RESTful API for prompts and categories
  - JWT authentication (simplified)
  - CORS support for frontend integration
  - Auto-generated API documentation
  - Mock data storage (ready for database integration)

## Quick Start

### Frontend Setup
```bash
cd admin
npm install
npm run dev
```
Frontend will be available at: http://localhost:3000

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
python main.py
```
Backend will be available at: http://localhost:8000

### API Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Development

### Frontend Development
- Built with Next.js 15 and TypeScript
- Uses Tailwind CSS for styling
- Implements reusable form components
- Supports file uploads and image previews

### Backend Development
- FastAPI with automatic API documentation
- Pydantic models for data validation
- CORS configured for frontend integration
- Ready for database integration (PostgreSQL recommended)

## Features

### Admin Dashboard
- ✅ Prompt management (Create, Read, Update, Delete)
- ✅ Category management (Create, Read, Update, Delete)
- ✅ File upload for prompt images
- ✅ Dark/Light theme toggle
- ✅ Responsive design
- ✅ Search and filtering
- ✅ Data tables with actions

### Backend API
- ✅ RESTful API endpoints
- ✅ CRUD operations for prompts and categories
- ✅ JWT authentication structure
- ✅ CORS support
- ✅ API documentation
- ✅ Error handling

## Next Steps

1. **Database Integration**: Replace mock data with PostgreSQL
2. **Authentication**: Implement proper JWT authentication
3. **File Storage**: Add proper file upload and storage
4. **Testing**: Add unit and integration tests
5. **Deployment**: Set up production deployment
6. **Monitoring**: Add logging and monitoring

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.
