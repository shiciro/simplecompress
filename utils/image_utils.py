import os
import shutil
from pathlib import Path
from PIL import Image
import subprocess
from config import WEBP_QUALITY, MOVE_ORIGINALS_TO_BACKUP, LOG_FILE, CREATE_NO_WINDOW, LOG_METADATA  # Import shared constants
from datetime import datetime  # Import datetime for timestamps
import logging  # Import logging module

# Configure logging
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s %(message)s')

def handleFileConflict(filePath, outputFolder, movedFolder):
  baseName = os.path.splitext(os.path.basename(filePath))[0]
  conflictFolder = os.path.join(outputFolder, f'{baseName}_conflict')

  conflictDetected = False

  outputFile = os.path.join(outputFolder, f'{baseName}.webp')
  if os.path.exists(outputFile):
    os.makedirs(conflictFolder, exist_ok=True)
    shutil.move(outputFile, os.path.join(conflictFolder, os.path.basename(outputFile)))
    conflictDetected = True

  originalFile = os.path.join(movedFolder, os.path.basename(filePath))
  if os.path.exists(originalFile):
    os.makedirs(conflictFolder, exist_ok=True)
    shutil.move(originalFile, os.path.join(conflictFolder, os.path.basename(originalFile)))
    conflictDetected = True

  if not conflictDetected and os.path.exists(conflictFolder):
    os.rmdir(conflictFolder)

  if conflictDetected:
    logging.info(f"Conflicting files moved to: {conflictFolder}")  # Log conflict resolution message

def processImage(imagePath, outputFolder, movedFolder):
  filename = str(imagePath)
  filenameOut = os.path.join(outputFolder, f'{imagePath.stem}.webp')
  messages = []
  status = 'success'

  if os.path.exists(filenameOut) or os.path.exists(os.path.join(movedFolder, os.path.basename(filename))):
    handleFileConflict(filename, outputFolder, movedFolder)
    messages.append(f"File conflict detected for: {filename}")

  try:
    subprocess.check_call(
      ['cwebp', '-q', WEBP_QUALITY, filename, '-o', filenameOut],
      creationflags=CREATE_NO_WINDOW,
      stdout=subprocess.DEVNULL,
      stderr=subprocess.DEVNULL
    )
    messages.append(f"Image successfully compressed: {filename} -> {filenameOut}")
  except subprocess.CalledProcessError as e:
    status = 'error'
    messages.append(f"Error compressing image: {filename}: {e}")
    return {'status': status, 'messages': messages, 'file': filename}

  if imagePath.suffix.lower() == '.png':
    try:
      with Image.open(filename) as im:
        userComment = im.info.get('parameters', '')
        prompt = im.info.get('prompt', '')
        workflow = im.info.get('workflow', '')

        userComment = userComment.replace('"', '\\"')
        prompt = prompt.replace('"', '\\"')
        workflow = workflow.replace('"', '\\"')

        if LOG_METADATA:
          messages.append(f"Metadata extracted for {filename}: parameters='{userComment}', prompt='{prompt}', workflow='{workflow}'")

      subprocess.check_call(
        ['exiftool', '-overwrite_original', 
         f'-UserComment={userComment}', 
         f'-Prompt={prompt}', 
         f'-Workflow={workflow}', 
         filenameOut],
        creationflags=CREATE_NO_WINDOW,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
      )
      messages.append(f"Metadata successfully added to: {filenameOut}")
    except Exception as e:
      status = 'error'
      messages.append(f"Error processing metadata for {filename}: {e}")

  try:
    os.utime(filenameOut, (os.path.getmtime(filename), os.path.getmtime(filename)))
    messages.append(f"Timestamps updated for: {filenameOut}")
  except FileNotFoundError:
    status = 'error'
    messages.append(f"Error updating timestamps for {filenameOut}: File not found")

  if not os.path.exists(filenameOut):
    status = 'error'
    messages.append(f"Failed to create compressed file for: {filename}")
    return {'status': status, 'messages': messages, 'file': filename}

  originalSize = os.path.getsize(filename)
  compressedSize = os.path.getsize(filenameOut)

  if compressedSize >= originalSize:
    os.remove(filenameOut)
    shutil.copy2(filename, filenameOut)
    try:
      original_atime = os.path.getatime(filename)
      original_mtime = os.path.getmtime(filename)
      os.utime(filenameOut, (original_atime, original_mtime))
      messages.append(f"Timestamps updated for copied file: {filenameOut}")
    except Exception as e:
      status = 'error'
      messages.append(f"Error updating timestamps for copied file {filenameOut}: {e}")
    messages.append(f"Compressed file larger than original, kept original: {filename}")

  if MOVE_ORIGINALS_TO_BACKUP:
    try:
      os.makedirs(movedFolder, exist_ok=True)
      shutil.move(filename, os.path.join(movedFolder, os.path.basename(filename)))
      messages.append(f"Original image moved to backup: {filename}")
    except Exception as e:
      status = 'error'
      messages.append(f"Error moving original image to backup: {filename}: {e}")

  return {'status': status, 'messages': messages, 'file': filename}