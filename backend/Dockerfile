FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt && pip list

# Copy entrypoint script
# Install system dependencies
RUN apt-get update && apt-get install -y openssl dos2unix

COPY . .

# Ensure entrypoint is executable and has Unix line endings
RUN chmod +x /app/entrypoint.sh && dos2unix /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
