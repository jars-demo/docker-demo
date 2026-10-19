FROM python:3.13.16-slim-trixie
WORKDIR /app
COPY server.py .
EXPOSE 8000
# The slim image has no curl. Python is already here, so ask with Python: urlopen raises on
# any status other than 2xx, and the non-zero exit marks the check as failed.
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=2)"]
CMD ["python", "server.py"]
