#!/bin/bash

echo "🚀 Starting RoyalPrompts Backend API..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp env.example .env
    echo "⚠️  Please update .env file with your configuration"
fi

# Check if uploads directory exists
if [ ! -d "uploads" ]; then
    echo "📁 Creating uploads directory..."
    mkdir -p uploads/images uploads/thumbnails
fi

# Test MongoDB connection
echo "🗄️  Testing MongoDB connection..."
if python3 scripts/test_connection.py > /dev/null 2>&1; then
    echo "✅ MongoDB connection successful"
else
    echo "❌ MongoDB connection failed"
    echo "Please check your MONGODB_URL in .env file"
    echo ""
    echo "Examples:"
    echo "  Local: MONGODB_URL=mongodb://localhost:27017/royalprompts"
    echo "  Atlas: MONGODB_URL=mongodb+srv://user:pass@cluster.mongodb.net/royalprompts"
    echo ""
    echo "To start local MongoDB with Docker:"
    echo "docker run -d -p 27017:27017 --name mongodb mongo:latest"
    echo ""
    read -p "Continue anyway? (y/N): " continue_anyway
    if [[ ! $continue_anyway =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "🐍 Creating virtual environment..."
    python3 -m venv venv
fi

echo "📦 Activating virtual environment and installing dependencies..."
source venv/bin/activate
pip install -r requirements.txt

# Ask if user wants to seed database
echo ""
read -p "🌱 Do you want to seed the database with sample data? (y/N): " seed_db
if [[ $seed_db =~ ^[Yy]$ ]]; then
    echo "🌱 Seeding database..."
    python3 scripts/seed_data.py
fi

echo ""
echo "🎉 Starting the server..."
echo "📖 API Documentation: http://localhost:8000/docs"
echo "🔧 Admin Panel API: http://localhost:8000/admin/"
echo "💡 Health Check: http://localhost:8000/health"
echo ""

# Start the server
python3 main.py
