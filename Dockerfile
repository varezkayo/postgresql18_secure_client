FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && mkdir -p /app/logs && chown 10001:10001 /app/logs
COPY pinger.py db.py config.toml ./
USER 10001:10001
CMD ["python", "-u", "pinger.py"]
