#!/bin/bash

if [ ! -f /debug0 ]; then
  touch /debug0

  if [ -e requirements_os.txt ]; then
    apt-get install -y "$(cat requirements_os.txt)"
  fi
  if [ -e requirements/prod.txt ]; then
    pip3 install --no-cache-dir -r requirements/prod.txt
  fi

  while getopts 'hd' flag; do
    case "${flag}" in
    h)
      echo "options:"
      echo "-h  show brief help"
      echo "-d  debug mode, no nginx or gunicorn, direct start with 'python3 app/app.py'"
      exit 0
      ;;
    d)
      echo "Debug!"
      touch /debug1
      ;;
    *) ;;
    esac
  done
fi

if [ -e /debug1 ]; then
  echo "Running app in debug mode!"
  python3 /app/src/api/app.py
else
  echo "Running app in production mode!"
  nginx && gunicorn -c /app/docker/gunicorn.conf.py
fi
