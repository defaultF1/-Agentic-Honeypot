FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
# Adjusted path for root build context
COPY honeypot/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
# Adjusted path for root build context
COPY honeypot/app/ ./app/

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=7860

# Expose port
EXPOSE 7860

# Run with uvicorn (Path adjusted relative to WORKDIR which is /app)
# Since we copied to /app/app, python sees 'app' package
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]