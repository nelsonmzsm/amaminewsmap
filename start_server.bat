@echo off
echo Starting Amami News Map Server...
echo --------------------------------
echo Installing dependencies...
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Installation failed. Please check if Python is installed.
    echo.
    pause
    exit /b
)

echo.
echo --------------------------------
echo Starting Server...
echo Do NOT close this window while using the app.
echo.
echo Opening http://localhost:5000 in your browser...
start http://localhost:5000
python app.py
pause
