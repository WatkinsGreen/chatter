#!/bin/bash
# Setup script for Incident Response Chatbot

set -e

echo "🚀 Setting up Incident Response Chatbot..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env file created. Please edit it with your monitoring system configuration."
else
    echo "✅ .env file already exists."
fi

# Create SSL directory if it doesn't exist
if [ ! -d "nginx/ssl" ]; then
    mkdir -p nginx/ssl
    echo "📁 Created nginx/ssl directory for SSL certificates."
fi

# Check if SSL certificates exist, offer to create self-signed ones
if [ ! -f "nginx/ssl/cert.pem" ] || [ ! -f "nginx/ssl/key.pem" ]; then
    echo "🔐 SSL certificates not found."
    read -p "Would you like to create self-signed certificates for development? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🔐 Generating self-signed SSL certificates..."
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout nginx/ssl/key.pem -out nginx/ssl/cert.pem \
            -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
        echo "✅ Self-signed certificates created."
    fi
fi

# Ask for deployment mode
echo "🐳 Choose deployment mode:"
echo "1) Development (with live reload)"
echo "2) Production (optimized with nginx)"
read -p "Enter choice (1 or 2): " -n 1 -r
echo

if [[ $REPLY == "1" ]]; then
    echo "🔧 Starting in development mode..."
    docker-compose up --build
elif [[ $REPLY == "2" ]]; then
    echo "🚀 Starting in production mode..."
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d
    echo ""
    echo "✅ Services started successfully!"
    echo "📊 Application: http://localhost"
    echo "🔍 Health Check: http://localhost/health"
    echo "📚 API Docs: http://localhost/api/docs"
    echo ""
    echo "📝 View logs with: docker-compose logs -f"
    echo "🛑 Stop with: docker-compose down"
else
    echo "❌ Invalid choice. Exiting."
    exit 1
fi