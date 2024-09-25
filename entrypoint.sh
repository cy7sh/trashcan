#!/bin/sh
set -e
exec gunicorn main:app
