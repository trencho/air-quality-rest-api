#!/bin/bash

# Constants
DEBUG_FILE="/debug0"
DEBUG_FLAG_FILE="/debug1"
REQUIREMENTS_OS="requirements_os.txt"
REQUIREMENTS_PROD="requirements/prod.txt"
APP_PATH="/app/src/api/app.py"
GUNICORN_CONF="/app/docker/gunicorn.conf.py"

if [ ! -f $DEBUG_FILE ]; then
  touch $DEBUG_FILE

  if [ -e $REQUIREMENTS_OS ]; then
    apt-get install -y "$(cat $REQUIREMENTS_OS)"
  fi
  if [ -e $REQUIREMENTS_PROD ]; then
    pip3 install --no-cache-dir -r $REQUIREMENTS_PROD
  fi

  while getopts 'hd' flag; do
    case "${flag}" in
    h)
      echo "options:"
      echo "-h  show brief help"
      echo "-d  debug mode, no nginx or gunicorn, direct start with 'python3 $APP_PATH'"
      exit 0
      ;;
    d)
      echo "Debug!"
      touch $DEBUG_FLAG_FILE
      ;;
    *) ;;
    esac
  done
fi

if [ -e $DEBUG_FLAG_FILE ]; then
  echo "Running app in debug mode!"
  python3 $APP_PATH
else
  echo "Running app in production mode!"
  nginx && gunicorn -c $GUNICORN_CONF
fi
