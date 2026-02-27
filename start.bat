@echo off
chcp 65001 >nul
title ProcuraShield — Полный запуск

echo ========================================
echo   ProcuraShield — Запуск всех сервисов
echo ========================================
echo.

cd /d "%~dp0"

echo Запуск Backend (порт 8100)...
start "ProcuraShield Backend" cmd /c "%~dp0start_backend.bat"

timeout /t 3 /nobreak >nul

echo Запуск Frontend (порт 3100)...
start "ProcuraShield Frontend" cmd /c "%~dp0start_frontend.bat"

echo.
echo ========================================
echo   Backend:  http://localhost:8100/docs
echo   Frontend: http://localhost:3100
echo   Логин:    admin@procurashield.kz
echo   Пароль:   admin123!
echo ========================================
echo.
echo Оба сервиса запущены в отдельных окнах.
echo Закройте это окно или нажмите любую клавишу.
pause
