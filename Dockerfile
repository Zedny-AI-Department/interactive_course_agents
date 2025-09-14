# Builds the Docker image for the application.
# Use the official Python image as a base
FROM python:3.10-slim

# non-root user for security
# RUN adduser --disabled-password appuser

# USER appuser

# Install dependencies
WORKDIR /src

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Run the application
# 
EXPOSE 7000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7000"]

# # Set the application version as an argument
# ARG APP_VERSION
# ENV APP_VERSION=${APP_VERSION}

# RUN echo "Building version $APP_VERSION"
