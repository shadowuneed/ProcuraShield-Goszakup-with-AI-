@echo off
chcp 65001 >nul
title ProcuraShield Frontend (port 3100)

cd /d "%~dp0frontend"

if not exist "node_modules" (
    echo [1/2] Установка зависимостей...
    npm install
)

echo [2/2] Запуск Next.js dev-сервера...
echo.
echo ========================================
echo   ProcuraShield Frontend запущен
echo   http://localhost:3100
echo ========================================
echo.

npm run dev -- -p 3100
pause
