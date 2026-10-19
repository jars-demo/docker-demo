FROM python:3.13.16-slim-trixie
RUN useradd --system --uid 10001 --no-create-home app
# Create the data directory in the image and give it to the app user. A new, empty named
# volume copies this directory's owner and mode the first time it is mounted.
RUN mkdir /data && chown app:app /data
WORKDIR /app
COPY server.py .
USER app
VOLUME /data
EXPOSE 8000
CMD ["python", "server.py"]
