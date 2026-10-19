# syntax=docker/dockerfile:1
FROM python:3.13.16-slim-trixie
WORKDIR /app
ARG PACKAGE_TOKEN
COPY fetch_package.py .
RUN PACKAGE_TOKEN=$PACKAGE_TOKEN python fetch_package.py
COPY server.py .
EXPOSE 8000
CMD ["python", "server.py"]
