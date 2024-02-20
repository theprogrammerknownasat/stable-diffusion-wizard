import configparser
import os
import platform
import subprocess
import sys
import time
import urllib.request
import zipfile

from colorama import Fore, Style
import questionary

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
auto = False
comfy = False
invoke = False
foocus = False
kohya = False
volta = False
gpt = False

git_path = "git"


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
            print(f"Preferences loaded from {config_file}")
            return dict(config['Settings'])


settings = checkPreferences(False, 0)
globals().update(settings)


def update_progress(count, block_size, total_size):
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
    print('\rDownloading Git: {} {}'.format(bar, percentage), end='', flush=True)


def main():
    global new_user, ask_again

    used = checkPreferences(True, 0)
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
            usedBefore()
        else:
            newUser()


def checkRequirements():
    # Check Python version
    python_version = platform.python_version()
    major, minor, micro = python_version.split('.')
    if major == '3' and minor == '10':
        print(f"Python version: {python_version}")
    else:
        print()
        print()
        print(
            Fore.RED + f"Warning: Your Python version is {python_version}. Most versions of Stable Diffusion are "
                       f"designed to work with Python 3.10 and may not start without it" + Style.RESET_ALL)
        print()
        print()


    # Check if Git is installed
    try:
        try:
            subprocess.check_output(["git", "--version"])
            print("Git is installed.")
        except:
            subprocess.check_output(["./git/cmd/git.exe", "--version"])
            print("Git is installed locally.")
            global git_path
            git_path = "./git/cmd/git.exe"

    except:
        print("Git is not installed.")
        # Prompt the user to install Git
        install_git = questionary.confirm("Would you like to install Git?").ask()
        if install_git:
            git_url = "https://github.com/git-for-windows/git/releases/download/v2.44.0-rc1.windows.1/MinGit-2.44.0-rc1-64-bit.zip"
            filename = git_url.split("/")[-1]
            urllib.request.urlretrieve(git_url, filename, reporthook=update_progress)
            print("\nGit downloaded. Extracting Git...")

            # Create a "git" subdirectory in the script's directory
            script_dir = os.path.dirname(os.path.realpath(__file__))
            git_dir = os.path.join(script_dir, "git")
            os.makedirs(git_dir, exist_ok=True)

            # Extract the Git zip file to the "git" subdirectory
            with zipfile.ZipFile(filename, 'r') as zip_ref:
                zip_ref.extractall(git_dir)

            git_path = os.path.join(git_dir, "cmd", "git.exe")

            print("Git extracted. ")
            return


def runBat(file_path, window_title, args=None):
    if file_path.endswith('.py'):
        cmd = f'start "{window_title}" cmd.exe /k "python {file_path}"'
    else:
        cmd = f'start "{window_title}" cmd.exe /c "{file_path}"'

    if args:
        cmd += ' ' + args

    subprocess.run(cmd, shell=True)


def savePreferences():
    config = configparser.ConfigParser()
    config['Settings'] = {
        'used': new_user,
        'ask_again': ask_again,
        'auto': auto,
        'comfy': comfy,
        'invoke': invoke,
        'foocus': foocus,
        'kohya': kohya,
        'volta': volta,
        'gpt': gpt,
        'web': web_args,
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
        'gpt_path': gpt_path
    }

    config_dir = os.path.join(os.environ['APPDATA'], 'SD-helper') if sys.platform == 'win32' else os.path.join(
        os.path.expanduser('~'), '.local', 'SD-helper')
    os.makedirs(config_dir, exist_ok=True)

    with open(os.path.join(config_dir, 'settings.cfg'), 'w') as config_file:
        config.write(config_file)

    print(f"Preferences saved to {os.path.join(config_dir, 'settings.cfg')}")


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
        print("Exiting...")
        time.sleep(0.5)
        sys.exit(0)


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
            print("Path Updated. Please start SD to use the path")
            savePreferences()
        else:
            break

    usedBefore()


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
            print("Arguments Updated. Please start SD to use the new arguments")
            savePreferences()
        else:
            break

    usedBefore()


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


def updateSettings():
    pass


def usedBefore():
    settings = checkPreferences(False, 0)
    while True:
        action = questionary.select(
            "What do you want to do?",
            choices=["Install SD", "Run SD", "Edit Preferences/Paths", "Exit"]
        ).ask()

        if action == "Install SD":
            while True:
                version = questionary.select(
                    "What would you like to install?",
                    choices=["Automatic1111", "ComfyUI", "Invoke", "Ruined Fooocus", "Kohya SS", "Volta ML", "GPT Web",
                             "Back"]
                ).ask()
                if version == "Back":
                    break
                installSD(version)

        elif action == "Edit Preferences/Paths":
            while True:
                preference = questionary.select(
                    "What would you like to edit?",
                    choices=["Paths", "Preferences", "Back"]
                ).ask()

                if preference == "Paths":
                    updatePath()
                elif preference == "Preferences":
                    while True:
                        argument = questionary.select(
                            "What would you like to edit?",
                            choices=["CMD Arguments", "Settings", "Back"]
                        ).ask()
                        if argument == "Back":
                            break
                        elif argument == "CMD Arguments":
                            updateArgs()
                        elif argument == "Settings":
                            updateSettings()
                else:
                    break

        elif action == "Run SD":
            while True:
                version = questionary.select(
                    "What would you like to run?",
                    choices=["Automatic1111", "ComfyUI", "Invoke", "Ruined Fooocus", "Kohya SS", "Volta ML", "GPT Web",
                             "Back"]
                ).ask()
                if version == "Back":
                    break
                run(version, settings)

        else:
            print("Exiting...")
            time.sleep(0.5)
            sys.exit(0)


def run(selected_version, settings):
    # Define a dictionary to map versions to their corresponding actions
    version_actions = {
        "Automatic1111": {"path_index": 0,
                          "bat_file": "webui.bat",
                          "window_title": "Automatic1111",
                          "args_key": "auto_args"
                          },
        "ComfyUI": {"path_index": 1,
                    "bat_file": "main.py",
                    "window_title": "ComfyUI",
                    "args_key": "comfy_args"
                    },
        "Invoke": {"path_index": 2,
                   "bat_file": "invoke.bat",
                   "window_title": "Invoke",
                   "args_key": "invoke_args"
                   },
        "Ruined Fooocus": {"path_index": 3,
                           "bat_file": "run.bat",
                           "window_title": "Ruined Fooocus",
                           "args_key": "foocus_args"
                           },
        "Kohya SS": {"path_index": 4,
                     "bat_file": "gui.bat",
                     "window_title": "Kohya SS",
                     "args_key": "kohya_args"
                     },
        "Volta ML": {"path_index": 5,
                     "bat_file": "voltaml-manager.exe",
                     "window_title": "Volta ML",
                     "args_key": "volta_args"
                     },
        "GPT Web": {"path_index": 6,
                    "bat_file": "start_windows.bat",
                    "window_title": "GPT Web UI",
                    "args_key": "gpt_args"
                    }
    }

    action = version_actions.get(selected_version)

    if action:
        path = settings[action["path_index"]]
        if path != "null":
            os.chdir(path)
            if sys.platform == 'win32':
                args = settings.get(action["args_key"], None)
                runBat(action["bat_file"], action["window_title"], args)
        else:
            print(f"The path for {selected_version} is null. Please set a valid path in settings or install a valid "
                  f"release.")
    else:
        print("Exiting...")
        time.sleep(0.5)
        sys.exit(0)


def install(id):
    if id == 1:
        print("Installing Automatic1111...")

    if id == 2:
        print("Installing ComfyUI...")
        time.sleep(1)
    if id == 3:
        print("Installing Invoke...")
        time.sleep(1)
    if id == 4:
        print("Installing Ruined Fooocus...")
        time.sleep(1)
    if id == 5:
        print("Installing Kohya SS...")
        time.sleep(1)
    if id == 6:
        print("Installing Volta ML...")
        time.sleep(1)
    if id == 7:
        print("Installing GPT web...")
        time.sleep(1)
    else:
        raise ValueError("Invalid ID")


def newUser():
    choice_1 = questionary.select(
        "What do you want to do?",
        choices=["Install SD", "Exit"]
    ).ask()
    if choice_1 == "Install SD":
        choice_2 = questionary.select(
            "What would you like to install?",
            choices=["Automatic1111", "ComfyUI", "Invoke", "Ruined Fooocus", "Kohya SS", "Volta ML", "GPT Web", "Exit"]
        ).ask()
        installSD(choice_2)

    else:
        print("Exiting...")
        time.sleep(0.5)
        sys.exit(0)


if __name__ == '__main__':
    main()

"""questionary.text("What's your first name").ask()
    questionary.password("What's your secret?").ask()
    questionary.confirm("Are you amazed?").ask()

    questionary.select(
        "What do you want to do?",
        choices=["Order a pizza", "Make a reservation", "Ask for opening hours"],
    ).ask()

    questionary.rawselect(
        "What do you want to do?",
        choices=["Order a pizza", "Make a reservation", "Ask for opening hours"],
    ).ask()

    questionary.checkbox(
        "Select toppings", choices=["foo", "bar", "bazz"]
    ).ask()

    questionary.path("Path to the projects version file").ask()"""
