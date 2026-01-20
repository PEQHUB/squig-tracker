import json, requests, pandas as pd, numpy as np, io, os, time
from scipy.interpolate import interp1d

# --- CONFIGURATION ---
DB_FILE = "database.json"
LIBRARY_DIR = "library"
COMP_FILE = "DDComp.txt"
TARGET_FREQ = np.geomspace(20, 20000, 500)
CLEANUP_MODE = True 

# Hardware Mapping
REVIEWER_META = {
    "crinacle": {"rig": "5128", "pinna": "humanoid"},
    "vsg": {"rig": "5128", "pinna": "humanoid"},
    "superreview": {"rig": "711", "pinna": "standard"},
    "oratory1990": {"rig": "45ca", "pinna": "welti"}
}

def load_interpolation(file_path):
    """Generic loader to interpolate any txt/csv to our 500pt grid."""
    if not os.path.exists(file_path):
        return np.zeros(len(TARGET_FREQ))
    try:
        data = pd.read_csv(file_path, sep=None, engine='python', names=['f', 'a'])
        return interp1d(data['f'], data['a'], kind='linear', fill_value="extrapolate")(TARGET_FREQ)
    except: return np.zeros(len(TARGET_FREQ))

def get_harman_score(measured_amps, target_amps):
    """Calculates Harman Predicted Preference Rating."""
    try:
        error = measured_amps - target_amps
        error -= np.mean(error) 
        log_freq = np.log10(TARGET_FREQ)
        slope, _ = np.polyfit(log_freq, error, 1)
        sd_eb = np.std(error, ddof=1)
        score = 114.39 - (0.6 * sd_eb) - (26.3 * abs(slope))
        return max(0, min(100, round(score, 2)))
    except: return 0

def get_file_and_category(reviewer, model_name):
    """Crawl phone_book to find file_id and identify type."""
    path_map = {"iems": "inear", "earbuds": "inear", "headphones": "overear"}
    for folder, category in path_map.items():
        url = f"https://{reviewer}.squig.link/{folder}/data/phone_book.json"
        try:
            res = requests.get(url, timeout=5).json()
            def search(obj):
                if isinstance(obj, list):
                    for i in obj:
                        r = search(i)
                        if r: return r
                elif isinstance(obj, dict):
                    if obj.get('name') == model_name: return obj.get('file')
                    for v in obj.values():
                        r = search(v)
                        if r: return r
                return None
            fid = search(res)
            if fid: return fid, category
        except: continue
    return None, "unknown"

def download_and_standardize(reviewer, file_id, local_path):
    """Downloads and saves standardized FR."""
    url = f"https://{reviewer}.squig.link/data/{file_id}.txt"
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            df = pd.read_csv(io.StringIO(r.text), sep=None, engine='python', names=['f', 'a']).dropna()
            std_amps = interp1d(df['f'], df['a'], kind='linear', fill_value="extrapolate")(TARGET_FREQ)
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            pd.DataFrame({'freq': TARGET_FREQ, 'amp': std_amps}).to_csv(local_path, index=False)
            return std_amps
    except: return None

def validate_library():
    if not os.path.exists(LIBRARY_DIR): return
    for root, _, files in os.walk(LIBRARY_DIR):
        for file in files:
            if file.endswith(".csv"):
                p = os.path.join(root, file)
                try:
                    if os.path.getsize(p) < 100 or len(pd.read_csv(p)) != len(TARGET_FREQ):
                        os.remove(p)
                except: os.remove(p)

def main():
    if not os.path.exists(DB_FILE): return print("Run check.py first.")
    if CLEANUP_MODE: validate_library()

    with open(DB_FILE, "r") as f: database = json.load(f)
    dd_comp = load_interpolation(COMP_FILE)
    rankings = []

    for reviewer, models in database.items():
        if reviewer == "last_sync": continue
        meta = REVIEWER_META.get(reviewer, {"rig": "711", "pinna": "standard"})
        
        for model in models:
            file_id, category = get_file_and_category(reviewer, model)
            if not file_id or category == "unknown": continue

            local_path = os.path.join(LIBRARY_DIR, meta['rig'], meta['pinna'], category, reviewer, f"{file_id}.csv")
            
            if os.path.exists(local_path):
                std_amps = pd.read_csv(local_path)['amp'].values
            else:
                std_amps = download_and_standardize(reviewer, file_id, local_path)
                time.sleep(0.1)
            
            if std_amps is not None:
                if meta['rig'] == "711":
                    std_amps = std_amps - dd_comp

                # Select Target (Using 5128 for compensated 711)
                t_key = "5128" if meta['rig'] == "711" else meta['rig']
                t_file = f"target_{'ie' if category == 'inear' else 'oe'}_{t_key}_{meta['pinna'] if category == 'overear' else ''}".strip('_') + ".txt"
                target_amps = load_interpolation(t_file)

                score = get_harman_score(std_amps, target_amps)
                rankings.append({
                    "Model": model, "Category": category, "Score": score, "Reviewer": reviewer
                })

    df = pd.DataFrame(rankings)
    for cat in ["inear", "overear"]:
        if not df.empty:
            df[df['Category'] == cat].sort_values("Score", ascending=False).to_csv(f"rankings_{cat}.csv", index=False)

if __name__ == "__main__":
    main()
