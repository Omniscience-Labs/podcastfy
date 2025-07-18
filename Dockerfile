FROM python:3.11-slim

# Install system dependencies including ffmpeg
RUN apt-get update && \
    apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

# Install Doppler CLI
RUN curl -sLf --retry 3 --retry-delay 2 https://downloads.doppler.com/install.sh | sh

EXPOSE 10000

CMD ["doppler", "run", "--", "python", "daytona_ui/server.py"]
