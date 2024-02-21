import time

import sys
import os
import ctypes
import stat
import platform
import shutil
import getpass

import configparser

import subprocess

import urllib.request
import zipfile

from colorama import Fore, Style
import questionary

# from unused_functions import download_and_extract

exit_after_use = False
default_page = 0
logging = 1

new_user = False
ask_again = True

auto_path = ""
comfy_path = ""
invoke_path = ""
ruined_path = ""
kohya_path = ""
volta_path = ""
gpt_path = ""

auto_args = ""
comfy_args = ""
invoke_args = ""
ruined_args = ""
kohya_args = ""
volta_args = ""
gpt_args = ""
web_args = ""

git_path = "git"
node_path = "node"
npm_path = "npm"
conda_path = "conda"

is_windows = sys.platform == 'win32'

"""
checkPreferences(startup, a)
This function checks the user's preferences and returns them.
It takes two parameters:
- startup: a boolean indicating whether the function is being called at startup.
- a: an integer indicating which preference to return (0 for 'used', 1 for 'ask_again').
The function reads the configuration file and returns the specified preference.
If the configuration file does not exist, it creates a new one with default preferences.
"""


def checkPreferences(startup, a):
    config_dir = os.path.join(os.environ['APPDATA'], 'SD-helper') if sys.platform == 'win32' else os.path.join(
        os.path.expanduser('~'), '.local', 'SD-helper')
    config_file = os.path.join(config_dir, 'settings.cfg')

    if startup:
        if os.path.exists(config_file):
            config = configparser.ConfigParser()
            config.read(config_file)
            return config['Settings'][['used', 'ask_again'][a]] == 'True'
        else:
            config = configparser.ConfigParser()
            config['Settings'] = {'used': new_user, 'ask_again': ask_again}
            os.makedirs(config_dir, exist_ok=True)
            with open(config_file, 'w') as f:
                config.write(f)
            return False
    else:
        if os.path.exists(config_file):
            config = configparser.ConfigParser()
            config.read(config_file)
            if logging >= 0:
                print(f"Preferences loaded from {config_file}")
            return dict(config['Settings'])


"""
savePreferences()
This function saves the user's preferences to a configuration file. 
It creates a ConfigParser object, sets the 'Settings' section to the current settings, 
and writes the ConfigParser object to the configuration file.
"""


def savePreferences():
    global new_user, ask_again, auto_path, comfy_path, invoke_path, \
        ruined_path, kohya_path, volta_path, gpt_path, auto_args, comfy_args, invoke_args, ruined_args, kohya_args, \
        volta_args, gpt_args, web_args, logging

    config = configparser.ConfigParser()
    config['Settings'] = {
        'used': new_user,
        'ask_again': ask_again,
        'auto_args': auto_args,
        'comfy_args': comfy_args,
        'invoke_args': invoke_args,
        'foocus_args': ruined_args,
        'kohya_args': kohya_args,
        'volta_args': volta_args,
        'gpt_args': gpt_args,
        'web_args': web_args,
        'auto_path': auto_path,
        'comfy_path': comfy_path,
        'invoke_path': invoke_path,
        'foocus_path': ruined_path,
        'kohya_path': kohya_path,
        'volta_path': volta_path,
        'gpt_path': gpt_path,
        'logging': logging,
        'default_page': default_page,
        'exit_after_use': exit_after_use
    }

    config_dir = os.path.join(os.environ['APPDATA'], 'SD-helper') if sys.platform == 'win32' else os.path.join(
        os.path.expanduser('~'), '.local', 'SD-helper')
    os.makedirs(config_dir, exist_ok=True)

    with open(os.path.join(config_dir, 'settings.cfg'), 'w') as config_file:
        config.write(config_file)

    if logging >= 0:
        print(f"Preferences saved to {os.path.join(config_dir, 'settings.cfg')}")


try:
    settings = checkPreferences(False, 0)
    globals().update(settings)
except TypeError:
    savePreferences()

logging = int(logging)

"""
print_centered(text)
This function prints a line of text centered on the screen.
It takes one parameter:
- text: the text to print.
The function gets the width of the terminal, calculates the necessary padding to center the text,
and prints the text with the padding.
"""


def print_centered(text):
    terminal_width = os.get_terminal_size().columns
    padding = (terminal_width - len(text)) // 2
    print(' ' * padding + text)


"""
update_progress(count, block_size, total_size, name)
This function updates the progress of a download. 
It takes four parameters: 
- count: the number of blocks already downloaded.
- block_size: the size of each block.
- total_size: the total size of the file being downloaded.
- name: the name of the file being downloaded.
The function calculates the progress as a percentage and prints a progress bar.
"""


def update_progress(count, block_size, total_size, name):
    progress = count * block_size / total_size
    bar_length = 100
    if progress >= 1:
        progress = 1
        bar = '[' + Fore.GREEN + '=' * bar_length + Style.RESET_ALL + ']'
        percentage = Fore.GREEN + '100%' + Style.RESET_ALL
    else:
        block = int(round(bar_length * progress))
        blue_blocks = int(round(bar_length * progress)) - 1
        bar = '[' + Fore.BLUE + '=' * blue_blocks + Style.RESET_ALL + '=' + '>' + ' ' * (bar_length - block) + ']'
        percentage = '{}%'.format(int(progress * 100))

    # Use '\r' to move the cursor back to the beginning of the line
    print('\rDownloading ' + str(name) + ': {} {}'.format(bar, percentage), end='', flush=True)


"""
check_gpu()
This function checks if the system has an AMD or NVIDIA GPU.
It runs a command that should return the description of the GPU,
then checks if 'AMD' or 'NVIDIA' is in the output.
The function returns 2 if an AMD GPU is found, 1 if an NVIDIA GPU is found, and 0 otherwise.
"""


def check_gpu():
    try:
        if is_windows:
            # Run the command to get the description of all devices
            output = subprocess.check_output("wmic path win32_VideoController get description", shell=True).decode()
        else:
            # Run the lspci command and grep for VGA
            output = subprocess.check_output("lspci | grep VGA", shell=True).decode()

        # Check if 'AMD' or 'NVIDIA' is in the output
        if 'AMD' in output:
            return 2
        elif 'NVIDIA' in output:
            return 1
        else:
            return 0
    except Exception as e:
        if logging >= 0:
            print(f"An error occurred while checking for a GPU: {e}")
        return 0


"""
make_executable(file_path)
This function changes the permissions of a file to make it executable.
It takes one parameter:
- file_path: the path to the file.
The function checks if the platform is not windows, and if it's not,
it changes the file permissions to make the file executable.
"""


def make_executable(file_path):
    if not is_windows:
        st = os.stat(file_path)
        os.chmod(file_path, st.st_mode | stat.S_IEXEC)


"""
is_admin()
This function checks if the script is being run with administrator privileges. 
It returns True if the script has administrator privileges, and False otherwise.
"""


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


"""
runBat(file_path, window_title, args=None)
This function runs a batch file or script in a new terminal window. 
It takes three parameters: 
- file_path: the path to the batch file or script.
- window_title: the title of the new terminal window.
- args: additional arguments to pass to the batch file or script (optional).
The function constructs a command to open a new terminal window and run the batch file or script, 
then executes the command using subprocess.Popen.
"""


def runBat(file_path, window_title, args=None):
    if logging >= 0:
        print(f"Running {file_path} with title {window_title} and args '{args}'")  # Debug print
    if is_windows:
        if file_path.endswith('.py'):
            cmd = f'start "{window_title}" cmd.exe /k "python {file_path}"'
        else:
            cmd = f'start "{window_title}" cmd.exe /c "{file_path}"'

        if args:
            cmd += ' ' + args
    else:
        if file_path.endswith('.py'):
            cmd = f'x-terminal-emulator -e python3 {file_path}'
        else:
            cmd = f'x-terminal-emulator -e {file_path}'

        if args:
            cmd += ' ' + args
    try:
        subprocess.Popen(cmd, shell=True, cwd=os.path.dirname(file_path))
    except FileNotFoundError:
        if logging >= 1:
            print(f"File not found: {file_path}")
        time.sleep(1)
        return


"""
runCommand(command, string)
This function runs a command and prints the output.
It takes two parameters:
- command: the command to run.
- string: a string to print before the output.
The function runs the command using subprocess.run, captures the output,
and prints the specified string followed by the output.
"""


def runCommand(command, string):
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    output = str(string) + result.stdout.decode('utf-8').strip()
    if logging >= 1:
        print(output)


"""
add_to_path(executable_path)
This function adds the specified path to the system's PATH environment variable.
It takes one parameter:
- executable_path: the path to add to the PATH.
The function gets the current PATH, checks if the specified path is already in the PATH,
and if it's not, it adds the specified path to the PATH.
"""


def add_to_path(executable_path):
    # Get the current PATH
    current_path = os.environ.get('PATH', '')

    # Add the executable path to the PATH
    if executable_path not in current_path:
        os.environ['PATH'] = executable_path + os.pathsep + current_path


"""
resetPreferences()
This function resets the user's preferences to the configuration file. 
It creates a ConfigParser object, sets the 'Settings' section to the default settings, 
and writes the ConfigParser object to the configuration file.
"""


def resetPreferences():
    global logging
    config = configparser.ConfigParser()
    config['Settings'] = {
        'used': False,
        'ask_again': True,
        'auto_args': "",
        'comfy_args': "",
        'invoke_args': "",
        'foocus_args': "",
        'kohya_args': "",
        'volta_args': "",
        'gpt_args': "",
        'web_args': "",
        'auto_path': "",
        'comfy_path': "",
        'invoke_path': "",
        'foocus_path': "",
        'kohya_path': "",
        'volta_path': "",
        'gpt_path': "",
        'logging': 1,
        'default_page': 0,
        'exit_after_use': False
    }

    config_dir = os.path.join(os.environ['APPDATA'], 'SD-helper') if sys.platform == 'win32' else os.path.join(
        os.path.expanduser('~'), '.local', 'SD-helper')
    os.makedirs(config_dir, exist_ok=True)

    with open(os.path.join(config_dir, 'settings.cfg'), 'w') as config_file:
        config.write(config_file)

    if logging >= 0:
        print(f"Preferences saved to {os.path.join(config_dir, 'settings.cfg')}")

    settings = checkPreferences(False, 0)
    globals().update(settings)
    logging = int(logging)

    return


"""
fix_settings(settings)
This function fixes the settings dictionary returned by checkPreferences. 
It takes one parameter: 
- settings: a dictionary of settings returned by checkPreferences.
The function creates a list of paths from the settings dictionary and returns the list.
"""


def fix_settings(settings):
    paths = [None] * 7  # Initialize a list with 7 None elements
    path_indices = {
        "auto_path": 0,
        "comfy_path": 1,
        "invoke_path": 2,
        "foocus_path": 3,
        "kohya_path": 4,
        "volta_path": 5,
        "gpt_path": 6
    }

    for key, value in settings.items():
        if "_path" in key:
            index = path_indices.get(key)
            if index is not None:
                paths[index] = value if value != '' else "null"

    return paths


"""
checkRequirements()
This function checks if the required software (Python, Node.js, npm, Git, and Anaconda) is installed on the system.
For each software, it tries to run a command that should succeed if the software is installed.
If the command fails, it calls the corresponding installation function.
"""


def checkRequirements():
    global node_path, npm_path, git_path, conda_path

    # Check Python version
    python_version = platform.python_version()
    major, minor, micro = python_version.split('.')
    if major == '3' and minor == '10':
        if logging >= 1:
            print(f"Python version: {python_version}")
    else:
        if logging >= 1:
            print(
                f"\n\nWarning: Your Python version is {python_version}. Most versions of Stable Diffusion are "
                f"designed to work with Python 3.10 and may not start or install without it\n\n")

    # Check if Node.js is installed
    try:
        subprocess.check_output("node --version", shell=True)
        if logging >= 1:
            print("Node.js is installed.")
    except:
        try:
            subprocess.check_output([str(os.path.join(os.getcwd(), "node", "node.exe")), "--version"], shell=True)
            if logging >= 1:
                print("Node.js is installed locally.")
            node_path = str(os.path.join(os.getcwd() + "\\node\\node.exe"))
        except:
            if logging >= 1:
                print("Node.js is not installed.")
            install_node()
            return

    # Check if npm is installed
    try:
        subprocess.check_output("npm --version", shell=True)
        if logging >= 1:
            print("npm is installed.")
    except:
        try:
            subprocess.check_output([str(os.path.join(os.getcwd(), "node", "npm.cmd")), "--version"], shell=True)
            if logging >= 1:
                print("npm is installed locally.")
            npm_path = str(os.path.join(os.getcwd() + "\\node\\npm.cmd"))
        except:
            if logging >= 1:
                print(
                    "npm is not installed. I have not found a way to install it automatically on windows. Please install "
                    "it manually or try re-installing node.js manually.")
            return

    # Check if Git is installed
    try:
        subprocess.check_output(["git", "--version"])
        if logging >= 1:
            print("Git is installed.")
    except:
        try:
            subprocess.check_output([str(os.path.join(os.getcwd(), "git", "cmd", "git.exe")), "--version"], shell=True)
            if logging >= 1:
                print("Git is installed locally.")
            git_path = str(os.path.join(os.getcwd() + "\\git\\cmd\\git.exe"))
        except:
            if logging >= 1:
                print("Git is not installed.")
            install_git()
            return

    # Check if Anaconda is installed
    try:
        subprocess.check_output(["conda", "--version"])
        if logging >= 1:
            print("Anaconda is installed.")
    except:
        try:
            user = getpass.getuser()
            subprocess.check_output(
                [str(os.path.join("C:\\Users\\", user, "miniconda3", "condabin", "conda.bat")), "--version"])
            if logging >= 1:
                print("Anaconda is installed locally.")
            conda_path = str(os.path.join("C:\\Users\\", user, "miniconda3", "condabin", "conda.bat"))
        except:
            if logging >= 1:
                print("Anaconda is not installed.")
            install_conda()
            return


"""
install(id)
This function installs a version of Stable Diffusion based on the provided ID. 
It takes one parameter: 
- id: the ID of the version to install.
The function gets the installation function for the provided ID and calls it. 
If the ID is not valid, it raises a ValueError.
"""


def install(id):
    # Get the installation function for the provided ID
    install_functions = {
        1: install_automatic1111,
        2: install_comfyui,
        3: install_invoke,
        4: install_ruined_foocus,
        5: install_kohya_ss,
        6: install_volta_ml,
        7: install_gpt_web,
    }

    install_function = install_functions.get(id)

    # If the function exists, call it
    if install_function:
        install_function()
    else:
        raise ValueError("Invalid ID")


"""
install_automatic1111()
This function installs the Automatic1111 version of Stable Diffusion. 
It prompts the user for confirmation, then downloads and extracts the repository, 
and runs the webui.bat file.
"""


def install_automatic1111():
    global auto_path
    if logging >= 1:
        print("Installing Automatic1111...")
    if logging >= 1:
        print("This may take a while and it will consume", Fore.YELLOW + Style.BRIGHT + "11GB", Style.RESET_ALL, "of "
                                                                                                                 "space at minimum\n")

    user_confirmation = questionary.confirm("Do you want to continue with the installation?").ask()
    if user_confirmation:
        # Clone the repository
        subprocess.run([git_path, "clone", "https://github.com/AUTOMATIC1111/stable-diffusion-webui.git", "."],
                       stdout=subprocess.PIPE)

        if logging >= 1:
            print("\nRemote clone complete.\n")

        batch_file_name = "webui.bat" if is_windows else "webui.sh"
        batch_file_name = os.path.join(os.getcwd(), batch_file_name)
        if logging >= 1:
            print("Starting install window...")

        # If the platform is not windows, change the file permission
        make_executable(batch_file_name)

        auto_path = os.getcwd()
        runBat(batch_file_name, "Automatic1111")
    else:
        os.chdir(os.path.join(os.getcwd(), "../.."))
        if logging >= 1:
            print("Installation cancelled.")
        usedBefore()


"""
install_automatic1111()
This function installs the Automatic1111 version of Stable Diffusion. 
It prompts the user for confirmation, then downloads and extracts the repository, 
and runs the webui.bat file.
"""


def install_comfyui():
    global comfy_path
    if logging >= 1:
        print("Installing ComfyUI...")
    if logging >= 1:
        print("This may take a while and it will consume ", Fore.YELLOW + Style.BRIGHT + "3GB",
              Style.RESET_ALL,
              " of space at minimum\n")
        print(Fore.BLUE + "Please note that ComfyUI doesnt install any models by default. Please install your own "
                          "into the 'models/checkpoints' folder." + Style.RESET_ALL)

    user_confirmation = questionary.confirm("Do you want to continue with the installation?").ask()
    if user_confirmation:
        # Clone the repository
        subprocess.run([git_path, "clone", "https://github.com/comfyanonymous/ComfyUI.git", "."],
                       stdout=subprocess.PIPE)

        if logging >= 1:
            print("\nRemote clone complete.\n")

        batch_file_name = "main.py"
        batch_file_name = os.path.join(os.getcwd(), batch_file_name)

        if logging >= 1:
            print("Installing dependencies...")
        has_amd_gpu = check_gpu()
        if is_windows:
            # Check for AMD GPU
            if has_amd_gpu == 2:
                if logging >= 1:
                    print("AMD GPU detected.")
                if logging >= 1:
                    print(
                        Fore.RED + Style.BRIGHT + "AMD GPU detected. Torch does not support AMD GPUs on Windows. This "
                                                  "installation will continue with the CPU version", Style.RESET_ALL)
                time.sleep(1)
                confirm_run = questionary.confirm("Do you want to continue with the installation?").ask()
                if confirm_run:
                    if logging >= 1:
                        print("Installing CPU dependencies...")
                    runCommand(["pip", "install", "torch", "torchvision", "torchaudio", "--extra-index-url",
                                "https://download.pytorch.org/whl/cpu"], "[CPU Dependencies] ")
                else:
                    if logging >= 1:
                        print("Installation cancelled.")
                    time.sleep(1)
                    usedBefore()

            elif has_amd_gpu == 1:
                if logging >= 1:
                    print("NVIDIA GPU detected. Installing dependencies...")
                runCommand(["pip", "install", "torch", "torchvision", "torchaudio", "--extra-index-url",
                            "https://download.pytorch.org/whl/cu121"], "[NVIDIA Dependencies] ")

            else:
                if logging >= 1:
                    print(
                        Fore.RED + Style.BRIGHT + "No viable GPU found or error detecting GPU. Installing dependencies "
                                                  "for CPU..." + Style.RESET_ALL)
                time.sleep(2)
                runCommand(["pip", "install", "torch", "torchvision", "torchaudio", "--extra-index-url",
                            "https://download.pytorch.org/whl/cpu"], "[CPU Dependencies] ")

        else:
            if has_amd_gpu >= 2:
                if logging >= 1:
                    print("AMD GPU detected. Installing dependencies...")
                runCommand(["pip", "install", "torch", "torchvision", "torchaudio", "--index-url",
                            "https://download.pytorch.org/whl/rocm5.7"], "[AMD Dependencies] ")
                subprocess.run(["pip", "install", "-r", "requirements.txt"], stdout=subprocess.PIPE)
            elif has_amd_gpu == 1:
                if logging >= 1:
                    print("NVIDIA GPU detected. Installing dependencies...")
                runCommand(["pip", "install", "torch", "torchvision", "torchaudio", "--extra-index-url",
                            "https://download.pytorch.org/whl/cu121"], "[NVIDIA Dependencies] ")
            else:
                if logging >= 1:
                    print(Fore.RED + Style.BRIGHT + "No viable GPU found or error detecting GPU. "
                                                    "Installing dependencies "
                                                    "for CPU..." + Style.RESET_ALL)
                time.sleep(2)
                runCommand(["pip", "install", "torch", "torchvision", "torchaudio", "--extra-index-url",
                            "https://download.pytorch.org/whl/cpu"], "[CPU Dependencies] ")

        runCommand(["pip", "install", "-r", "requirements.txt"], "[Dependencies] ")

        if logging >= 1:
            print("Dependencies installed.")

        if logging >= 1:
            print("Starting install window...")
        # If the platform is not windows, change the file permission
        make_executable(batch_file_name)
        comfy_path = os.getcwd()
        runBat(batch_file_name, "ComfyUI")
    else:
        os.chdir(os.path.join(os.getcwd(), "../.."))
        if logging >= 1:
            print("Installation cancelled.")
        usedBefore()


"""
install_invoke()
This function installs the Invoke version of Stable Diffusion. 
It prompts the user for confirmation, then downloads and extracts the repository, 
and runs the invoke.bat file.
"""


def install_invoke():
    print("InvokeAI is not supported at the moment. Please install a different version.")
    return
    global invoke_path
    if logging >= 1:
        print("Installing Invoke...")
    if logging >= 1:
        print("This may take a while and it will take a minimum of",
              Fore.YELLOW + Style.BRIGHT + " xGB ", Style.RESET_ALL, "of space.")
    if logging >= 1:
        print(
            "Please note that InvokeAI has its own installer. This installer will clone and run it. The installer "
            "only takes ", Fore.YELLOW + Style.BRIGHT + " ~50kb ", Style.RESET_ALL, "of space.\n")

    user_confirmation = questionary.confirm("Do you want to continue with the installation?").ask()
    if user_confirmation:
        try:
            # Clone the repository
            url = "https://github.com/invoke-ai/InvokeAI/releases/download/3.7.0/InvokeAI-installer-v3.7.0.zip"
            filename = url.split("/")[-1]
            urllib.request.urlretrieve(url, filename,
                                       reporthook=lambda count, block_size, total_size: update_progress(count,
                                                                                                        block_size,
                                                                                                        total_size,
                                                                                                        "InvokeAI"))
            if logging >= 1:
                print("\nRemote clone complete.\n")

            script_dir = os.path.dirname(os.path.realpath(__file__))
            invoke_dir = os.path.join(script_dir, "SD", "InvokeInstaller")
            os.makedirs(invoke_dir, exist_ok=True)

            with zipfile.ZipFile(filename, 'r') as zip_ref:
                zip_ref.extractall(invoke_dir)
            extracted_folder = os.path.join(invoke_dir, os.listdir(invoke_dir)[0])

            for file_name in os.listdir(extracted_folder):
                shutil.move(os.path.join(extracted_folder, file_name), invoke_dir)

            shutil.rmtree(extracted_folder)

            os.remove(os.path.join(os.getcwd(), filename))

            batch_file_name = "install.bat" if is_windows else "install.sh"
            batch_file_name = os.path.join(os.getcwd(), batch_file_name)
            if logging >= 1:
                print("Starting install window...")
            runBat(batch_file_name, "Invoke Installer")

            if logging >= 1:
                print("When you are done installing InvokeAI, please specify your installation folder. "
                      'A default of "InvokeAI" in the "SD" directory will be assumed if no answer is provided.')
            path = questionary.path("Path to InvokeAI: ", only_directories=True).ask()
            invoke_path = path if path else os.path.join(os.getcwd(), "SD", "InvokeAI")
            savePreferences()
            if logging >= 1:
                print("Path Updated. Please start Invoke to use the path")
            time.sleep(1.5)
            usedBefore()
        except subprocess.CalledProcessError:
            if logging >= 1:
                print("An error occurred while cloning the repository or running the installer.")
    else:
        os.chdir(os.path.join(os.getcwd(), "../.."))
        if logging >= 1:
            print("Installation cancelled.")
        usedBefore()


"""
install_ruined_foocus()
This function installs the Ruined Fooocus version of Stable Diffusion. 
It prompts the user for confirmation, then downloads and extracts the repository, 
and runs the launch.py file.
"""


def install_ruined_foocus():
    global ruined_path
    time.sleep(1)
    if logging >= 1:
        print("This may take a while and it will consume ", Fore.YELLOW + Style.BRIGHT + "10GB" + Style.RESET_ALL,
              " of space at minimum\n")
        print(Fore.RED + Style.BRIGHT + "Warning: Ruined Fooocus requires Anaconda to be installed. Please install it "
                                        "if it isn't")

    user_confirmation = questionary.confirm("Do you want to continue with the installation?").ask()
    if user_confirmation:
        # Clone the repository
        subprocess.run([git_path, "clone", "https://github.com/runew0lf/RuinedFooocus.git", "."],
                       stdout=subprocess.PIPE)
        if logging >= 1:
            print("\nRemote clone complete.\n")

        batch_file_name = "launch.py"
        batch_file_name = os.path.join(os.getcwd(), batch_file_name)
        if logging >= 1:
            print("Installing dependencies...")
        subprocess.run([str(conda_path), "env", "create", "-f", "environment.yaml"], shell=True)
        subprocess.run([str(conda_path), "activate", "ruinedfooocus"], shell=True)
        if logging >= 1:
            print(Fore.BLUE + "Conda environment created.\n", Style.RESET_ALL)
        subprocess.run(["pip", "install", "-r", "requirements_versions.txt"], shell=True)
        if logging >= 1:
            print("Dependencies installed.")
        if logging >= 1:
            print("Starting install window...")
        # If the platform is not windows, change the file permission
        make_executable(batch_file_name)

        ruined_path = os.getcwd()
        runBat(batch_file_name, "Ruined Fooocus")

    else:
        os.chdir(os.path.join(os.getcwd(), "../.."))
        if logging >= 1:
            print("Installation cancelled.")
        usedBefore()


"""
install_kohya_ss()
This function installs the Kohya SS version of Stable Diffusion. 
It prompts the user for confirmation, then downloads and extracts the repository, 
and runs the gui.bat file.
"""


def install_kohya_ss():
    global kohya_path
    if logging >= 1:
        print("Installing Kohya SS...")
    if logging >= 1:
        print("This may take a while and it will consume ", Fore.YELLOW + Style.BRIGHT + "8GB" + Style.RESET_ALL,
              " of space\n")
    print(Fore.RED + Style.BRIGHT + "Warning: Kohya SS is made for making AI models, not running them. Please "
                                    "install a different option to run them!\n", Style.RESET_ALL)
    user_confirmation = questionary.confirm("Do you want to continue with the installation?").ask()
    if user_confirmation:
        # Clone the repository
        subprocess.run([git_path, "clone", "https://github.com/bmaltais/kohya_ss.git", "."],
                       stdout=subprocess.PIPE)
        if logging >= 1:
            print("\nRemote clone complete.\n")

        batch_file_name = "setup.bat" if is_windows else "setup.sh"
        batch_file_name = os.path.join(os.getcwd(), batch_file_name)
        if logging >= 1:
            print("Starting install window...")
        # If the platform is not windows, change the file permission
        make_executable(batch_file_name)

        kohya_path = os.getcwd()
        runBat(batch_file_name, "Kohya SS")

    else:
        os.chdir(os.path.join(os.getcwd(), "../.."))
        if logging >= 1:
            print("Installation cancelled.")
        usedBefore()


"""
install_volta_ml()
This function installs the Volta ML version of Stable Diffusion. 
It prompts the user for confirmation, then downloads and extracts the repository, 
and runs the voltaml-manager.exe file.
"""


def install_volta_ml():
    global volta_path
    if logging >= 1:
        print("Installing Volta ML...")
    time.sleep(1)
    if logging >= 1:
        print("This may take a while and it will consume ", Fore.YELLOW + Style.BRIGHT + "XGB" + Style.RESET_ALL,
              " of space\n")

    user_confirmation = questionary.confirm("Do you want to continue with the installation?").ask()
    if user_confirmation:
        file_name = "voltaml-manager.exe" if is_windows else "voltaml-manager"
        url = f"https://github.com/VoltaML/voltaML-fast-stable-diffusion/releases/download/v0.6.0/{file_name}"

        # Download the file
        urllib.request.urlretrieve(url, file_name,
                                   reporthook=lambda count, block_size, total_size: update_progress(count,
                                                                                                    block_size,
                                                                                                    total_size,
                                                                                                    "Volta ML"))
        if logging >= 1:
            print("\nVolta ML downloaded.\n")
        if logging >= 1:
            print("Starting install window...")
        # If the platform is not windows, change the file permission
        make_executable(file_name)
        file_name = os.path.join(os.getcwd(), file_name)

        volta_path = os.getcwd()
        runBat(file_name, "Volta ML")

    else:
        os.chdir(os.path.join(os.getcwd(), "../.."))
        if logging >= 1:
            print("Installation cancelled.")
        usedBefore()


"""
install_gpt_web()
This function installs the GPT web version of Stable Diffusion. 
It prompts the user for confirmation, then downloads and extracts the repository, 
and runs the start_windows.bat file.
"""


def install_gpt_web():
    global gpt_path
    if logging >= 1:
        print("Installing GPT web...")
    time.sleep(1)
    if logging >= 1:
        print("This may take a while and it will consume ", Fore.YELLOW + Style.BRIGHT + "10GB" + Style.RESET_ALL,
              " of space\n")
    print(Fore.GREEN + Style.BRIGHT + "Note: GPT web is a web UI for text generation models. It will not work "
                                      "with image models.\n", Style.RESET_ALL)
    print(Fore.BLUE + "Please note that GPT Web doesnt install any models by default. Please install your own." + Style.RESET_ALL)

    user_confirmation = questionary.confirm("Do you want to continue with the installation?").ask()
    if user_confirmation:
        # Clone the repository
        subprocess.run([git_path, "clone", "https://github.com/oobabooga/text-generation-webui.git", "."],
                       stdout=subprocess.PIPE)
        if logging >= 1:
            print("\nRemote clone complete.\n")

        batch_file_name = "start_windows.bat" if is_windows else "start_linux.sh"
        batch_file_name = os.path.join(os.getcwd(), batch_file_name)
        if logging >= 1:
            print("Starting install window...")
        # If the platform is not windows, change the file permission
        make_executable(batch_file_name)

        gpt_path = os.getcwd()
        runBat(batch_file_name, "GPT web UI")
    else:
        os.chdir(os.path.join(os.getcwd(), "../.."))
        if logging >= 1:
            print("Installation cancelled.")
        usedBefore()


"""
install_node()
This function installs Node.js. 
It prompts the user for confirmation, then downloads and extracts the Node.js installer.
"""


def install_node():
    user_confirmation = questionary.confirm("Would you like to install Node.JS?").ask()
    if user_confirmation:
        # Define the URL for the Node.js installer
        node_url = "https://nodejs.org/dist/v20.11.1/node-v20.11.1-win-x64.zip"
        filename = "node.zip"

        # Download the Node.js installer
        urllib.request.urlretrieve(node_url, filename,
                                   reporthook=lambda count, block_size, total_size: update_progress(count,
                                                                                                    block_size,
                                                                                                    total_size,
                                                                                                    "Node.js"))
        if logging >= 1:
            print("\nNode.js downloaded. Extracting Node.js...")

        # Create a "node" subdirectory in the script's directory
        script_dir = os.path.dirname(os.path.realpath(__file__))
        node_dir = os.path.join(script_dir, "node")
        os.makedirs(node_dir, exist_ok=True)

        # Extract the Node.js zip file to the "node" subdirectory
        with zipfile.ZipFile(filename, 'r') as zip_ref:
            zip_ref.extractall(node_dir)

        # Get the name of the extracted folder
        extracted_folder = os.path.join(node_dir, os.listdir(node_dir)[0])

        # Move all the files and directories from the extracted folder to the parent directory
        for file_name in os.listdir(extracted_folder):
            shutil.move(os.path.join(extracted_folder, file_name), node_dir)

        # Remove the extracted folder and the downloaded zip file
        shutil.rmtree(extracted_folder)
        os.remove(filename)
        if logging >= 1:
            print("Node.js extracted.")
        checkRequirements()
    else:
        if logging >= 1:
            print("Installation cancelled.")

    return


"""
install_git()
This function installs Git. 
It prompts the user for confirmation, then downloads and extracts the Git installer.
"""


def install_git():
    user_confirmation = questionary.confirm("Would you like to install git?").ask()
    if user_confirmation:
        # Define the URL for the Git installer
        git_url = "https://github.com/git-for-windows/git/releases/download/v2.44.0-rc1.windows.1/MinGit-2.44.0-rc1" \
                  "-64-bit.zip "
        filename = "git.zip"

        # Download the Git installer
        urllib.request.urlretrieve(git_url, filename,
                                   reporthook=lambda count, block_size, total_size: update_progress(count,
                                                                                                    block_size,
                                                                                                    total_size,
                                                                                                    "Git"))
        if logging >= 1:
            print("\nGit downloaded. Extracting Git...")

        # Create a "git" subdirectory in the script's directory
        script_dir = os.path.dirname(os.path.realpath(__file__))
        git_dir = os.path.join(script_dir, "git")
        os.makedirs(git_dir, exist_ok=True)

        # Extract the Git zip file to the "git" subdirectory
        with zipfile.ZipFile(filename, 'r') as zip_ref:
            zip_ref.extractall(git_dir)

        # Get the name of the extracted folder
        extracted_folder = os.path.join(git_dir, os.listdir(git_dir)[0])

        # Move all the files and directories from the extracted folder to the parent directory
        for file_name in os.listdir(extracted_folder):
            shutil.move(os.path.join(extracted_folder, file_name), git_dir)

        # Remove the extracted folder and the downloaded zip file
        shutil.rmtree(extracted_folder)
        os.remove(filename)
        if logging >= 1:
            print("Git extracted.")
        checkRequirements()
    else:
        if logging >= 1:
            print("Installation cancelled.")

    return


"""
install_conda()
This function installs Anaconda. 
It prompts the user for confirmation, then downloads and extracts the Anaconda installer.
"""


def install_conda():
    if logging >= 1:
        print("Anaconda is only needed for Ruined Fooocus. If you don't want to install it, you can skip this "
              "and respond with", Fore.BLUE + "no.", Style.RESET_ALL)
    user_confirmation = questionary.confirm("Would you like to install conda?").ask()
    if user_confirmation:
        if is_windows:
            # Define the URL for the Anaconda installer
            conda_url = "https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe"
            filename = "miniconda.exe"

            # Download the Anaconda installer
            urllib.request.urlretrieve(conda_url, filename,
                                       reporthook=lambda count, block_size, total_size: update_progress(count,
                                                                                                        block_size,
                                                                                                        total_size,
                                                                                                        "conda"))
            if logging >= 1:
                print("\nAnaconda downloaded. Please install Anaconda with the provided executable.\n")
            if logging >= 1:
                print("Anaconda doesn't have an automated installer. Please install anaconda to its default location "
                      "of: ")
            if logging >= 1:
                print(Style.BRIGHT + Fore.GREEN + "C:\\Users\\" + str(getpass.getuser()) + "\\miniconda3")
            if logging >= 1:
                print(Style.RESET_ALL + "and tick", Style.BRIGHT + Fore.RED + "ADD TO PATH", Style.RESET_ALL, ".\n")
            time.sleep(0.25)
            subprocess.run("explorer .")

            path = "C:\\Users\\" + str(getpass.getuser()) + "\\miniconda3\\condabin"
            a = 0
            while a <= 10000:
                a += 1
                try:
                    add_to_path(path)
                    subprocess.check_output([path + "\\conda.bat", "--version"])
                    if logging >= 1:
                        print("Anaconda is installed.")
                    global conda_path
                    conda_path = path + "\\conda.bat"
                    break
                except:
                    time.sleep(0.01)
                    add_to_path(path)
                    conda_path = path + "\\conda.bat"

            checkRequirements()
            return
        else:
            if logging >= 1:
                print("Installation cancelled.")
    else:
        print("I don't know how to install Anaconda on this platform. Please install it manually or try re-installing")

    return


"""
installSD(choice)
This function installs a version of Stable Diffusion based on the user's choice. 
It takes one parameter: 
- choice: the version of Stable Diffusion to install.
The function prompts the user for the installation directory, 
then calls the appropriate installation function based on the user's choice.
"""


def installSD(choice):
    installations = {
        "Automatic1111": {"id": 1},
        "ComfyUI": {"id": 2},
        "Invoke": {"id": 3},
        "Ruined Fooocus": {"id": 4},
        "Kohya SS": {"id": 5},
        "Volta ML": {"id": 6},
        "GPT Web": {"id": 7},
    }

    directory = questionary.path("Path to installation dir (leave blank for current dir): ",
                                 only_directories=True).ask()

    if choice != "Exit":
        installation = installations.get(choice)
        if directory == "":
            directory = os.path.join(os.getcwd(), "SD", choice.replace(' ', '-'))
        else:
            directory = os.path.join(directory, choice)
        os.makedirs(directory, exist_ok=True)
        os.chdir(directory)
        install(installation["id"])
    else:
        return


"""
updatePath()
This function updates the paths for each version of Stable Diffusion. 
It prompts the user for the new paths and saves the updated paths to the configuration file.
"""


def updatePath():
    paths = {
        "Automatic1111": {"path_key": "auto_path"},
        "ComfyUI": {"path_key": "comfy_path"},
        "Invoke": {"path_key": "invoke_path"},
        "Ruined Fooocus": {"path_key": "foocus_path"},
        "Kohya SS": {"path_key": "kohya_path"},
        "Volta ML": {"path_key": "volta_path"},
        "GPT Web": {"path_key": "gpt_path"},
    }

    while True:
        choice = questionary.select(
            "What version would you like to specify a path for?",
            choices=list(paths.keys()) + ["Back"]
        ).ask()

        if choice != "Back":
            path = questionary.path(f"Path to {choice}").ask()
            path_key = paths[choice]["path_key"]
            globals()[path_key] = path
            if logging >= 1:
                print("Path Updated. Please start SD to use the path")
            savePreferences()
        else:
            break

    usedBefore()


"""
updateArgs()
This function updates the arguments for each version of Stable Diffusion. 
It prompts the user for the new arguments and saves the updated arguments to the configuration file.
"""


def updateArgs():
    args = {
        "Automatic1111": {"args_key": "auto_args"},
        "ComfyUI": {"args_key": "comfy_args"},
        "Invoke": {"args_key": "invoke_args"},
        "Ruined Fooocus": {"args_key": "foocus_args"},
        "Kohya SS": {"args_key": "kohya_args"},
        "Volta ML": {"args_key": "volta_args"},
        "GPT Web": {"args_key": "gpt_args"},
    }

    while True:
        choice = questionary.select(
            "For which version would you like to specify arguments?",
            choices=list(args.keys()) + ["Back"]
        ).ask()

        if choice != "Back":
            arguments = questionary.text(f"Enter the arguments for {choice}").ask()
            args_key = args[choice]["args_key"]
            globals()[args_key] = arguments
            if logging >= 1:
                print("Arguments Updated. Please start SD to use the new arguments")
            savePreferences()
        else:
            break

    usedBefore()


"""
updateSettings()
This function updates the settings for the script. 
It prompts the user for the new settings and saves the updated settings to the configuration file.
"""


def updateSettings():
    global logging, default_page, exit_after_use
    while True:
        setting = questionary.select(
            "What setting would you like to change?",
            choices=["Logging", "Default Page", "Exit after use", "Delete Preferences", "Back"]
        ).ask()

        if setting == "Back":
            break
        elif setting == "Delete Preferences":
            delete = questionary.confirm("Are you sure you want to delete your preferences?", default=False).ask()
            if delete:
                resetPreferences()
                if logging >= 1:
                    print("Preferences reset.")
                    print("Please restart the program to apply changes.")

                time.sleep(1)
                sys.exit(0)
            else:
                if logging >= 1:
                    print("Deletion cancelled.")
        elif setting == "Exit after use":
            exit_after = questionary.select("Would you like to exit after use?", choices=["Yes", "No", "Back"]).ask()
            if exit_after == "Yes":
                exit_after_use = True
                if logging >= 1:
                    print("Exiting after use set to true.")
            elif exit_after == "No":
                exit_after_use = False
                if logging >= 1:
                    print("Not exiting after use set to true.")
            else:
                break
            savePreferences()
            usedBefore()
        elif setting == "Logging":
            log = questionary.select(
                "What would you like to set logging to?",
                choices=["DEBUG", "INFO", "ERROR", "Back"]
            ).ask()
            if log == "Back":
                break
            elif log == "DEBUG":
                logging = 0
            elif log == "INFO":
                logging = 1
            elif log == "ERROR":
                logging = 2
            else:
                if logging >= 1:
                    print("Invalid input.")
            if logging >= 1:
                print("Logging Updated.")
            savePreferences()
            usedBefore()
        elif setting == "Default Page":
            page = questionary.select(
                "Set default page to run?",
                choices=["Yes", "No", "Back"], default="No"
            ).ask()
            if page == "Back":
                break
            elif page == "Yes":
                default_page = 1
            else:
                default_page = 0

            if logging >= 1:
                print("Default Page Updated.")
            savePreferences()
            usedBefore()


"""
run(selected_version, settings)
This function runs a version of Stable Diffusion. 
It takes two parameters: 
- selected_version: the version of Stable Diffusion to run.
- settings: a dictionary of settings returned by checkPreferences.
The function gets the action dictionary for the selected version, 
changes the current working directory to the path of the selected version, 
and calls the runBat function to run the batch file or script for the selected version.
"""


def run(selected_version, settings):
    # Define a dictionary to map versions to their corresponding actions
    if is_windows:
        version_actions = {
            "Automatic1111": {"path_key": "auto_path", "bat_file": "webui.bat", "window_title": "Automatic1111",
                              "args_key": "auto_args"},
            "ComfyUI": {"path_key": "comfy_path", "bat_file": "main.py", "window_title": "ComfyUI",
                        "args_key": "comfy_args"},
            "Invoke": {"path_key": "invoke_path", "bat_file": "invoke.bat", "window_title": "Invoke",
                       "args_key": "invoke_args"},
            "Ruined Fooocus": {"path_key": "foocus_path", "bat_file": "launch.py", "window_title": "Ruined Fooocus",
                               "args_key": "foocus_args"},
            "Kohya SS": {"path_key": "kohya_path", "bat_file": "gui.bat", "window_title": "Kohya SS",
                         "args_key": "kohya_args"},
            "Volta ML": {"path_key": "volta_path", "bat_file": "voltaml-manager.exe", "window_title": "Volta ML",
                         "args_key": "volta_args"},
            "GPT Web": {"path_key": "gpt_path", "bat_file": "start_windows.bat", "window_title": "GPT Web UI",
                        "args_key": "gpt_args"}
        }
    else:
        version_actions = {
            "Automatic1111": {"path_key": "auto_path", "bat_file": "webui.sh", "window_title": "Automatic1111",
                              "args_key": "auto_args"},
            "ComfyUI": {"path_key": "comfy_path", "bat_file": "main.py", "window_title": "ComfyUI",
                        "args_key": "comfy_args"},
            "Invoke": {"path_key": "invoke_path", "bat_file": "invoke.sh", "window_title": "Invoke",
                       "args_key": "invoke_args"},
            "Ruined Fooocus": {"path_key": "foocus_path", "bat_file": "launch.py", "window_title": "Ruined Fooocus",
                               "args_key": "foocus_args"},
            "Kohya SS": {"path_key": "kohya_path", "bat_file": "gui.sh", "window_title": "Kohya SS",
                         "args_key": "kohya_args"},
            "Volta ML": {"path_key": "volta_path", "bat_file": "voltaml-manager", "window_title": "Volta ML",
                         "args_key": "volta_args"},
            "GPT Web": {"path_key": "gpt_path", "bat_file": "start_linux.sh", "window_title": "GPT Web UI",
                        "args_key": "gpt_args"}
        }
    action = version_actions.get(selected_version)

    if action:
        path = settings[action["path_key"]]
        path = os.path.normpath(path)
        if path != "null":
            if logging >= 0:
                print(f"Running {selected_version} from {path}")  # Debug print
            path = path.replace(":", ":\\")
            os.chdir(path)
            if is_windows:
                args = settings.get(action["args_key"], None)
                os.chdir(os.path.dirname(os.path.realpath(__file__)))
                runBat(os.path.join(path, action["bat_file"]), action["window_title"], args)
        else:
            if logging >= 1:
                print(
                    f"The path for {selected_version} is null. Please set a valid path in settings or install a valid "
                    f"release.")
    else:
        if logging >= 1:
            print("Exiting...")
        time.sleep(0.5)
        return
        # sys.exit(0)


"""
usedBefore()
This function is the main menu of the script. 
It prompts the user for an action (install SD, edit preferences/paths, run SD, or exit), 
then calls the appropriate function based on the user's choice.
"""


def usedBefore():
    global default_page, exit_after_use
    settings = checkPreferences(False, 0)
    while True:
        if str(default_page) == "0":
            action = questionary.select(
                "What would you like to do?",
                choices=["Run SD", "Edit Preferences/Paths", "Install SD", "Info", "Exit"]
            ).ask()
        else:
            default_page = 0
            action = "Run SD"

        while True:
            if action == "Install SD":
                choice = questionary.select(
                    "What would you like to install?",
                    choices=["Automatic1111", "ComfyUI", "Invoke", "Ruined Fooocus", "Kohya SS", "Volta ML", "GPT Web",
                             "Back"]
                ).ask()
                if choice != "Back":
                    installSD(choice)
                    if exit_after_use:
                        if logging >= 1:
                            print("Exiting...")
                        time.sleep(0.5)
                        sys.exit(0)
                    else:
                        pass
                else:
                    break

            elif action == "Edit Preferences/Paths":
                choice = questionary.select(
                    "What would you like to edit?",
                    choices=["Paths", "Arguments", "Settings", "Back"]
                ).ask()
                if choice == "Paths":
                    updatePath()
                elif choice == "Arguments":
                    updateArgs()
                elif choice == "Settings":
                    updateSettings()
                else:
                    break

            elif action == "Run SD":
                choice = questionary.select(
                    "What version would you like to run?",
                    choices=["Automatic1111", "ComfyUI", "Invoke", "Ruined Fooocus", "Kohya SS", "Volta ML", "GPT Web",
                             "Back"]
                ).ask()
                if choice != "Back":
                    run(choice, settings)
                    if exit_after_use:
                        if logging >= 1:
                            print("Exiting...")
                        time.sleep(0.5)
                        sys.exit(0)
                    else:
                        pass
                else:
                    break

            elif action == "Info":
                time.sleep(0.5)
                print("\n\n\n\n")
                print_centered("Info")
                print()
                print_centered("v1.0.0")
                print("\nDeveloped by [@]\n")
                print(Fore.YELLOW + "Current Known Problems: ", Style.RESET_ALL)
                print("1. InvokeAI is not supported at the moment.")
                print("2. Levels of debug logging can be chosen but dont seem to have any effect.")
                print("3. The script is not able to install npm, Git, or Anaconda on non-windows platforms.")
                print("4. The the script has not been tested on non-windows platforms. It will not run on macOS.")
                print("5. User preferences are sometimes not read properly")
                print("6. Error handling")
                print("7. Download size for Volta ML is unknown. (easy fix)")
                print("8. Randomly exits after installing a version of SD.")
                print("\nPlease fill out a bug report if you encounter any other issues.")
                print("If you think you can fix them, please submit a pull request.")
                print("\n")
                print("Soon to come features: ")
                print("1. A better way to install dependencies.")
                print("2. Executables for Windows and Linux.")
                print("3. Bug fixes.")
                print("4. Add webserver for launching, installing, and files.")
                print("\n\n")
                break
            elif action == "Exit":
                if logging >= 1:
                    print("Exiting...")
                time.sleep(0.5)
                sys.exit(0)
            else:
                return
        else:
            break


"""
newUser()
This function is called when the script is run for the first time. 
It prompts the user for an action (install SD or exit), 
then calls the appropriate function based on the user's choice.
"""


def newUser():
    while True:
        choice_1 = questionary.select(
            "What do you want to do?",
            choices=["Install SD", "Edit Preferences/Paths", "Exit"]
        ).ask()
        if choice_1 == "Install SD":
            choice_2 = questionary.select(
                "What would you like to install?",
                choices=["Automatic1111", "ComfyUI", "Invoke", "Ruined Fooocus", "Kohya SS", "Volta ML", "GPT Web", "Exit"]
            ).ask()
            installSD(choice_2)
        elif choice_1 == "Edit Preferences/Paths":
            choice = questionary.select(
                "What would you like to edit?",
                choices=["Paths", "Arguments", "Settings", "Back"]
            ).ask()
            if choice == "Paths":
                updatePath()
            elif choice == "Arguments":
                updateArgs()
            elif choice == "Settings":
                updateSettings()
            else:
                break

        elif choice_1 == "Exit":
            if logging >= 1:
                print("Exiting...")
            time.sleep(0.5)
            sys.exit(0)
        else:
            break


"""
startup()
This function prints the startup message for the script.
It prints several newline characters to clear the screen,
then prints the title of the script and some information about the script.
"""


def startup():
    print("\n\n\n\n")
    title = """

     _____ _        _     _             _   _      _                 
    /  ___| |      | |   | |           | | | |    | |                
    \ `--.| |_ __ _| |__ | | ___ ______| |_| | ___| |_ __   ___ _ __ 
     `--. \ __/ _` | '_ \| |/ _ \______|  _  |/ _ \ | '_ \ / _ \ '__|
    /\__/ / || (_| | |_) | |  __/      | | | |  __/ | |_) |  __/ |   
    \____/ \__\__,_|_.__/|_|\___|      \_| |_/\___|_| .__/ \___|_|   
                                                    | |              
                                                    |_|              

    """
    print_centered(title)
    print(Fore.CYAN + Style.BRIGHT + "\nA tool to help new and existing users with Stable Diffusion.\n", Style.RESET_ALL)
    print("Developed by [@]")
    print("v1.0.0")
    print("\n\n")


"""
main()
This function is the entry point of the script. 
It checks the user's preferences, then calls the usedBefore function if the user has used the script before, 
or the newUser function if the user is new.
"""


def main():
    global new_user, ask_again
    os.chdir(os.getcwd())
    used = checkPreferences(True, 0)
    startup()
    time.sleep(1.5)
    if checkPreferences(True, 1):
        used_before = questionary.confirm("Have you used Stable Diffusion before").ask()
        if used_before:
            new_user = True
            ask_again = questionary.confirm("Would you like to display this message every startup?").ask()
            savePreferences()
            checkRequirements()
            usedBefore()
        else:
            new_user = False
            ask_again = questionary.confirm("Would you like to display this message every startup?").ask()
            savePreferences()
            checkRequirements()
            newUser()

    else:
        if used:
            checkRequirements()
            usedBefore()
        else:
            checkRequirements()
            newUser()


"""
Starts the program.
"""
if __name__ == '__main__':
    main()
