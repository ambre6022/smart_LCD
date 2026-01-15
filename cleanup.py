import os
import sqlite3
import shutil

def cleanup():
    print("Starting Project Cleanup...")
    
    # Delete database
    if os.path.exists('database.db'):
        os.remove('database.db')
        print("Done: Database deleted")
    
    # Clear shared_media folders
    folders = ['shared_media/images', 'shared_media/videos', 'shared_media/queue']
    for folder in folders:
        if os.path.exists(folder):
            for filename in os.listdir(folder):
                file_path = os.path.join(folder, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print(f'Failed to delete {file_path}. Reason: {e}')
            print(f"Done: Cleared {folder}")
    
    print("Cleanup Complete! You can now start fresh.")

if __name__ == "__main__":
    cleanup()
