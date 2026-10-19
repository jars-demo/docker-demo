#!/bin/sh
# Run migrations, then start the API.
set -e
python migrate.py
# exec replaces this shell with the server, so the server becomes PID 1 and receives the
# SIGTERM that docker stop sends.
exec python server.py
