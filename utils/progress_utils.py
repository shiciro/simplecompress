from tqdm import tqdm

def updateProgressBar(total, description):
  return tqdm(
    total=total,
    desc=description,
    bar_format='{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]'  # Updated format to resemble pip
  )
