#!/bin/sh

/app/.venv/bin/python manage.py makemigrations
/app/.venv/bin/python manage.py migrate
#/app/.venv/bin/python manage.py runserver $SERVER_ADDRESS
/app/.venv/bin/gunicorn --workers=2 --threads=40 --bind $SERVER_ADDRESS app.wsgi:application