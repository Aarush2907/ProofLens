FROM python:3.12-slim

# The API and the MCP child process run as a normal user. The embedding model
# is cached under that user's home, which Compose mounts as a volume.
RUN useradd --create-home --uid 1000 app && mkdir -p /home/app/.cache && chown -R app:app /home/app

WORKDIR /app

COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend /app/backend
COPY database /app/database
RUN chown -R app:app /app

USER app
WORKDIR /app/backend
ENV PYTHONUNBUFFERED=1
EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=5 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=4)"

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
