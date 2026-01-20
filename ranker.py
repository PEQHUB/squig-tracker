import json
import requests
import pandas as pd
import numpy as np
import io
import os
from scipy.interpolate import interp1d
from github import Github

# --- CONFIGURATION ---
DB_FILE = "database.json"
TARGET_CSV = "rankings.csv"
GITHUB_TOKEN = os.getenv("GH_TOKEN")
REPO_NAME = "your_username/your_repo"

# Simplified Harman Target (Interpolated to 20-20kHz)
# In a production environment, load this from a CSV
TARGET_FREQ = np.geomspace(20, 20000, 500)
# Mock Harman Target Curve (flat with bass boost & ear gain)
TARGET_AMP = np.zeros(500) 

def get_harman_score(freqs, amps):
    """Calculates Harman PPI based on Error SD and Slope."""
    try:
        interp = interp1d(freqs, amps, kind='linear', fill_value="extrapolate")
        resampled_amp = interp(TARGET_FREQ)
        
        error = resampled_amp - TARGET_AMP
        error -= np.mean(error) # Normalization
        
        sd_eb = np.std(error, ddof=1)
        log_freqs = np.log10(TARGET_FREQ)
        slope, _ = np.polyfit(log_freqs, error, 1)
        
        score = 114.39 - (0.6 * sd_eb) - (26.3 * abs(slope))
        return max(0, min(100, round(score, 2)))
    except:
        return 0

def find_file_id(reviewer, model_name):
    """Re-fetches the phone_book for a reviewer to find the file_id for a name."""
    url = f"https://{reviewer}.squig.link/data/phone_book.json"
    try:
        res = requests.get(url, timeout=5).json()
        # Flatten the nested Squiglink JSON to find the model
        def search(obj):
            if isinstance(obj, list):
                for item in obj:
                    res = search(item)
                    if res: return res
            elif isinstance(obj, dict):
                if obj.get('name') == model_name:
                    return obj.get('file')
                for k, v in obj.items():
                    res = search(v)
                    if res: return res
            return None
        return search(res)
    except:
        return None

def main():
    if not os.path.exists(DB_FILE):
        return print("Error: database.json not found.")

    with open(DB_FILE, "r") as f:
        database = json.load(f)

    rankings = []
    
    for reviewer, models in database.items():
        if reviewer == "last_sync" or not isinstance(models, list): continue
        
        print(f"Processing {reviewer}...")
        for model in models[:10]: # Limit for speed
            file_id = find_file_id(reviewer, model)
            if not file_id: continue
            
            # Fetch raw FR data
            fr_url = f"https://{reviewer}.squig.link/data/{file_id}.txt"
            fr_res = requests.get(fr_url, timeout=5)
            if fr_res.status_code == 200:
                data = pd.read_csv(io.StringIO(fr_res.text), sep=None, engine='python', names=['f', 'a']).dropna()
                score = get_harman_score(data['f'].values, data['a'].values)
                
                rankings.append({
                    "Model": model,
                    "Reviewer": reviewer,
                    "PPI_Score": score
                })

    # Save and Upload
    df = pd.DataFrame(rankings).sort_values(by="PPI_Score", ascending=False)
    df.to_csv(TARGET_CSV, index=False)
    print(f"Saved {len(df)} rankings to {TARGET_CSV}")

    # GitHub Logic
    if GITHUB_TOKEN:
        g = Github(GITHUB_TOKEN)
        repo = g.get_user().get_repo(REPO_NAME)
        with open(TARGET_CSV, "r") as f:
            content = f.read()
        try:
            old_file = repo.get_contents(TARGET_CSV)
            repo.update_file(old_file.path, "Update Rankings", content, old_file.sha)
        except:
            repo.create_file(TARGET_CSV, "Initial Ranking", content)

if __name__ == "__main__":
    main()
