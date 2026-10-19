FROM python:3.13.16-slim-trixie
RUN useradd --system --uid 10001 --no-create-home app
WORKDIR /app
COPY server.py .
USER app
VOLUME /data
EXPOSE 8000
CMD ["python", "server.py"]
