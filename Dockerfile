FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    chromium-driver \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Set up the working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Run the application
CMD ["python", "app.py"]
