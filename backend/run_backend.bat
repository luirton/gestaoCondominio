@echo off
echo ==============================================
echo Iniciando Backend Django (CondoGestao API)
echo ==============================================
cd /d "%~dp0"
call venv\Scripts\activate
python manage.py runserver 0.0.0.0:8000
