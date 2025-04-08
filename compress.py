import os  # Import OS module for file and directory operations
import shutil  # Import shutil for file operations
import subprocess  # Import subprocess for running external commands
import sys  # Import sys for platform-specific operations
from pathlib import Path  # Import Path for path manipulations
from PIL import Image  # Import Image for image processing
from concurrent.futures import ThreadPoolExecutor  # Import ThreadPoolExecutor for parallel processing
from datetime import datetime  # Import datetime for timestamps

# Constants
WEBP_QUALITY = '90'  # Quality for WebP compression
V_CODEC_WEBM = 'libvpx'  # Video codec for WebM
A_CODEC_WEBM = 'libvorbis'  # Audio codec for WebM
CRF_WEBM = '47'  # Constant Rate Factor for WebM
DELETE_ORIGINALS = True  # Flag to delete original files after processing
LOG_FILE = 'conversion_log.txt'  # Log file for recording operations

# Add CREATE_NO_WINDOW for Windows
CREATE_NO_WINDOW = 0x08000000 if sys.platform.startswith('win') else 0  # Prevents cmd window pop-ups on Windows

def clearConsole():
  if sys.platform.startswith('win'):  # Check if the platform is Windows
    os.system('cls')  # Clear console for Windows
  else:
    os.system('clear')  # Clear console for Linux/macOS

def getVideoDimensions(videoPath):
  try:
    result = subprocess.run(
      ['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height', '-of', 'csv=s=x:p=0', videoPath],
      stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=CREATE_NO_WINDOW
    )  # Run ffprobe to get video dimensions
    output = result.stdout.strip()  # Trim the output
    dimensions = output.split('x')  # Split dimensions
    if len(dimensions) >= 2:
      return map(int, dimensions[:2])  # Return width and height as integers
  except Exception as e:
    with open(LOG_FILE, 'a') as f:
      f.write(f"Error getting dimensions for {videoPath}: {e}\n")  # Log error
  return None, None  # Return None if dimensions cannot be retrieved

def moveUnpairedFiles(folder1, folder2, outputFolder):
  os.makedirs(outputFolder, exist_ok=True)  # Ensure the output folder exists
  
  files1 = os.listdir(folder1)  # List files in folder1
  files2 = os.listdir(folder2)  # List files in folder2
  
  baseNames1 = {os.path.splitext(f)[0] for f in files1}  # Get base names from folder1
  baseNames2 = {os.path.splitext(f)[0] for f in files2}  # Get base names from folder2
  
  unpairedInFolder1 = baseNames1 - baseNames2  # Find unpaired files in folder1
  unpairedInFolder2 = baseNames2 - baseNames1  # Find unpaired files in folder2
  
  for file in files1:
    baseName = os.path.splitext(file)[0]  # Get base name
    if baseName in unpairedInFolder1:
      shutil.move(os.path.join(folder1, file), os.path.join(outputFolder, file))  # Move unpaired file from folder1
  
  for file in files2:
    baseName = os.path.splitext(file)[0]  # Get base name
    if baseName in unpairedInFolder2:
      shutil.move(os.path.join(folder2, file), os.path.join(outputFolder, file))  # Move unpaired file from folder2

  print(f"Unpaired files have been moved to: {outputFolder}")  # Print completion message

def processImage(imagePath, outputFolder, movedFolder):
  filename = str(imagePath)  # Convert Path object to string
  filenameOut = os.path.join(outputFolder, f'{imagePath.stem}.webp')  # Output file path
  try:
    subprocess.check_call(
      ['cwebp', '-q', WEBP_QUALITY, filename, '-o', filenameOut],
      creationflags=CREATE_NO_WINDOW
    )  # Convert to WebP
    with open(LOG_FILE, 'a') as f:
      f.write(f"Processed image: {filename} -> {filenameOut}\n")  # Log success
  except subprocess.CalledProcessError as e:
    with open(LOG_FILE, 'a') as f:
      f.write(f"Error converting image: {filename}: {e}\n")  # Log error
    return
  
  if imagePath.suffix.lower() == '.png':  # Check if the file is a PNG
    try:
      im = Image.open(filename)  # Open the image
      userComment = im.info.get('parameters', '')  # Get metadata
      subprocess.check_call(
        ['exiftool', '-overwrite_original', f'-UserComment={userComment}', filenameOut],
        creationflags=CREATE_NO_WINDOW
      )  # Add metadata to WebP
    except Exception as e:
      with open(LOG_FILE, 'a') as f:
        f.write(f"Error processing PNG metadata for {filename}: {e}\n")  # Log error
  
  os.utime(filenameOut, (os.path.getmtime(filename), os.path.getmtime(filename)))  # Set modification date
  
  if not os.path.exists(filenameOut):  # Check if the output file exists
    with open(LOG_FILE, 'a') as f:
      f.write(f"Failed to create compressed file for: {filename}\n")  # Log failure
    return
  
  originalSize = os.path.getsize(filename)  # Get original file size
  compressedSize = os.path.getsize(filenameOut)  # Get compressed file size
  
  if originalSize < compressedSize:  # Check if the original is smaller
    shutil.copy2(filename, filenameOut)  # Copy original to output folder
    os.remove(filenameOut)  # Remove the larger compressed file
    with open(LOG_FILE, 'a') as f:
      f.write(f"Compressed file larger than original, kept original: {filename}\n")  # Log decision

  if DELETE_ORIGINALS:  # Check if originals should be deleted
    os.makedirs(movedFolder, exist_ok=True)  # Ensure the backup folder exists
    shutil.move(filename, movedFolder)  # Move original to backup folder
    with open(LOG_FILE, 'a') as f:
      f.write(f"Moved original image to backup: {filename}\n")  # Log move

def processVideo(videoPath, outputFolder, movedFolder):
  filename = str(videoPath)  # Convert Path object to string
  filenameOut = os.path.join(outputFolder, f'{videoPath.stem}.webm')  # Output file path
  
  width, height = getVideoDimensions(filename)  # Get video dimensions
  if width is None or height is None:
    with open(LOG_FILE, 'a') as f:
      f.write(f"Error getting dimensions for video: {filename}\n")  # Log error
    return
  
  scale = f"640:-2" if width > height else f"-2:640"  # Determine scale parameters
  
  try:
    subprocess.check_call(
      [
        'ffmpeg', '-i', filename, '-vf', f'scale={scale}',
        '-c:v', V_CODEC_WEBM, '-crf', CRF_WEBM, '-b:v', '1M', '-c:a', A_CODEC_WEBM,
        filenameOut
      ],
      creationflags=CREATE_NO_WINDOW
    )  # Convert to WebM
    with open(LOG_FILE, 'a') as f:
      f.write(f"Processed video: {filename} -> {filenameOut}\n")  # Log success
  except subprocess.CalledProcessError as e:
    with open(LOG_FILE, 'a') as f:
      f.write(f"Error compressing video: {filename}: {e}\n")  # Log error
    return
  
  originalSize = os.path.getsize(filename)  # Get original file size
  compressedSize = os.path.getsize(filenameOut)  # Get compressed file size
  
  if compressedSize >= originalSize:  # Check if the compressed file is larger
    os.remove(filenameOut)  # Delete the compressed file
    shutil.copy(filename, filenameOut)  # Copy original to output folder
    with open(LOG_FILE, 'a') as f:
      f.write(f"Compressed video larger than original, kept original: {filename}\n")  # Log decision
  else:
    with open(LOG_FILE, 'a') as f:
      f.write(f"Compressed video is smaller, kept compressed: {filename}\n")  # Log decision

  if DELETE_ORIGINALS:  # Check if originals should be deleted
    os.makedirs(movedFolder, exist_ok=True)  # Ensure the backup folder exists
    shutil.move(filename, movedFolder)  # Move original to backup folder
    with open(LOG_FILE, 'a') as f:
      f.write(f"Moved original video to backup: {filename}\n")  # Log move

def main():
  clearConsole()  # Clear the console
  inputPath = input('Enter the directory path: ')  # Get input directory path
  inputFolderName = os.path.basename(os.path.normpath(inputPath))  # Get folder name
  
  # Create output folders in the same directory as the input folder
  outputFolder = os.path.join(inputPath, f'{inputFolderName}_compressed')  # Output folder path
  movedFolder = os.path.join(inputPath, f'{inputFolderName}_originals_backup')  # Backup folder path
  unpairedFolder = os.path.join(inputPath, f'{inputFolderName}_unpaired')  # Unpaired folder path
  
  os.makedirs(outputFolder, exist_ok=True)  # Ensure output folder exists
  os.makedirs(movedFolder, exist_ok=True)  # Ensure backup folder exists
  os.makedirs(unpairedFolder, exist_ok=True)  # Ensure unpaired folder exists
  
  with open(LOG_FILE, 'a') as f:
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Get current timestamp
    f.write(f"\n--- Script Execution Started: {timestamp} ---\n")  # Log start time
  
  files = [os.path.join(inputPath, file) for file in os.listdir(inputPath) if os.path.isfile(os.path.join(inputPath, file))]  # Get list of files
  
  with ThreadPoolExecutor() as executor:  # Use ThreadPoolExecutor for parallel processing
    for filePath in files:
      if filePath.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):  # Check for image files
        executor.submit(processImage, Path(filePath), outputFolder, movedFolder)  # Process image
      elif filePath.lower().endswith(('.mp4', '.mov', '.avi', '.webm', '.m4v')):  # Check for video files
        executor.submit(processVideo, Path(filePath), outputFolder, movedFolder)  # Process video
  
  moveUnpairedFiles(outputFolder, movedFolder, unpairedFolder)  # Move unpaired files
  
  with open(LOG_FILE, 'a') as f:
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Get current timestamp
    f.write(f"--- Script Execution Ended: {timestamp} ---\n")  # Log end time

if __name__ == '__main__':
  main()  # Run the main function