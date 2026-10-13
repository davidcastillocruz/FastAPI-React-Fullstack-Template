# Development image of the backend: the code is mounted from your computer (see docker-compose.yml)
FROM python:3.14-slim
WORKDIR /app

# Dependencies first: Docker reuses this layer while requirements.txt doesn't change
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Applies the pending migrations, then starts the API reloading on every change
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload"]
