# Update to Python 3.11
FROM python:3.11-slim

# Install cron
RUN apt-get update && apt-get -y install cron

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application
COPY . .

# Add crontab file to cron directory
COPY crontab /etc/cron.d/app-cron

# Give execution rights on the cron job
RUN chmod 0644 /etc/cron.d/app-cron

# Apply cron job
RUN crontab /etc/cron.d/app-cron

# Create log file
RUN touch /var/log/cron.log

# Create a script to start both cron and tail the logs
RUN echo '#!/bin/bash\n\
    cron\n\
    tail -f /var/log/cron.log' > /app/start.sh

RUN chmod +x /app/start.sh

# Run the script
CMD ["/app/start.sh"]
