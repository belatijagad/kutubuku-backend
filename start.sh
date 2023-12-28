#!bin/sh

python manage.py flush --no-input
python manage.py makemigrations --merge --no-input
python manage.py migrate --no-input
python manage.py runserver 0.0.0.0:80