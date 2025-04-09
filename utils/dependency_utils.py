import importlib  # Import the importlib module
import sys  # Import the sys module
import logging  # Import logging module

def checkDependencies():
  dependencies = {
    'keyboard': 'pip install keyboard',
    'tqdm': 'pip install tqdm',
    'Pillow': 'pip install Pillow',
    'ffmpeg': 'Refer to https://ffmpeg.org/download.html for installation',
    'exiftool': 'Refer to https://exiftool.org/ for installation'
  }  # Define required dependencies and their installation instructions

  missing = []
  for module, installCmd in dependencies.items():
    try:
      importlib.import_module(module)  # Try importing the module
    except ImportError:
      missing.append((module, installCmd))  # Add missing module and installation command

  if missing:
    print('\nThe following dependencies are missing:')
    for module, installCmd in missing:
      print(f'- {module}: {installCmd}')  # Print missing module and how to install it
    print('\nPlease install the missing dependencies and restart the script.')
    sys.exit(1)  # Exit the script if dependencies are missing
  else:
    logging.info('Dependencies checked successfully')  # Log dependency check success