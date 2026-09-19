FROM python:3.12-slim
WORKDIR /app
COPY validate_shard.py .
COPY shards/ /data/shards/
CMD ["python", "validate_shard.py"]
