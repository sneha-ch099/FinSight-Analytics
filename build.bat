@echo off
setlocal
cd /d "%~dp0"
echo Building MarketLens Stock Analysis App
where python >nul 2>nul
if errorlevel 1 (echo Python not found. Install Python 3.11 or 3.12 and add it to PATH.& pause & exit /b 1)
if not exist ".venv\Scripts\python.exe" (python -m venv .venv || goto :error)
".venv\Scripts\python.exe" -m pip install --upgrade pip || goto :error
".venv\Scripts\python.exe" -m pip install -r requirements.txt || goto :error
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean --onefile --windowed --name FinanceProject main.py || goto :error
echo Build complete. Executable: dist\FinanceProject.exe
pause
exit /b 0
:error
echo Build failed. Read the error messages above.
pause
exit /b 1
