FROM python:3.13.16-slim-trixie
WORKDIR /app
COPY server.py .
# Inside a container, 127.0.0.1 is the container's own loopback. Published ports and other
# containers arrive on the container's network interface, so listen on all of them.
ENV HOST=0.0.0.0
EXPOSE 8000
CMD ["python", "server.py"]
