@echo off
setlocal EnableExtensions EnableDelayedExpansion

cd /d "%~dp0"

set "PORT=8502"
set "VENV_DIR=.venv"
set "VENV_PY=%VENV_DIR%\Scripts\python.exe"
set "VENV_PIP=%VENV_DIR%\Scripts\pip.exe"

echo ==========================================
echo PDF to Excel Portable Launcher
echo Folder: %cd%
echo ==========================================
echo.

set "PY_CMD="
where py >nul 2>nul
if %errorlevel%==0 set "PY_CMD=py -3"
if not defined PY_CMD (
  where python >nul 2>nul
  if %errorlevel%==0 set "PY_CMD=python"
)

if not defined PY_CMD (
  echo [ERROR] Python tidak ditemukan.
  echo Install Python 3.10+ lalu jalankan lagi.
  pause
  exit /b 1
)

if not exist "%VENV_PY%" (
  echo [1/4] Membuat virtual environment lokal...
  %PY_CMD% -m venv "%VENV_DIR%"
  if errorlevel 1 (
    echo [ERROR] Gagal membuat virtual environment.
    pause
    exit /b 1
  )
)

echo [2/4] Install / update dependency...
"%VENV_PY%" -m pip install --upgrade pip >nul 2>nul
"%VENV_PIP%" install -r requirements.txt
if errorlevel 1 (
  echo [ERROR] Gagal install dependency.
  echo Pastikan internet tersedia lalu jalankan ulang.
  pause
  exit /b 1
)

if exist "C:\Program Files\Tesseract-OCR\tesseract.exe" (
  set "TESSDATA_PREFIX=C:\Program Files\Tesseract-OCR\tessdata"
)

echo [3/4] Menjalankan aplikasi...
echo URL: http://127.0.0.1:%PORT%
echo Tekan CTRL+C untuk stop.
echo.

echo [4/4] Membuka browser...
start "" "http://127.0.0.1:%PORT%"

"%VENV_PY%" -m streamlit run app.py --server.address 127.0.0.1 --server.port %PORT% --server.headless true

echo.
echo Aplikasi berhenti.
pause
