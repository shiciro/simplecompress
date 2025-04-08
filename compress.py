import os
from pathlib import Path
from PIL import Image
import subprocess
import sys
import shutil

# Image compression settings
webpQuality = "90"
# Video compression settings
vcodec_webm = "libvpx"
acodec_webm = "libvorbis"
crf_webm = "47"
deleteOriginals = True
log_file = "conversion_log.txt"  # Set the path to the log file

def clear_console():
    # Clear console for Windows, Linux, and macOS
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
            text=True
        )
        output = result.stdout.strip()
        dimensions = output.split('x')
        if len(dimensions) >= 2:
            width, height = map(int, dimensions[:2])
            return width, height
        else:
            raise ValueError("Unexpected output from ffprobe command")
    except Exception as e:
        with open(log_file, 'a') as f:
            f.write(f"Error getting dimensions for {video_path}: {e}\n")
            f.write(f"ffprobe output: {result.stdout}\n")
            f.write(f"ffprobe error: {result.stderr}\n")
        return None, None

def process_image(image_path, output_folder, moved_folder):
    filename = str(image_path)
    filenameOut = os.path.join(output_folder, f'{image_path.stem}.webp')
    try:
        # Convert to WEBP
        subprocess.check_call(['cwebp', '-q', webpQuality, filename, '-o', filenameOut])
    except subprocess.CalledProcessError as e:
        with open(log_file, 'a') as f:
            f.write(f"Error converting {filename}: {e}\n")
        return

    # Copy PNG Chunk data from original PNG
    if image_path.suffix.lower() == '.png':
        im = Image.open(filename)
        im.load()  # Needed only for .png EXIF data (see citation above)
        userComment = im.info.get("parameters", "")
        # Write UserComment to WEBP
        subprocess.check_call(['exiftool', '-overwrite_original', f'-UserComment={userComment}', filenameOut])

    # Set modification date
    original_modification_time = os.path.getmtime(filename)
    os.utime(filenameOut, (original_modification_time, original_modification_time))

    if not os.path.exists(filenameOut):
        # Failed to create the compressed file
        with open(log_file, 'a') as f:
            f.write(f"Failed to create compressed file for: {filename}\n")
        return

    # Check file sizes and decide which to keep
    original_size = os.path.getsize(filename)
    compressed_size = os.path.getsize(filenameOut)

    if original_size < compressed_size:
        shutil.copy2(filename, filenameOut)  # Copy original to output folder
        os.remove(filenameOut)  # Remove the larger compressed file

    if deleteOriginals:
        # Ensure the target directory exists
        os.makedirs(moved_folder, exist_ok=True)
        try:
            shutil.move(filename, moved_folder)
        except Exception as e:
            with open(log_file, 'a') as f:
                f.write(f"Error moving {filename} to {moved_folder}: {e}\n")
        else:
            with open(log_file, 'a') as f:
                f.write(f"Moved original file: {filename}\n")

def process_video(video_path, output_folder, moved_folder):
    filename = str(video_path)
    filenameOut = os.path.join(output_folder, f'{video_path.stem}.webm')

    # Get video dimensions
    width, height = get_video_dimensions(filename)
    if width is None or height is None:
        return

    # Determine scale parameters to maintain aspect ratio
    if width > height:  # Landscape or square
        scale = f"640:-2" if width > 640 else f"{width}:{height}"
    else:  # Portrait
        scale = f"-2:640" if height > 640 else f"{width}:{height}"

    try:
        # FFmpeg command for converting to WebM
        ffmpeg_command = [
            "ffmpeg", "-i", filename, "-vf", f"scale={scale}",
            "-c:v", vcodec_webm, "-crf", crf_webm, "-b:v", "1M", "-c:a", acodec_webm,
            filenameOut
        ]
        
        subprocess.check_call(ffmpeg_command)
    except subprocess.CalledProcessError as e:
        with open(log_file, 'a') as f:
            f.write(f"Error compressing {filename}: {e}\n")
        return

    # Compare file sizes
    original_size = os.path.getsize(filename)
    compressed_size = os.path.getsize(filenameOut)

    if compressed_size >= original_size:
        # Delete the compressed file and copy the original to the output folder
        os.remove(filenameOut)
        shutil.copy(filename, filenameOut)
        with open(log_file, 'a') as f:
            f.write(f"Original file is smaller or equal in size, copying original: {filename}\n")
    else:
        with open(log_file, 'a') as f:
            f.write(f"Compressed file is smaller, keeping compressed: {filename}\n")

    # Set modification date
    original_modification_time = os.path.getmtime(filename)
    os.utime(filenameOut, (original_modification_time, original_modification_time))

    if deleteOriginals:
        # Ensure the target directory exists
        os.makedirs(moved_folder, exist_ok=True)
        try:
            shutil.move(filename, moved_folder)
        except Exception as e:
            with open(log_file, 'a') as f:
                f.write(f"Error moving {filename} to {moved_folder}: {e}\n")
        else:
            with open(log_file, 'a') as f:
                f.write(f"Moved original file: {filename}\n")

def main():
    # Clear console
    clear_console()

    # Input directory path
    input_path = input("Enter the directory path: ")
    input_folder_name = os.path.basename(os.path.normpath(input_path))

    # Set output and backup folders based on input folder name
    output_folder = f"{input_folder_name}_compressed"
    moved_folder = f"{input_folder_name}_originals_backup"

    # Ensure the output and backup directories exist
    os.makedirs(output_folder, exist_ok=True)
    os.makedirs(moved_folder, exist_ok=True)

    # Process files in the directory
    with open(log_file, 'a') as f:
        f.write("Conversion log:\n")

    for file in os.listdir(input_path):
        file_path = os.path.join(input_path, file)
        if os.path.isfile(file_path):
            if file.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                process_image(Path(file_path), output_folder, moved_folder)
            elif file.lower().endswith(('.mp4', '.mov', '.avi', '.webm','.m4v')):
                process_video(Path(file_path), output_folder, moved_folder)

if __name__ == "__main__":
    main()