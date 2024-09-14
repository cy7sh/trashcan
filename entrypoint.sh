#!/bin/sh
set -e
service ssh start
exec gunicorn main:app
