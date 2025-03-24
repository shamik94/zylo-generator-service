# Update to Python 3.11
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application
COPY . .

# Default command (can be overridden by Heroku)
CMD ["python", "-m", "src.cron.cron"]
