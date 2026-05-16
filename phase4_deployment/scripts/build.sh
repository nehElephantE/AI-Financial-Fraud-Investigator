#!/bin/bash

# Build script for production deployment

echo "Building Docker images..."

# Build API image
docker build -f docker/Dockerfile.api -t fraud-api:latest .

# Build UI image
docker build -f docker/Dockerfile.ui -t fraud-ui:latest .

# Build Nginx image
docker build -f docker/Dockerfile.nginx -t fraud-nginx:latest .

echo "✅ Build complete!"

# Tag for registry
if [ ! -z "$1" ]; then
    docker tag fraud-api:latest $1/fraud-api:latest
    docker tag fraud-ui:latest $1/fraud-ui:latest
    docker push $1/fraud-api:latest
    docker push $1/fraud-ui:latest
    echo "✅ Pushed to registry: $1"
fi