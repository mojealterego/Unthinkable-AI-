FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN groupadd --system ai && useradd --system --gid ai --home-dir /app ai
COPY services/gateway/requirements.txt /tmp/requirements.txt
RUN python -m pip install --no-cache-dir -r /tmp/requirements.txt
COPY services /app/services
USER ai
EXPOSE 8081
CMD ["uvicorn", "services.gateway.app:app", "--host", "0.0.0.0", "--port", "8081"]
