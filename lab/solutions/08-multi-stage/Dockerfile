# Stage 1: build. The full image has gcc and libpq's headers, which psycopg-c needs to compile.
FROM python:3.13.16-trixie AS build
RUN python -m venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: run. Only the slim base, the runtime libpq and the finished virtual environment.
FROM python:3.13.16-slim-trixie
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/*
RUN useradd --system --uid 10001 --no-create-home app
COPY --from=build /opt/venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH
WORKDIR /app
COPY server.py .
USER app
EXPOSE 8000
CMD ["python", "server.py"]
