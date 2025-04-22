# Use the official Python image as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port (change if your server uses a different port)
EXPOSE 8000

# Set environment variables from .env file if present
# (docker-compose or cloud IDEs usually handle this, but this is a fallback)
ARG ENV_FILE=.env
RUN if [ -f "$ENV_FILE" ]; then \
    export $(grep -v '^#' $ENV_FILE | xargs) ;\
  fi

# Default command to run the server (update if your entrypoint is different)
CMD ["python", "server.py"]
