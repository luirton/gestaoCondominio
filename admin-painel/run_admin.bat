@echo off
echo ==============================================
echo Iniciando Servidor do Super Painel Global
echo ==============================================
cd /d "%~dp0"
"..\backend\venv\Scripts\python.exe" -m http.server 5174 --bind 127.0.0.1
