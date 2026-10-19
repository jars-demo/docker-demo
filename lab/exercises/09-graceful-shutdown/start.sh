#!/bin/sh
# Run migrations, then start the API.
set -e
python migrate.py
python server.py
