import os
import shutil

def move_unpaired_files(folder1, folder2, output_folder):
    # Create the output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
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

# Example usage
folder1 = '/storage/emulated/0/UltimateCompress/Compresscp_compressed'
folder2 = '/storage/emulated/0/UltimateCompress/Compresscp_originals_backup'
output_folder = '/storage/emulated/0/UltimateCompress/Aa'

move_unpaired_files(folder1, folder2, output_folder)