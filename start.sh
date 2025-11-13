#!/bin/bash

# Start script for CourtListener Database Browser
# This script helps start all services

echo "Starting CourtListener Database Browser..."

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed or not in PATH"
    echo "Please install Docker Desktop from https://www.docker.com/products/docker-desktop"
    echo ""
    echo "Or start Docker Desktop manually and ensure it's running, then try again."
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "Error: Docker is not running"
    echo "Please start Docker Desktop and wait for it to fully start, then try again."
    exit 1
fi

# Navigate to project directory
cd "$(dirname "$0")"

# Check if docker-compose or docker compose is available
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    echo "Error: docker-compose not found"
    echo "Please install docker-compose or use Docker Desktop which includes compose"
    exit 1
fi

echo "Using: $COMPOSE_CMD"
echo ""

# Start services
echo "Starting services..."
$COMPOSE_CMD up -d

echo ""
echo "Waiting for services to start..."
sleep 5

# Check service status
echo ""
echo "Service Status:"
$COMPOSE_CMD ps

echo ""
echo "Services are starting..."
echo ""
echo "Frontend: http://localhost:3000"
echo "Backend API: http://localhost:8001"
echo "API Docs: http://localhost:8001/docs"
echo ""
echo "To view logs: $COMPOSE_CMD logs -f"
echo "To stop services: $COMPOSE_CMD down"

