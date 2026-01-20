import json, requests, pandas as pd, numpy as np, io, os, time
from scipy.interpolate import interp1d
from github import Github

# --- SETTINGS ---
DB_FILE = "database.json"
LIBRARY_DIR = "library"
TARGET_FREQ = np.geomspace(20, 20000, 500)

def get_local_path(reviewer, file_id, category):
    """Constructs the local path for a standardized file."""
    return os.path.join(LIBRARY_DIR, category, reviewer, f"{file_id}.csv")

def main():
    if not os.path.exists(DB_FILE): return print("Run check.py first.")
    with open(DB_FILE, "r") as f: database = json.load(f)

    rankings = []
    
    # Load targets once at start to save memory
    targets = {
        "inear": load_target_for_type("inear"),
        "overear": load_target_for_type("overear")
    }

    for reviewer, models in database.items():
        if reviewer == "last_sync": continue
        print(f"Checking {reviewer}...")

        for model in models:
            # 1. Identify File & Category
            file_id, category = get_file_and_category(reviewer, model)
            if not file_id or category == "unknown": continue
            
            local_file = get_local_path(reviewer, file_id, category)
            std_amps = None

            # 2. LOCAL LIBRARY CHECK
            if os.path.exists(local_file):
                # Instant Load: Skip Network request
                std_amps = pd.read_csv(local_file)['amp'].values
            else:
                # Download and Standardize (New Item)
                print(f"  [New] Downloading {model}...")
                std_amps = download_and_standardize(reviewer, file_id, local_file)
                time.sleep(0.1) # Rate limiting

            # 3. Process Ranking
            if std_amps is not None:
                score = get_harman_score(TARGET_FREQ, std_amps, targets[category])
                rankings.append({
                    "Model": model,
                    "Category": category,
                    "Reviewer": reviewer,
                    "Score": score
                })

    # 4. Save and Upload Results
    save_and_upload_results(rankings)

def download_and_standardize(reviewer, file_id, local_path):
    """Downloads raw data and saves to the local library."""
    url = f"https://{reviewer}.squig.link/data/{file_id}.txt"
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            df = pd.read_csv(io.StringIO(r.text), sep=None, engine='python', names=['f', 'a']).dropna()
            # Standardize to 500 points
            std_amps = interp1d(df['f'], df['a'], kind='linear', fill_value="extrapolate")(TARGET_FREQ)
            
            # Create directories and save CSV
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            pd.DataFrame({'freq': TARGET_FREQ, 'amp': std_amps}).to_csv(local_path, index=False)
            return std_amps
    except: pass
    return None
