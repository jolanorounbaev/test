@echo off
echo Starting ProximityLinked Dev Environment...

REM Activate the virtual environment
call C:\Users\Jolan\miniconda3\Scripts\activate.bat C:\Users\Jolan\miniconda3\envs\prox_env

REM Start Django server
start cmd /k "cd /d C:\Users\Jolan\Desktop\proximitylinked && call activate prox_env && python manage.py runserver"

REM Start Daphne for Channels (on port 8001 for WebSockets)
start cmd /k "cd /d C:\Users\Jolan\Desktop\proximitylinked && call activate prox_env && daphne -b 127.0.0.1 -p 8001 config.asgi:application"

REM Start Celery worker
start cmd /k "cd /d C:\Users\Jolan\Desktop\proximitylinked && call activate prox_env && celery -A config worker --loglevel=info"

REM Start Celery beat scheduler
start cmd /k "cd /d C:\Users\Jolan\Desktop\proximitylinked && call activate prox_env && celery -A config beat --loglevel=info"



echo All services started! Close this window to stop them.
