FROM python:3.10-slim AS base

WORKDIR /app

FROM base AS builder
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM builder AS final
COPY . .

EXPOSE 8080

CMD ["python", "app.py"]
