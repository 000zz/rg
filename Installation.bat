@echo off
setlocal EnableDelayedExpansion

REM --------------------------------------------------------------------
REM Check if Python is installed
set python_exe=python.exe
for /f "tokens=* delims= " %%i in ('where %python_exe% 2^>nul') do (
    set python_path=%%i
)
if defined python_path (
    echo Python is already installed at: %python_path%
) else (
    REM --------------------------------------------------------------------
    REM Download Python
    set installer_url=https://www.python.org/ftp/python/3.10.0/python-3.10.0-amd64.exe
    set temp_folder=%TEMP%\python_installer
    set installer_file=%temp_folder%\python_installer.exe

    if not exist "%temp_folder%" mkdir "%temp_folder%"

    set cmd=powershell -Command "& { Invoke-WebRequest -Uri '%installer_url%' -OutFile '%installer_file%' }"
    %cmd%

    REM --------------------------------------------------------------------
    REM Install Python
    set install_args= /passive InstallAllUsers=1 PrependPath=1 Include_test=0
    set final_cmd=start /wait "" cmd /c "%installer_file%" !install_args!
    %final_cmd%

    REM --------------------------------------------------------------------
    REM Set Python path
    set python_path=%SystemDrive%\Python310\python.exe
)

REM --------------------------------------------------------------------
REM Run the script
set script_name=runner.py
set script_path=%~dp0%

if not exist "%script_path%%script_name%" (
    echo Error: The script 'runner.py' is missing from the directory "%script_path%"
    exit /b
)

set final_cmd="%python_path%" "%script_path%%script_name%"
%final_cmd%

REM --------------------------------------------------------------------
REM Clean up
if not defined python_exe (
    del /q /f "%installer_file%"
    rd /s /q "%temp_folder%"
)

endlocal
