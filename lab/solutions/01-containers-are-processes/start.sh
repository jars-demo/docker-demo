#!/bin/sh
# Start the API in the foreground: the container lives exactly as long as this script does.
echo "starting the api"
python server.py
