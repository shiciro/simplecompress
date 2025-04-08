import os
import shutil
import subprocess
import sys
from pathlib import Path
from PIL import Image
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime  # Import for timestamp

# Image compression settings
webpQuality = "90"
# Video compression settings
vcodec_webm = "libvpx"
acodec_webm = "libvorbis"
crf_webm = "47"
deleteOriginals = True
log_file = "conversion_log.txt"  # Set the path to the log file

# Add CREATE_NO_WINDOW for Windows
CREATE_NO_WINDOW = 0x08000000 if sys.platform.startswith('win') else 0

def clear_console():
    if sys.platform.startswith('win'):
        os.system('cls')
    else:
        os.system('clear')

def get_video_dimensions(video_path):
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=s=x:p=0", video_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=CREATE_NO_WINDOW  # Prevents cmd window from popping up
        )
        output = result.stdout.strip()
        dimensions = output.split('x')
        if len(dimensions) >= 2:
            return map(int, dimensions[:2])
    except Exception as e:
        with open(log_file, 'a') as f:
            f.write(f"Error getting dimensions for {video_path}: {e}\n")
    return None, None

def move_unpaired_files(folder1, folder2, output_folder):
    # Create the output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)
    
    # Get full file lists from both folders
    files1 = os.listdir(folder1)
    files2 = os.listdir(folder2)
    
    # Get filenames without extensions
    base_names1 = {os.path.splitext(f)[0] for f in files1}
    base_names2 = {os.path.splitext(f)[0] for f in files2}
    
    # Find unpaired base names
    unpaired_in_folder1 = base_names1 - base_names2
    unpaired_in_folder2 = base_names2 - base_names1
    
    # Move unpaired files from folder1 to output folder
    for file in files1:
        base_name = os.path.splitext(file)[0]
        if base_name in unpaired_in_folder1:
            shutil.move(os.path.join(folder1, file), os.path.join(output_folder, file))
    
    # Move unpaired files from folder2 to output folder
    for file in files2:
        base_name = os.path.splitext(file)[0]
        if base_name in unpaired_in_folder2:
            shutil.move(os.path.join(folder2, file), os.path.join(output_folder, file))

    print("Unpaired files have been moved to:", output_folder)

def process_image(image_path, output_folder, moved_folder):
    filename = str(image_path)
    filenameOut = os.path.join(output_folder, f'{image_path.stem}.webp')
    try:
        subprocess.check_call(
            ['cwebp', '-q', webpQuality, filename, '-o', filenameOut],
            creationflags=CREATE_NO_WINDOW  # Prevents cmd window from popping up
        )
        with open(log_file, 'a') as f:
            f.write(f"Processed image: {filename} -> {filenameOut}\n")
    except subprocess.CalledProcessError as e:
        with open(log_file, 'a') as f:
            f.write(f"Error converting image: {filename}: {e}\n")
        return
    
    if image_path.suffix.lower() == '.png':
        try:
            im = Image.open(filename)
            userComment = im.info.get("parameters", "")
            subprocess.check_call(
                ['exiftool', '-overwrite_original', f'-UserComment={userComment}', filenameOut],
                creationflags=CREATE_NO_WINDOW  # Prevents cmd window from popping up
            )
        except Exception as e:
            with open(log_file, 'a') as f:
                f.write(f"Error processing PNG metadata for {filename}: {e}\n")
    
    os.utime(filenameOut, (os.path.getmtime(filename), os.path.getmtime(filename)))
    
    if not os.path.exists(filenameOut):
        with open(log_file, 'a') as f:
            f.write(f"Failed to create compressed file for: {filename}\n")
        return
    
    original_size = os.path.getsize(filename)
    compressed_size = os.path.getsize(filenameOut)
    
    if original_size < compressed_size:
        shutil.copy2(filename, filenameOut)
        os.remove(filenameOut)
        with open(log_file, 'a') as f:
            f.write(f"Compressed file larger than original, kept original: {filename}\n")

    if deleteOriginals:
        os.makedirs(moved_folder, exist_ok=True)
        shutil.move(filename, moved_folder)
        with open(log_file, 'a') as f:
            f.write(f"Moved original image to backup: {filename}\n")

def process_video(video_path, output_folder, moved_folder):
    filename = str(video_path)
    filenameOut = os.path.join(output_folder, f'{video_path.stem}.webm')
    
    width, height = get_video_dimensions(filename)
    if width is None or height is None:
        with open(log_file, 'a') as f:
            f.write(f"Error getting dimensions for video: {filename}\n")
        return
    
    scale = f"640:-2" if width > height else f"-2:640"
    codec = vcodec_webm  # Use libvpx as the default codec
    
    try:
        subprocess.check_call(
            [
                "ffmpeg", "-i", filename, "-vf", f"scale={scale}",
                "-c:v", codec, "-crf", crf_webm, "-b:v", "1M", "-c:a", acodec_webm,
                filenameOut
            ],
            creationflags=CREATE_NO_WINDOW  # Prevents cmd window from popping up
        )
        with open(log_file, 'a') as f:
            f.write(f"Processed video: {filename} -> {filenameOut}\n")
    except subprocess.CalledProcessError as e:
        with open(log_file, 'a') as f:
            f.write(f"Error compressing video: {filename}: {e}\n")
        return
    
    original_size = os.path.getsize(filename)
    compressed_size = os.path.getsize(filenameOut)
    
    if compressed_size >= original_size:
        os.remove(filenameOut)
        shutil.copy(filename, filenameOut)
        with open(log_file, 'a') as f:
            f.write(f"Compressed video larger than original, kept original: {filename}\n")
    else:
        with open(log_file, 'a') as f:
            f.write(f"Compressed video is smaller, kept compressed: {filename}\n")

    if deleteOriginals:
        os.makedirs(moved_folder, exist_ok=True)
        shutil.move(filename, moved_folder)
        with open(log_file, 'a') as f:
            f.write(f"Moved original video to backup: {filename}\n")

def main():
    clear_console()
    input_path = input("Enter the directory path: ")
    input_folder_name = os.path.basename(os.path.normpath(input_path))
    output_folder = f"{input_folder_name}_compressed"
    moved_folder = f"{input_folder_name}_originals_backup"
    unpaired_folder = f"{input_folder_name}_unpaired"
    os.makedirs(output_folder, exist_ok=True)
    os.makedirs(moved_folder, exist_ok=True)
    os.makedirs(unpaired_folder, exist_ok=True)
    
    # Append to the log file and add a timestamp
    with open(log_file, 'a') as f:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"\n--- Script Execution Started: {timestamp} ---\n")
    
    files = [os.path.join(input_path, file) for file in os.listdir(input_path) if os.path.isfile(os.path.join(input_path, file))]
    
    with ThreadPoolExecutor() as executor:
        for file_path in files:
            if file_path.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                executor.submit(process_image, Path(file_path), output_folder, moved_folder)
            elif file_path.lower().endswith(('.mp4', '.mov', '.avi', '.webm', '.m4v')):
                executor.submit(process_video, Path(file_path), output_folder, moved_folder)
    
    # Move unpaired files
    move_unpaired_files(output_folder, moved_folder, unpaired_folder)
    
    # Log the end of the script execution
    with open(log_file, 'a') as f:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"--- Script Execution Ended: {timestamp} ---\n")

if __name__ == "__main__":
    main()