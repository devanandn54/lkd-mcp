# Dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --no-cache-dir playwright==1.40.0 fastapi==0.104.1 uvicorn==0.24.0

RUN playwright install chromium
RUN playwright install-deps chromium

COPY linkedin_scraper.py /app/

ENV PORT=8080
ENV PYTHONUNBUFFERED=1

EXPOSE 8080

CMD ["uvicorn", "linkedin_scraper:app", "--host", "0.0.0.0", "--port", "8080"]