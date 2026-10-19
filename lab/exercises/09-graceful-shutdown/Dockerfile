FROM python:3.13.16-slim-trixie
WORKDIR /app
COPY migrate.py server.py start.sh ./
EXPOSE 8000
CMD ["sh", "start.sh"]
