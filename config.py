# Constants shared across the application
CRF_WEBM = '47'  # Constant Rate Factor for WebM
WEBP_QUALITY = '90'  # Quality for WebP compression
HIDE_CMD_WINDOWS = False  # Toggle to hide or show command prompt windows
MOVE_ORIGINALS_TO_BACKUP = True  # Flag to move original files to a backup folder after processing
LOG_FILE = 'conversion_log.txt'  # Log file for recording operations
LOG_METADATA = True  # Toggle to enable or disable metadata logging

DEFAULT_SCALE_WIDTH = 640  # Default width for scaling videos
DEFAULT_SCALE_HEIGHT = 640  # Default height for scaling videos
WEBM_BITRATE = '1M'  # Bitrate for WebM compression

USE_THREAD_POOL_FOR_IMAGES = True  # Toggle to use ThreadPoolExecutor for image processing
USE_THREAD_POOL_FOR_VIDEOS = False  # Toggle to use ThreadPoolExecutor for video processing

ENABLE_DEPENDENCY_CHECK = True  # Toggle to enable or disable dependency checks

# Adjust creation flags based on the operating system and toggle
import os
CREATE_NO_WINDOW = 0x08000000 if HIDE_CMD_WINDOWS and os.name == 'nt' else 0
