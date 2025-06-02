FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libxcomposite1 libxdamage1 libxrandr2 libgbm1 libgtk-3-0 libasound2 libpangocairo-1.0-0 libxshmfence1 fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN playwright install chromium

CMD ["uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8080"]
