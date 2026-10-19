FROM python:3.13.16-slim-trixie
WORKDIR /app
COPY server.py .
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8000/healthz || exit 1
CMD ["python", "server.py"]
