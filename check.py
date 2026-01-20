import requests
import json
import os
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

OVERRIDES = {
    "crinacle": "https://graph.hangout.audio/iem/711/data/phone_book.json",
    "crinacle5128": "https://graph.hangout.audio/iem/5128/data/phone_book.json",
    "superreview": "https://squig.link/data/phone_book.json",
    "den-fi": "https://ish.squig.link/data/phone_book.json",
    "paulwasabii": "https://pw.squig.link/data/phone_book.json",
    "listener5128": "https://listener800.github.io/5128/data/phone_book.json"
}

# Only specific model series and explicit labels
HP_KEYWORDS = [
    "(OE)", "Headphone", "Over-Ear", "On-Ear", "Closed-back", "Open-back", "Circumaural",
    "HD600", "HD650", "HD800", "HD660", "MDR-Z", "MDR-1", "ATH-M", "LCD-", "DT770", "DT880", "DT990", 
    "DT1990", "DT1770", "Clear", "Utopia", "Elex", "Sundara", "Ananda", "Arya", "Susvara"
]

DB_FILE = "database.json"
HISTORY_FILE = "history.json"

def get_discovered_subdomains():
    try:
        print("Discovering new Squiglink reviewers...")
        url = "https://crt.sh/?q=%.squig.link&output=json"
        response = requests.get(url, timeout=25)
        if response.status_code != 200: return []
        data = response.json()
        discovered = set()
        for entry in data:
            name = entry['common_name'].lower().replace('*.', '')
            if name.endswith('.squig.link') and name not in ['squig.link', 'www.squig.link']:
                discovered.add(name.split('.')[0])
        return list(discovered)
    except Exception: return []

def fetch_data(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200: return response.json()
    except: pass
    return None

def log_item(link_domain, name, file_id, database, sub_key, new_finds):
    if not name or not isinstance(name, str): return
    clean_name = name.strip()
    if sub_key not in database: database[sub_key] = []
    
    final_file_id = file_id[0] if isinstance(file_id, list) else file_id
    current_link = f"https://{link_domain}/?share={urllib.parse.quote(str(final_file_id))}"

    # Check against specific model/label keywords
    is_hp_by_keyword = any(kw.lower() in clean_name.lower() for kw in HP_KEYWORDS)
    
    if is_hp_by_keyword and "headphones" not in current_link:
        current_link += "&type=headphone"

    if current_link not in database[sub_key]:
        database[sub_key].append(current_link)
        new_finds.append({
            "reviewer": sub_key.capitalize(),
            "item": clean_name,
            "date": datetime.now().strftime("%b %d, %H:%M"),
            "link": current_link
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
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            try: database = json.load(f)
            except: database = {}
    else: database = {}

    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            try: history = json.load(f)
            except: history = []
    else: history = []

    new_finds = []

    for sub_name, target_url in OVERRIDES.items():
        print(f"Checking Override: {sub_name}...")
        data = fetch_data(target_url)
        if data:
            domain_part = target_url.replace("https://", "").split('/data/')[0]
            parse_recursive(data, domain_part, database, sub_name, new_finds)

    discovered = get_discovered_subdomains()
    all_targets = list(set(SUBDOMAINS + [k for k in database.keys() if k != 'last_sync'] + discovered))
    
    # Nested paths ensure headphones/5128 directories are found
    SCAN_PATHS = ["", "iems", "headphones", "earbuds", "5128", "headphones/5128", "5128/headphones"]

    for sub in all_targets:
        if sub in OVERRIDES: continue 
        print(f"Checking {sub}...")
        for path in SCAN_PATHS:
            base = f"{sub}.squig.link/{path}".strip('/')
            url = f"https://{base}/data/phone_book.json"
            data = fetch_data(url)
            if data:
                print(f"  > Found data at /{path}")
                parse_recursive(data, base, database, sub, new_finds)

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
