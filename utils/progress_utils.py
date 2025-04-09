import logging  # Import logging module
from tqdm import tqdm

def updateProgressBar(total, description):
  logging.info('Progress bar updated')  # Log progress bar update
  return tqdm(
    total=total,
    desc=description,
    bar_format='{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]'  # Updated format to resemble pip
  )
