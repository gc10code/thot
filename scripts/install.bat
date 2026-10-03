@echo off
:: Create a virtual environment in .venv and install THOT.
:: Usage: scripts\install.bat [extras]   (default extras: gui,live)
setlocal

set "EXTRAS=%~1"
if "%EXTRAS%"=="" set "EXTRAS=gui,live"
set "ROOT=%~dp0.."

python -m venv "%ROOT%\.venv" || goto :error
"%ROOT%\.venv\Scripts\python.exe" -m pip install --upgrade pip || goto :error
"%ROOT%\.venv\Scripts\python.exe" -m pip install -e "%ROOT%[%EXTRAS%]" || goto :error

echo.
echo THOT installed. Activate with:  .venv\Scripts\activate
echo Then run:  thot --help   ^|   thot gui   ^|   thot live
exit /b 0

:error
echo Installation failed.
exit /b 1
