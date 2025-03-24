# Update to Python 3.11
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application
COPY . .

# Create a script to run the email generation
RUN echo '#!/bin/bash\n\
    python -m src.cron.cron' > /app/run.sh

RUN chmod +x /app/run.sh

# Run the script
CMD ["/app/run.sh"]
