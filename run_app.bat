@echo off
echo.
echo ========================================
echo   PlantPulse AI - Starting Application
echo ========================================
echo.

REM Check if data exists
if not exist "data\maintenance_logs.csv" (
    echo Generating sample data...
    python utils/data_generator.py
    echo.
)

echo Starting Streamlit application...
echo.
echo The app will open in your browser automatically.
echo Press Ctrl+C to stop the server.
echo.

streamlit run app.py

pause
