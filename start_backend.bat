@echo off
chcp 65001 >nul
title ProcuraShield Backend (port 8100)

cd /d "%~dp0backend"

if not exist "venv" (
    echo [1/3] Создание виртуального окружения...
    python -m venv venv
)

echo [2/3] Активация venv...
call venv\Scripts\activate.bat

echo [3/3] Установка зависимостей...
pip install -r requirements.txt -q

echo.
echo ========================================
echo   ProcuraShield Backend запущен
echo   API Docs: http://localhost:8100/docs
echo ========================================
echo.

uvicorn app.main:app --reload --port 8100 --host 0.0.0.0
pause
