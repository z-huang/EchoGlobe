#!/bin/bash

NEED_MIGRATE=$(python manage.py showmigrations | grep '\[ \]' || true)

if [ -n "$NEED_MIGRATE" ]; then
  python manage.py migrate
fi

python manage.py createsuperuser --no-input

gunicorn --bind 0.0.0.0:8001 myproject.wsgi:application