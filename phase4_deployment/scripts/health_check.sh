#!/bin/bash

# Health check script for production

API_URL="http://localhost:8002"
UI_URL="http://localhost:8501"

echo "Running health checks..."

# Check API
if curl -f -s -o /dev/null "$API_URL/health"; then
    echo "✅ API is healthy"
else
    echo "❌ API is down"
    exit 1
fi

# Check UI
if curl -f -s -o /dev/null "$UI_URL"; then
    echo "✅ UI is healthy"
else
    echo "❌ UI is down"
    exit 1
fi

# Check database
docker exec fraud_mysql_prod mysqladmin ping -h localhost -u fraud_user -pfraud_password > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Database is healthy"
else
    echo "❌ Database is down"
    exit 1
fi

echo "✅ All services are healthy!"