from tqdm import tqdm

def updateProgressBar(total, description):
  return tqdm(total=total, desc=description, bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]')
