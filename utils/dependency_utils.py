import importlib  # Import the importlib module
import sys  # Import the sys module
import logging  # Import logging module
import shutil  # Import shutil to check for executables

def checkDependencies():
  dependencies = {
    'keyboard': 'pip install keyboard',  # Python module
    'tqdm': 'pip install tqdm',  # Python module
    'Pillow': 'pip install Pillow',  # Python module
    'ffmpeg': 'Refer to https://ffmpeg.org/download.html for installation',  # External executable
    'exiftool': 'Refer to https://exiftool.org/ for installation'  # External executable
  }  # Define required dependencies and their installation instructions

  missing = []
  for module, installCmd in dependencies.items():
    if module in ['ffmpeg', 'exiftool']:  # Check for external executables
      if not shutil.which(module):  # Verify if the executable is in PATH
        missing.append((module, installCmd))  # Add missing executable and installation command
    else:
      try:
        importlib.import_module(module)  # Try importing the Python module
      except ImportError:
        missing.append((module, installCmd))  # Add missing module and installation command

  if missing:
    print('\nThe following dependencies are missing:')
    for module, installCmd in missing:
      print(f'- {module}: {installCmd}')  # Print missing module or executable and how to install it
    print('\nPlease install the missing dependencies and restart the script.')
    sys.exit(1)  # Exit the script if dependencies are missing
  else:
    logging.info('Dependencies checked successfully')  # Log dependency check success