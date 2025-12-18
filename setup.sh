#!/bin/bash

echo "=== BookWhisperer Setup ==="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "Error: Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✓ Docker and Docker Compose are installed"
echo ""

# Create .env file if it doesn't exist
if [ ! -f backend/.env ]; then
    echo "Creating .env file from .env.example..."
    cp backend/.env.example backend/.env
    echo "✓ Created backend/.env"
    echo "⚠ Please edit backend/.env to configure your settings"
else
    echo "✓ backend/.env already exists"
fi

echo ""

# Create storage directories
echo "Creating storage directories..."
mkdir -p backend/storage/uploads backend/storage/audio
touch backend/storage/uploads/.gitkeep
touch backend/storage/audio/.gitkeep
echo "✓ Storage directories created"
echo ""

# Start Docker containers
echo "Starting Docker containers..."
docker-compose up -d db redis ollama
echo "✓ Database, Redis, and Ollama containers started"
echo ""

# Wait for database to be ready
echo "Waiting for database to be ready..."
sleep 5

# Build and start backend
echo "Building backend container..."
docker-compose build backend
echo "✓ Backend container built"
echo ""

echo "Starting backend services..."
docker-compose up -d backend celery_worker flower
echo "✓ Backend services started"
echo ""

echo "=== Setup Complete ==="
echo ""
echo "Services available at:"
echo "  - API Documentation: http://localhost:8000/docs"
echo "  - API: http://localhost:8000"
echo "  - Flower (Celery monitoring): http://localhost:5555"
echo "  - PostgreSQL: localhost:5432"
echo "  - Redis: localhost:6379"
echo "  - Ollama: http://localhost:11434"
echo ""
echo "To view logs: docker-compose logs -f"
echo "To stop services: docker-compose down"
echo ""
echo "Note: You may need to pull an Ollama model:"
echo "  docker exec -it bookwhisperer_ollama ollama pull llama2"
echo ""
