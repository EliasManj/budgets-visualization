@echo off
SETLOCAL EnableDelayedExpansion

REM Navigate to the script's directory
cd /d "%~dp0"

REM Activate Python virtual environment
call venv\Scripts\activate.bat

REM Initialize flags and default date
set UPDATE=false
set RESET=false
set ACCUMULATE=false
for /f %%i in ('powershell -Command "(Get-Date).Month"') do set MONTH=%%i
for /f %%i in ('powershell -Command "(Get-Date).Year"') do set YEAR=%%i

REM Check if any process is using port 5006 (requires netstat + findstr)
echo Checking for processes on port 5006
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5006') do (
    echo Killing process on port 5006 with PID %%a
    taskkill /PID %%a /F >nul 2>&1
)

REM Parse command-line arguments
:parse_args
if "%~1"=="" goto after_args
if "%~1"=="-u" (
    set UPDATE=true
) else if "%~1"=="--update" (
    set UPDATE=true
) else if "%~1"=="-r" (
    set RESET=true
) else if "%~1"=="--reset" (
    set RESET=true
) else if "%~1"=="-a" (
    set ACCUMULATE=true
) else if "%~1"=="--acc" (
    set ACCUMULATE=true
) else if not "!arg:~0,8!"=="" (
    set arg=%~1
    echo !arg! | findstr /b /c:"-m=" >nul && (
        for /f "tokens=2 delims==" %%m in ("!arg!") do set MONTH=%%m
    )
    echo !arg! | findstr /b /c:"--month=" >nul && (
        for /f "tokens=2 delims==" %%m in ("!arg!") do set MONTH=%%m
    )
    echo !arg! | findstr /b /c:"-y=" >nul && (
        for /f "tokens=2 delims==" %%y in ("!arg!") do set YEAR=%%y
    )
    echo !arg! | findstr /b /c:"--year=" >nul && (
        for /f "tokens=2 delims==" %%y in ("!arg!") do set YEAR=%%y
    )
)
shift
goto parse_args

:after_args

REM Reset the database if needed
if "%RESET%"=="true" (
    echo Deleting sqlite database
    del /f /q db\database.db
    echo Recreating sqlite database from schema.sql
    sqlite3 db\database.db < schema.sql
)

REM Activate venv (again in case we're running standalone)
call venv\Scripts\activate.bat

REM Run import scripts if update or reset is true
if "%UPDATE%"=="true" (
    call python amex.py
    call python bbva.py
    call python bbva_debit.py
    call python banamex.py
    call python cetes.py
) else if "%RESET%"=="true" (
    call python amex.py
    call python bbva.py
    call python bbva_debit.py
    call python banamex.py
    call python cetes.py
)

REM Apply DB modifications
sqlite3 db\database.db < db\modifications.sql

REM Launch Panel dashboard
panel serve Visualize.py --show --log-level debug

ENDLOCAL
