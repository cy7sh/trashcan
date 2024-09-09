#!/bin/sh
set -e
service ssh start
printenv
exec gunicorn main:app > gunicorn.log 2> gunicorn_error.log