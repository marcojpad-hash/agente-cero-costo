FROM python:3.12-slim
WORKDIR /app
COPY gestor.py PROMPT_GESTOR.md ./
ENV BOT_DATA_DIR=/app/datos PYTHONUNBUFFERED=1
VOLUME ["/app/datos"]
CMD ["python", "gestor.py"]
