import os
import shutil

def main(): 
    # cleanup all backup folders created from visualise file structure migration
    base_folder = "poppunk_output"
    all_backup_output_folders = [
        os.path.join(base_folder, item)
        for item in os.listdir(base_folder)
        if os.path.isdir(os.path.join(base_folder, item)) and item.endswith("backup")
    ]
    
    for folder in all_backup_output_folders:
        if os.path.exists(folder):
            try:
                shutil.rmtree(folder)
                print(f"Successfully removed: {folder}")
            except Exception as e:
                print(f"Error removing {folder}: {e}")
        else:
            print(f"Folder not found: {folder}")
        
    
    
if __name__ == "__main__":
    main()