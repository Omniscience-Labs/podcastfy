# Use Python 3.11 explicitly to satisfy requirements.txt version constraints
FROM python:3.11-slim

# Install system dependencies including ffmpeg
RUN apt-get update && \
    apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy all code into the container
COPY . .

# Install pip dependencies
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Install Doppler CLI to inject secrets
RUN curl -sLf --retry 3 --retry-delay 2 https://downloads.doppler.com/install.sh | sh

# Expose the port Flask will run on (match your server.py)
EXPOSE 10000

# Run the server via Doppler (DOPPLER_TOKEN must be in Render env vars)
CMD ["doppler", "run", "--", "python", "server.py"] 