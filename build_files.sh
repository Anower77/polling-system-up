# build_files.sh
pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py makemigrations
python manage.py migrate 
python manage.py runserver 0.0.0.0:80