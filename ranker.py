import json, requests, pandas as pd, numpy as np, io, os, time
from scipy.interpolate import interp1d

# --- SETTINGS ---
DB_FILE = "database.json"
LIBRARY_DIR = "library"
COMP_FILE = "DDComp.txt"
TARGET_FREQ = np.geomspace(20, 20000, 500)

# Rig Mapping
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
    """Calculates Harman Predicted Preference Rating (PPR)."""
    try:
        # Standard calculation range: 20Hz - 10kHz for IEMs
        error = measured_amps - target_amps
        error -= np.mean(error) # Level normalization
        
        # Calculate Slope (g) and Standard Deviation (s)
        log_freq = np.log10(TARGET_FREQ)
        slope, _ = np.polyfit(log_freq, error, 1)
        sd_eb = np.std(error, ddof=1)
        
        # Formula: 114.39 - 0.6*SD - 26.3*abs(Slope)
        score = 114.39 - (0.6 * sd_eb) - (26.3 * abs(slope))
        return max(0, min(100, round(score, 2)))
    except: return 0

def main():
    if not os.path.exists(DB_FILE): return print("Run check.py first.")
    with open(DB_FILE, "r") as f: database = json.load(f)

    # 1. Pre-load DDComp (only applied to 711 rigs)
    dd_comp = load_interpolation(COMP_FILE)
    rankings = []

    for reviewer, models in database.items():
        if reviewer == "last_sync": continue
        meta = REVIEWER_META.get(reviewer, {"rig": "711", "pinna": "standard"})
        
        for model in models:
            file_id, category = get_file_and_category(reviewer, model)
            if not file_id: continue

            # Construct path with hardware context
            local_path = os.path.join(LIBRARY_DIR, meta['rig'], meta['pinna'], category, reviewer, f"{file_id}.csv")
            
            # Library Check
            if os.path.exists(local_path):
                std_amps = pd.read_csv(local_path)['amp'].values
            else:
                std_amps = download_and_standardize(reviewer, file_id, local_path)
            
            if std_amps is not None:
                # 2. CORE LOGIC: Normalize 711 to 5128 approximation
                if meta['rig'] == "711":
                    std_amps = std_amps - dd_comp

                # 3. Target Selection
                # Since 711 is now compensated, we use 5128 targets for both 711 and 5128 rigs
                target_key = "5128" if meta['rig'] in ["711", "5128"] else meta['rig']
                target_file = f"target_{'ie' if category == 'inear' else 'oe'}_{target_key}_{meta['pinna'] if category == 'overear' else ''}".strip('_') + ".txt"
                target_amps = load_interpolation(target_file)

                score = get_harman_score(std_amps, target_amps)
                rankings.append({
                    "Model": model, "Category": category, "Score": score,
                    "Rig": meta['rig'], "Reviewer": reviewer
                })

    # Export
    df = pd.DataFrame(rankings)
    for cat in ["inear", "overear"]:
        df[df['Category'] == cat].sort_values("Score", ascending=False).to_csv(f"rankings_{cat}.csv", index=False)

def download_and_standardize(reviewer, file_id, local_path):
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

if __name__ == "__main__":
    main()
