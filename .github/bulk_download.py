import os
import requests
import json
import time
from tqdm import tqdm # Run 'pip install tqdm' for a progress bar

# --- CONFIGURATION ---
BASE_DOWNLOAD_DIR = "measurements_library"
DATABASE_FILE = "database.json"

def download_file(url, folder, filename):
    """Downloads a single FR file."""
    path = os.path.join(folder, filename)
    if os.path.exists(path):
        return False # Skip if already exists

    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            with open(path, 'wb') as f:
                f.write(response.content)
            return True
    except:
        pass
    return False

def start_bulk_download():
    # 1. Load your existing monitor database
    if not os.path.exists(DATABASE_FILE):
        print("database.json not found. Run your monitor script first.")
        return
        
    with open(DATABASE_FILE, 'r') as f:
        db = json.load(f)

    # 2. Setup folders
    if not os.path.exists(BASE_DOWNLOAD_DIR):
        os.makedirs(BASE_DOWNLOAD_DIR)

    # 3. Process each reviewer
    # We skip 'last_sync' if it exists in your json
    reviewers = [k for k in db.keys() if k != "last_sync"]

    for sub in reviewers:
        print(f"\nProcessing Reviewer: {sub}")
        reviewer_dir = os.path.join(BASE_DOWNLOAD_DIR, sub)
        os.makedirs(reviewer_dir, exist_ok=True)

        # We need to find where their data lives (handling subfolders like /iems/)
        # We'll try the most common Squiglink paths
        data_found = False
        for path in ["", "iems", "earbuds", "headphones"]:
            base_url = f"https://{sub}.squig.link/{path}".strip('/')
            phonebook_url = f"https://{base_url}/data/phone_book.json"
            
            try:
                res = requests.get(phonebook_url, timeout=10)
                if res.status_code == 200:
                    phonebook = res.json()
                    
                    # Phonebook can be a dict of lists or a flat list
                    # We'll extract all 'file' entries
                    files_to_get = []
                    
                    def extract_files(obj):
                        if isinstance(obj, dict):
                            if 'file' in obj:
                                files_to_get.append(obj['file'])
                            for v in obj.values():
                                extract_files(v)
                        elif isinstance(obj, list):
                            for item in obj:
                                extract_files(item)

                    extract_files(phonebook)
                    
                    print(f"Found {len(files_to_get)} files for {sub}. Starting download...")
                    
                    # Download loop with progress bar
                    for filename in tqdm(files_to_get):
                        # Construct the direct link to the .txt file
                        # Some files already have .txt, some don't
                        ext = "" if filename.endswith(('.txt', '.csv')) else ".txt"
                        file_url = f"https://{base_url}/data/{filename}{ext}"
                        
                        # Use the filename as the local name, making it OS-safe
                        safe_name = "".join([c for c in f"{filename}{ext}" if c.isalnum() or c in (' ', '.', '-', '_')]).strip()
                        download_file(file_url, reviewer_dir, safe_name)
                        
                    data_found = True
                    break
            except Exception as e:
                continue
        
        if not data_found:
            print(f"Could not locate data folder for {sub}")

if __name__ == "__main__":
    start_bulk_download()
