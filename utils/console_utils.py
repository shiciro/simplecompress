import os
import sys

def clearConsole():
  if sys.platform.startswith('win'):
    os.system('cls')
  else:
    os.system('clear')
