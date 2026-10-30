@echo off
echo ======================================================
echo Iniciando CondoGestao (Backend + Frontend + Super Admin)
echo ======================================================

start "CondoGestao - Backend Django (Porta 8000)" cmd /k "cd /d %~dp0backend && run_backend.bat"
start "CondoGestao - Frontend Vue (Porta 5173)" cmd /k "cd /d %~dp0frontend && run_frontend.bat"
start "CondoGestao - Super Painel Global (Porta 5174)" cmd /k "cd /d %~dp0admin-painel && run_admin.bat"

echo.
echo Aplicacoes iniciadas com sucesso!
echo ------------------------------------------------------
echo 1. Backend REST API:        http://127.0.0.1:8000/api/
echo 2. Frontend Morador/Gestao: http://localhost:5173/
echo 3. Super Painel Global:     http://localhost:5174/
echo ------------------------------------------------------
pause
