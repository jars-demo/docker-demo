# syntax=docker/dockerfile:1
FROM python:3.13.16-slim-trixie
WORKDIR /app
COPY fetch_package.py .
# The secret is mounted for this one RUN step and exported as an environment variable.
# It is never written to a layer, the image config or the build history.
RUN --mount=type=secret,id=package_token,env=PACKAGE_TOKEN python fetch_package.py
COPY server.py .
EXPOSE 8000
CMD ["python", "server.py"]
