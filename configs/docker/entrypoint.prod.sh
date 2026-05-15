#!/bin/sh

mkdir -p /var/log/gunicorn
chown -R app:app /var/log/gunicorn

python manage.py collectstatic --no-input
python manage.py makemigrations
python manage.py migrate
exec "$@"
