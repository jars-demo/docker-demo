FROM python:3.13.16-slim-trixie
WORKDIR /app
COPY server.py .
ARG VERSION=dev
ENV APP_VERSION=$VERSION
EXPOSE 8000
CMD ["python", "server.py"]
