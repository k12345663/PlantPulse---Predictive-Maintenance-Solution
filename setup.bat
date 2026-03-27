@echo off
echo Installing PlantPulse AI dependencies...
pip install -r requirements.txt

echo.
echo Generating sample data...
python utils/data_generator.py

echo.
echo Setup complete!
echo.
echo To run the application:
echo   streamlit run app.py
echo.
pause
