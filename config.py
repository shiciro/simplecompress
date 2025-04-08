# Constants shared across the application
CRF_WEBM = '47'  # Constant Rate Factor for WebM
WEBP_QUALITY = '90'  # Quality for WebP compression
HIDE_CMD_WINDOWS = False  # Toggle to hide or show command prompt windows
MOVE_ORIGINALS_TO_BACKUP = True  # Flag to move original files to a backup folder after processing
LOG_FILE = 'conversion_log.txt'  # Log file for recording operations

# Adjust creation flags based on the operating system and toggle
import os
CREATE_NO_WINDOW = 0x08000000 if HIDE_CMD_WINDOWS and os.name == 'nt' else 0
