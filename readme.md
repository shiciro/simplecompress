### **UltimateCompress - README**

---

## **Overview**

**UltimateCompress** is a Python-based tool designed to compress images and videos efficiently. It supports various image and video formats and ensures that the compressed files maintain a balance between quality and size. The tool also provides options to back up original files, handle unpaired files, resolve file conflicts during the compression process, and toggle multithreading for image and video processing.

---

## **Features**

- **Image Compression**:
  - Converts images to the WebP format for better compression.
  - Supports `.jpg`, `.jpeg`, `.png`, and `.webp` formats.
  - Retains metadata for `.png` files using `exiftool`.

- **Video Compression**:
  - Converts videos to the WebM format using the `libvpx` codec.
  - Supports `.mp4`, `.mov`, `.avi`, `.webm`, and `.m4v` formats.
  - Automatically adjusts video resolution to a maximum of 640 pixels while maintaining the aspect ratio.

- **Backup and Cleanup**:
  - Moves original files to a backup folder after compression (optional).
  - Handles unpaired files by moving them to a separate folder.

- **Conflict Resolution**:
  - Detects and resolves file name conflicts by moving conflicting files to a dedicated `_conflict` folder.

- **Logging**:
  - Logs all operations, including successes, errors, and conflict resolutions, to a `conversion_log.txt` file.

- **Multithreading**:
  - Processes multiple files simultaneously using Python's `ThreadPoolExecutor` for faster execution.
  - Configurable toggles to enable or disable multithreading for image and video processing.

---

## **Requirements**

Before running the script, ensure you have the following installed:

1. **Python**: Version 3.6 or higher.
2. **Dependencies**:
   - `Pillow` (for image processing)
   - `ffmpeg` (for video compression)
   - `cwebp` (for WebP image compression)
   - `exiftool` (for handling metadata in `.png` files)

---

## **Installation**

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/your-username/UltimateCompress.git
   cd UltimateCompress
   ```

2. **Install Python Dependencies**:
   ```bash
   pip install pillow
   ```

3. **Install External Tools**:
   - **FFmpeg**: [Download and install FFmpeg](https://ffmpeg.org/download.html).
   - **cwebp**: [Download and install cwebp](https://developers.google.com/speed/webp/download).
   - **ExifTool**: [Download and install ExifTool](https://exiftool.org/).

4. **Verify Installation**:
   Ensure the tools are accessible from the command line:
   ```bash
   ffmpeg -version
   cwebp -version
   exiftool -ver
   ```

---

## **Usage**

1. **Run the Script**:
   Open a terminal, navigate to the script directory, and run:
   ```bash
   python compress.py
   ```

2. **Provide the Input Directory**:
   When prompted, enter the path to the folder containing the images and videos you want to compress. For example:
   ```
   Enter the directory path: D:\MyMedia
   ```

3. **Output Folders**:
   The script will create the following folders in the same directory as the input folder:
   - `<input_folder>_compressed`: Contains the compressed files.
   - `<input_folder>_originals_backup`: Contains the original files (if deletion is enabled).
   - `<input_folder>_unpaired`: Contains unpaired files that could not be processed.
   - `<input_folder>_conflict`: Contains conflicting files that were moved during processing.

4. **Check the Log File**:
   After the script completes, review the `conversion_log.txt` file for details about the operations performed, including any errors or conflicts.

---

## **How It Works**

1. **Image Compression**:
   - The script converts supported image files to the WebP format using the `cwebp` tool.
   - For `.png` files, metadata is preserved using `exiftool`.
   - If the compressed file is larger than the original, the original file is retained.

2. **Video Compression**:
   - The script converts supported video files to the WebM format using `ffmpeg`.
   - The resolution is adjusted to a maximum of 640 pixels while maintaining the aspect ratio.
   - If the compressed file is larger than the original, the original file is retained.

3. **Backup and Cleanup**:
   - Original files are moved to a backup folder if the `MOVE_ORIGINALS_TO_BACKUP` flag is enabled.
   - Unpaired files (files without matching counterparts in the output folder) are moved to a separate folder.

4. **Conflict Resolution**:
   - If a file with the same name already exists in the output or backup folder, the conflicting file is moved to a `_conflict` folder to avoid overwriting.

5. **Logging**:
   - All operations, including successes, errors, and conflict resolutions, are logged in the `conversion_log.txt` file for easy troubleshooting.

---

## **Example**

### **Input Folder Structure**:
```
D:\MyMedia
├── image1.jpg
├── image2.png
├── video1.mp4
├── video2.mov
```

### **Output Folder Structure** (after running the script):
```
D:\MyMedia
├── MyMedia_compressed
│   ├── image1.webp
│   ├── image2.webp
│   ├── video1.webm
│   ├── video2.webm
├── MyMedia_originals_backup
│   ├── image1.jpg
│   ├── image2.png
│   ├── video1.mp4
│   ├── video2.mov
├── MyMedia_unpaired
├── MyMedia_conflict
├── conversion_log.txt
```

---

## **Configuration**

The script can be customized by modifying the constants in the `config.py` file:

- **`WEBP_QUALITY`**: Defines the quality of WebP image compression. Higher values result in better quality but larger file sizes. *(Default: `'90'`)*
- **`V_CODEC_WEBM`**: Specifies the video codec used for WebM compression. *(Default: `'libvpx'`)*
- **`A_CODEC_WEBM`**: Specifies the audio codec used for WebM compression. *(Default: `'libvorbis'`)*
- **`CRF_WEBM`**: Sets the Constant Rate Factor for WebM compression, controlling the balance between quality and file size. *(Default: `'47'`)*
- **`MOVE_ORIGINALS_TO_BACKUP`**: When set to `True`, original files are moved to a backup folder after compression. *(Default: `True`)*

To apply these changes, edit the `config.py` file in the project directory and adjust the values as needed.


---

## **Troubleshooting**

1. **Command Not Found**:
   - Ensure `ffmpeg`, `cwebp`, and `exiftool` are installed and added to your system's PATH.

2. **Permission Denied**:
   - Ensure you have read/write permissions for the input and output directories.

3. **File Not Compressed**:
   - Check the `conversion_log.txt` file for error messages.

4. **File Conflicts**:
   - Conflicting files are moved to a `_conflict` folder. Check this folder for details.

---

## **Contributing**

Contributions are welcome! If you find a bug or have a feature request, feel free to open an issue or submit a pull request.

---

## **License**

This project is licensed under the MIT License. See the `LICENSE` file for details.

---

## **Acknowledgments**

- **FFmpeg**: For video compression.
- **cwebp**: For WebP image compression.
- **ExifTool**: For handling metadata in `.png` files.
- **Pillow**: For image processing in Python.

---

