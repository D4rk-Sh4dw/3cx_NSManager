FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt && pip list

# Install openssl and generate self-signed certificate
RUN apt-get update && apt-get install -y openssl && \
    mkdir -p /app/certs && \
    openssl req -x509 -newkey rsa:4096 -keyout /app/certs/key.pem -out /app/certs/cert.pem -days 365 -nodes -subj "/CN=emergency-backend"

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
