FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for MySQL connector
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Default command (will be overridden by docker-compose)
CMD ["python", "generate_transactions.py"]