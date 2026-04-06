#!/bin/bash
set -e

# Constants
APP_PATH="/app/src/api/app.py"

# Check if APP_ENV is set to 'development' for debug mode
if [ "${APP_ENV}" = "development" ]; then
  echo "Running app in development mode!"
  python3 $APP_PATH
else
  echo "Running app in production mode!"
  nginx && gunicorn -c "/app/docker/gunicorn.conf.py"
fi
