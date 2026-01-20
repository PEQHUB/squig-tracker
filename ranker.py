import json, requests, pandas as pd, numpy as np, io, os, time
from scipy.interpolate import interp1d

# --- SETTINGS ---
DB_FILE = "database.json"
LIBRARY_DIR = "library"
TARGET_FREQ = np.geomspace(20, 20000, 500)

def load_target_for_type(hp_type):
    """Loads either the IE or OE target file."""
    filename = "target_inear.txt" if hp_type == "inear" else "target_overear.txt"
    if not os.path.exists(filename):
        return np.zeros(len(TARGET_FREQ))
    data = pd.read_csv(filename, sep=None, engine='python', names=['f', 'a'])
    return interp1d(data['f'], data['a'], kind='linear', fill_value="extrapolate")(TARGET_FREQ)

def get_file_and_category(reviewer, model_name):
    """
    Checks common Squiglink paths to find the file and categorize the device.
    """
    # Map the Squiglink path to our category
    path_map = {
        "iems": "inear",
        "earbuds": "inear",
        "headphones": "overear"
    }
    
    for path, category in path_map.items():
        url = f"https://{reviewer}.squig.link/{path}/data/phone_book.json"
        try:
            res = requests.get(url, timeout=3).json()
            
            # Recursive search within the JSON
            def find_in_json(obj):
                if isinstance(obj, list):
                    for item in obj:
                        res = find_in_json(item)
                        if res: return res
                elif isinstance(obj, dict):
                    if obj.get('name') == model_name:
                        return obj.get('file')
                    for v in obj.values():
                        res = find_in_json(v)
                        if res: return res
                return None

            file_id = find_in_json(res)
            if file_id:
                return file_id, category
        except:
            continue
    return None, "unknown"

def main():
    with open(DB_FILE, "r") as f:
        database = json.load(f)

    rankings = []

    for reviewer, models in database.items():
        if reviewer == "last_sync": continue
        
        for model in models:
            file_id, category = get_file_and_category(reviewer, model)
            
            if file_id and category != "unknown":
                # Create categorized directory: library/inear/reviewer/
                save_dir = os.path.join(LIBRARY_DIR, category, reviewer)
                os.makedirs(save_dir, exist_ok=True)
                
                # Download and Standardize
                raw_url = f"https://{reviewer}.squig.link/data/{file_id}.txt"
                try:
                    r = requests.get(raw_url, timeout=5)
                    if r.status_code == 200:
                        df = pd.read_csv(io.StringIO(r.text), sep=None, engine='python', names=['f', 'a']).dropna()
                        std_amps = interp1d(df['f'], df['a'], kind='linear', fill_value="extrapolate")(TARGET_FREQ)
                        
                        # Save local standardized CSV
                        pd.DataFrame({'freq': TARGET_FREQ, 'amp': std_amps}).to_csv(
                            os.path.join(save_dir, f"{file_id}.csv"), index=False
                        )
                        
                        # Calculate PPI using the correct category target
                        target_amp = load_target_for_type(category)
                        score = get_harman_score(TARGET_FREQ, std_amps, target_amp)
                        
                        rankings.append({
                            "Model": model,
                            "Category": category,
                            "Reviewer": reviewer,
                            "Score": score
                        })
                except: continue

    # Output separate CSVs for In-Ear and Over-Ear
    full_df = pd.DataFrame(rankings)
    for cat in ["inear", "overear"]:
        cat_df = full_df[full_df['Category'] == cat].sort_values(by="Score", ascending=False)
        cat_df.to_csv(f"rankings_{cat}.csv", index=False)
