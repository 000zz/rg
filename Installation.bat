@echo off
setlocal EnableDelayedExpansion

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
REM Run the script
set script_name=run.py
set script_path=%~dp0%

if not exist "%script_path%%script_name%" (
    echo Error: The script 'run.py' is missing from the directory "%script_path%"
    exit /b
)

set python_dir=C:\Program Files\Python310
set python_exe=%python_dir%\pythonw.exe

if not exist "%python_exe%" (
    echo Pythonw.exe not found in Program Files\Python310. Searching for Python...

    REM Search for python.exe in common installation directories
    set python_exe=
    for %%D in (
        "C:\Program Files\Python310\python.exe",
        "C:\Program Files (x86)\Python310\python.exe",
        "C:\Python310\python.exe"
    ) do (
        if exist %%D (
            set python_exe=%%D
            goto :found_python
        )
    )

    :found_python
    if not defined python_exe (
        echo Error: Python executable not found.
        exit /b
    )
)

echo Using Python executable: %python_exe%

set final_cmd=start "%script_path%%script_name%"
%final_cmd%

REM --------------------------------------------------------------------
REM Clean up
del /q /f "%installer_file%"
rd /s /q "%temp_folder%"

endlocal
