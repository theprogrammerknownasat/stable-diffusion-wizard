# Description: This file contains functions that are not used in the main program, but are still useful for debugging
# and testing.
import subprocess
import sys
import urllib
import zipfile
from main import update_progress, make_executable

git_path = "git"
logging = 1
is_windows = sys.platform == 'win32'

"""
download_and_extract(url, filename, name, extract_dir, is_zip, is_executable)
This function downloads a file from a URL and extracts it if it's a zip file.
It takes six parameters:
- url: the URL to download the file from.
- filename: the name to save the downloaded file as.
- name: the name of the file (used for the progress bar).
- extract_dir: the directory to extract the zip file to.
- is_zip: a boolean indicating whether the file is a zip file.
- is_executable: a boolean indicating whether the file should be made executable.
The function downloads the file, updates the progress bar during the download,
and if the file is a zip file, it extracts it to the specified directory.
If the file should be made executable, it changes the file permissions to make it executable.
"""


def download_and_extract(url, filename, name, extract_dir, is_zip, is_executable):
    # Download the file
    if ".git" in url:
        subprocess.run([git_path, "clone", url, "."], stdout=subprocess.PIPE)

    else:
        urllib.request.urlretrieve(url, filename,
                                   reporthook=lambda count, block_size, total_size: update_progress(count,
                                                                                                    block_size,
                                                                                                    total_size,
                                                                                                    name))
    if logging >= 1:
        print(f"\n{name} downloaded.")

    if is_zip:
        # Extract the zip file
        with zipfile.ZipFile(filename, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        if logging >= 1:
            print(f"{name} extracted.")

    if is_executable and sys.platform is not is_windows:
        make_executable(filename)
