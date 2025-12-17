@echo off
chcp 65001 >nul
echo Очистка кэша Python...
venv\Scripts\python clear_cache.py

echo.
echo Запуск бота...
venv\Scripts\python main.py
pause

