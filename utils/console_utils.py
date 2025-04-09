import os
import sys
import logging  # Import logging module

def clearConsole():
  if sys.platform.startswith('win'):
    os.system('cls')
  else:
    os.system('clear')
  logging.info('Console cleared')  # Log the console clear action
