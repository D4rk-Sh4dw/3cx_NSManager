FROM python:3.11-slim

WORKDIR /app

# Logs sofort ausgeben (sonst puffert Python print() im Container)
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
