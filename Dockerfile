FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ .

# Copy import scripts to /app
COPY import_directly.py /app/import_directly.py
COPY import_citations_parallel.py /app/import_citations_parallel.py
COPY import_parallel.py /app/import_parallel.py

# Expose port
EXPOSE 8000

# Create startup script
RUN echo '#!/bin/bash\n\
set -e\n\
echo "Running database migrations..."\n\
alembic upgrade head\n\
echo "Starting uvicorn server..."\n\
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --log-level info\n\
' > /app/start.sh && chmod +x /app/start.sh

# Default command
CMD ["/app/start.sh"]
