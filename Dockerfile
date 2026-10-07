FROM python:3.12-slim

# Install system dependencies, Node.js, and supervisor
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    supervisor \
    ca-certificates \
    gnupg \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list \
    && apt-get update && apt-get install -y --no-install-recommends nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install WhatsApp bridge Node dependencies
COPY bridges/whatsapp/package.json ./bridges/whatsapp/
RUN cd ./bridges/whatsapp && npm install --omit=dev

# Copy project files
COPY . .

# Expose FastAPI port
EXPOSE 8000
EXPOSE 3001

CMD ["supervisord", "-c", "/app/supervisord.conf"]
