@echo off

echo Setting up Privacy Protector...

REM Create a virtual environment
python -m venv venv

REM Activate the virtual environment
call venv\Scripts\activate.bat

REM Upgrade pip
pip install --upgrade pip

REM Install the package in editable mode
pip install -e .

echo Setup complete. Activate the virtual environment with 'venv\Scripts\activate.bat'