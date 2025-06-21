@echo off
echo Starting ProximityLinked Dev Environment...

REM Start Django server
start cmd /k "cd /d C:\Users\Jolan\Desktop\proximitylinked && call C:\Users\Jolan\miniconda3\Scripts\activate.bat prox_env && python manage.py runserver"

REM Start Daphne for Channels (on port 8001 for WebSockets)
start cmd /k "cd /d C:\Users\Jolan\Desktop\proximitylinked && call C:\Users\Jolan\miniconda3\Scripts\activate.bat prox_env && daphne -b 127.0.0.1 -p 8001 config.asgi:application"

REM Start Celery worker
start cmd /k "cd /d C:\Users\Jolan\Desktop\proximitylinked && call C:\Users\Jolan\miniconda3\Scripts\activate.bat prox_env && celery -A config worker --loglevel=info"

REM Start Celery beat scheduler
start cmd /k "cd /d C:\Users\Jolan\Desktop\proximitylinked && call C:\Users\Jolan\miniconda3\Scripts\activate.bat prox_env && celery -A config beat --loglevel=info"
