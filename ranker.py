import json
import requests
import pandas as pd
import numpy as np
import io
import os
from github import Github # pip install PyGithub

# --- CONFIG ---
DB_FILE = "database.json"
GITHUB_TOKEN = os.getenv("GH_TOKEN") # Set this in your environment variables
REPO_NAME = "your_username/your_repo"
OUTPUT_FILE = "rankings.csv"

# Standard Harman Target Frequencies (truncated for example)
# In practice, you'll want the full 20-20kHz 1/12th octave points
TARGET_FREQS = np.geomspace(20, 20000, 400) 

def fetch_raw_fr(reviewer, file_id):
    """Fetches the actual text file containing freq/amplitude data."""
    # Constructing the raw data URL based on Squiglink patterns
    url = f"https://{reviewer}.squig.link/data/{file_id}.txt"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            # Parse the .txt (usually Tab or Space separated)
            df = pd.read_csv(io.StringIO(response.text), sep=None, engine='python', names=['freq', 'amp'])
            return df
    except Exception:
        return None

def calculate_harman_ppi(fr_df):
    """
    Placeholder for the Harman Listener Preference Model.
    This converts FR data into a 0-100 score.
    """
    if fr_df is None or fr_df.empty: return 0
    
    # 1. Interpolate fr_df to match TARGET_FREQS
    # 2. Subtract Harman Target values
    # 3. Apply the Preference Rating Formula:
    # Score = 114.39 - (0.6 * SD_of_Error) - (26.3 * Slope_of_Error) ... etc
    
    # Return a dummy score for now
    return round(np.random.uniform(50, 95), 2)

def main():
    if not os.path.exists(DB_FILE):
        print("Database not found. Run check.py first.")
        return

    with open(DB_FILE, "r") as f:
        database = json.load(f)

    results = []

    # Iterate through reviewers and their items
    for reviewer, items in database.items():
        if reviewer == "last_sync": continue
        
        print(f"Ranking items for {reviewer}...")
        for item_name in items[:5]: # Limit to 5 for testing
            # Note: You'll need to modify check.py to save the file_id 
            # into the DB to make this fetch work reliably.
            fr_data = fetch_raw_fr(reviewer, item_name.replace(" ", "_")) 
            score = calculate_harman_ppi(fr_data)
            
            results.append({
                "Reviewer": reviewer,
                "Model": item_name,
                "Harman_Score": score
            })

    # Create CSV
    df_ranks = pd.DataFrame(results).sort_values(by="Harman_Score", ascending=False)
    df_ranks.to_csv(OUTPUT_FILE, index=False)

    # --- GitHub Upload ---
    if GITHUB_TOKEN:
        g = Github(GITHUB_TOKEN)
        repo = g.get_user().get_repo(REPO_NAME)
        
        with open(OUTPUT_FILE, "r") as f:
            content = f.read()
            
        try:
            contents = repo.get_contents(OUTPUT_FILE)
            repo.update_file(contents.path, "Update Rankings", content, contents.sha)
        except:
            repo.create_file(OUTPUT_FILE, "Initial Rankings", content)
        print("Upload complete!")

if __name__ == "__main__":
    main()
