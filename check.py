import requests
import json
import os
import time
import urllib.parse
from datetime import datetime

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

DB_FILE = "database.json"
HISTORY_FILE = "history.json"

def fetch_data(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

def process_item(link_domain, name, share_id, database, sub_key, new_finds):
    encoded_id = urllib.parse.quote(share_id)
    deep_link = f"https://{link_domain}/?share={encoded_id}"

    if name not in database[sub_key]:
        database[sub_key].append(name)
        new_finds.append({
            "reviewer": sub_key.capitalize(),
            "item": name,
            "date": datetime.now().strftime("%b %d, %H:%M"),
            "link": deep_link
        })

def run_check():
    # 1. LOAD DATA
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            database = json.load(f)
    else:
        database = {}

    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            history = json.load(f)
    else:
        history = []

    new_finds = []

    # 2. RUN SCRAPER
    for sub in SUBDOMAINS:
        print(f"Checking {sub}...")
        if sub not in database:
            database[sub] = []
        
        data = None
        link_domain = ""
        paths_to_try = ["", "headphones", "earbuds", "iems"]
        
        for path in paths_to_try:
            base_url = f"https://{sub}.squig.link"
            if path: base_url += f"/{path}"
            
            check_url = f"{base_url}/data/phone_book.json"
            fetched = fetch_data(check_url)
            
            if fetched:
                data = fetched
                link_domain = f"{sub}.squig.link/{path}" if path else f"{sub}.squig.link"
                break
        
        if not data:
            continue
        
        # 3. PARSE DATA
        if isinstance(data, dict):
            for share_id, display_name in data.items():
                if isinstance(display_name, list):
                    for model in display_name:
                        process_item(link_domain, f"{share_id} {model}", model, database, sub, new_finds)
                else:
                    process_item(link_domain, display_name, share_id, database, sub, new_finds)
        elif isinstance(data, list):
            for item in data:
                process_item(link_domain, item, item, database, sub, new_finds)
        
        time.sleep(1)

    # 4. SAVE DATA
    if new_finds:
        print(f"Found {len(new_finds)} new items!")
        # Update history and keep only latest 200
        history = (new_finds + history)[:200]
        
        with open(DB_FILE, "w") as f:
            json.dump(database, f, indent=4)
        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=4)
    else:
        print("No new items found.")

if __name__ == "__main__":
    run_check()
