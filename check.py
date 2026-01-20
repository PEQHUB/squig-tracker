import requests
import json
import os
import urllib.parse
from datetime import datetime

# The script will now automatically add found subdomains to this list
SUBDOMAINS = [
    "crinacle", "superreview", "hbb", "precog", "timmyv", "aftersound", 
    "paulwasabii", "vortexreviews", "tonedeafmonk", "rg", "nymz", 
    "gadgetrytech", "eliseaudio", "den-fi", "achoreviews", "aden", "adri-n", 
    "animagus", "ankramutt", "arc", "atechreviews", "arn", "audioamigo", 
    "theaudiostore", "awsmdanny", "bakkwatan", "banzai1122", "bassyalexander", 
    "bassaudio", "bedrock", "boizoff", "breampike", "bryaudioreviews", 
    "bukanaudiophile", "csi-zone", "dchpgall", "dhrme", "dl", "doltonius", 
    "ducbloke", "ekaudio", "fahryst", "enemyspider", "eplv", "flare", 
    "foxtoldmeso", "freeryder05", "hadoe", "harpo", "hore", "hu-fi", 
    "ianfann", "ideru", "iemocean", "iemworld", "isaiahse", "jacstone", 
    "jaytiss", "joshtbvo", "kazi", "kr0mka", "lestat", "listener", 
    "loomynarty", "lown-fi", "melatonin", "mmagtech", "musicafe", "obodio", 
    "practiphile", "pw", "ragnarok", "recode", "regancipher", "riz", "smirk", 
    "soundignity", "suporsalad", "tgx78", "therollo9", "scboy", "seanwee", 
    "silicagel", "sl0the", "soundcheck39", "tanchjim", "tedthepraimortis", 
    "treblewellxtended", "vsg", "yanyin", "yoshiultra", "kuulokenurkka", 
    "sai", "earphonesarchive"
]

OVERRIDES = {
    "crinacle": "https://graph.hangout.audio/iem/711/data/phone_book.json",
    "superreview": "https://squig.link/data/phone_book.json",
    "den-fi": "https://ish.squig.link/data/phone_book.json",
    "paulwasabii": "https://pw.squig.link/data/phone_book.json"
}

DB_FILE = "database.json"
HISTORY_FILE = "history.json"

def get_discovered_subdomains():
    """Fetches all registered .squig.link subdomains from public logs (crt.sh)."""
    try:
        print("Discovering new Squiglink reviewers via crt.sh...")
        url = "https://crt.sh/?q=%.squig.link&output=json"
        response = requests.get(url, timeout=25)
        if response.status_code != 200: return []
        
        data = response.json()
        discovered = set()
        for entry in data:
            name = entry['common_name'].lower()
            name = name.replace('*.', '')
            if name.endswith('.squig.link') and name not in ['squig.link', 'www.squig.link']:
                prefix = name.split('.')[0]
                discovered.add(prefix)
        return list(discovered)
    except Exception as e:
        print(f"Discovery skipped: {e}")
        return []

def fetch_data(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return None

def log_item(link_domain, name, file_id, database, sub_key, new_finds):
    if not name or not isinstance(name, str): return
    clean_name = name.strip()
    final_file_id = file_id[0] if isinstance(file_id, list) else file_id
    
    if clean_name not in database[sub_key]:
        database[sub_key].append(clean_name)
        new_finds.append({
            "reviewer": sub_key.capitalize(),
            "item": clean_name,
            "date": datetime.now().strftime("%b %d, %H:%M"),
            "link": f"https://{link_domain}/?share={urllib.parse.quote(str(final_file_id))}"
        })

def parse_recursive(obj, link_domain, database, sub_key, new_finds, brand_context=""):
    if isinstance(obj, dict) and 'phones' in obj:
        current_brand = obj.get('name', brand_context)
        for phone in obj.get('phones', []):
            parse_recursive(phone, link_domain, database, sub_key, new_finds, current_brand)
    elif isinstance(obj, dict) and 'name' in obj:
        model_name = obj['name']
        file_id = obj.get('file', model_name)
        full_label = f"{brand_context} {model_name}".strip()
        log_item(link_domain, full_label, file_id, database, sub_key, new_finds)
    elif isinstance(obj, dict):
        for key, val in obj.items():
            if isinstance(val, (dict, list)):
                parse_recursive(val, link_domain, database, sub_key, new_finds, brand_context)
            else:
                log_item(link_domain, val, key, database, sub_key, new_finds)
    elif isinstance(obj, list):
        for item in obj:
            parse_recursive(item, link_domain, database, sub_key, new_finds, brand_context)

def run_check():
    # Load existing data
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            try: database = json.load(f)
            except: database = {}
    else:
        database = {}

    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            try: history = json.load(f)
            except: history = []
    else:
        history = []

    new_finds = []

    # --- STEP 1: Discovery ---
    # Merge hardcoded SUBDOMAINS with whatever exists in database.json and new crt.sh finds
    discovered = get_discovered_subdomains()
    all_targets = list(set(SUBDOMAINS + list(database.keys()) + discovered))
    
    # Remove 'last_sync' from targets if it exists
    all_targets = [t for t in all_targets if t != 'last_sync']

    # --- STEP 2: Scrape ---
    for sub in all_targets:
        print(f"Checking {sub}...")
        if sub not in database:
            database[sub] = []
        
        data = None
        link_domain = ""

        if sub in OVERRIDES:
            target_url = OVERRIDES[sub]
            data = fetch_data(target_url)
            if data:
                link_domain = target_url.replace("https://", "").split('/data/')[0]

        if not data:
            # Try various standard Squiglink paths
            for path in ["", "iems", "earbuds", "headphones"]:
                base = f"{sub}.squig.link/{path}".strip('/')
                url = f"https://{base}/data/phone_book.json"
                fetched = fetch_data(url)
                if fetched:
                    data = fetched
                    link_domain = base
                    break
        
        if data:
            parse_recursive(data, link_domain, database, sub, new_finds)

    # --- STEP 3: Save results ---
    # We update the sync time so the website knows we just finished a check
    database["last_sync"] = datetime.now().isoformat()

    if new_finds:
        print(f"Success! Found {len(new_finds)} new items.")
        history = new_finds + history 
        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=4)
            
    with open(DB_FILE, "w") as f:
        json.dump(database, f, indent=4)

if __name__ == "__main__":
    run_check()
