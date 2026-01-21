import requests
import json
import os
import urllib.parse
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# --- Target Discovery ---
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
    "crinacleHP": "https://graph.hangout.audio/hp/data/phone_book.json",
    "superreview": "https://squig.link/data/phone_book.json",
    "den-fi": "https://ish.squig.link/data/phone_book.json",
    "paulwasabii": "https://pw.squig.link/data/phone_book.json",
    "listener5128": "https://listener800.github.io/5128/data/phone_book.json"
}

# --- Exclusion & Recognition Lists ---
NOT_A_HEADPHONE = ["IEM", "In-Ear", "Monitor", "Earphone", "T10", "Planar IEM"]
HP_SINGLES = ["(OE)", "Over-Ear", "On-Ear", "Closed-back", "Open-back", "Circumaural", "Supra-aural", "HD600", "HD650", "HD800", "HD6XX", "HD560", "HD580", "Sundara", "Ananda", "Susvara", "DT770", "DT880", "DT990", "DT1990", "K701", "K702", "K371", "MDR-7506", "Porta Pro"]
HP_PAIRS = {
    "Dan Clark": ["Stealth", "Expanse", "Ether", "Aeon", "Corina", "DCA"],
    "ZMF": ["Atrium", "Verite", "Aeolus", "Eikon", "Auteur", "Caldera", "Bokeh"],
    "Focal": ["Clear", "Stellia", "Utopia", "Elex", "Radiance", "Bathys", "Hadenys"],
    "Audeze": ["Maxwell", "LCD", "Mobius", "Penrose"],
    "Meze": ["Elite", "Empyrean", "Liric", "109 Pro"]
}
TWS_KEYWORDS = ["Earbud", "TWS", "Wireless", "Buds", "Pods", "True Wireless", "AirPods"]

DB_FILE = "database.json"
HISTORY_FILE = "history.json"

def fetch_data(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        return response.json() if response.status_code == 200 else None
    except: return None

def log_item(link_domain, name, file_id, database, sub_key, new_finds):
    if not name or not isinstance(name, str): return
    clean_name = name.strip()
    name_lower = clean_name.lower()
    
    # Initialize list if sub_key is new, maintaining compatibility with older DB
    if sub_key not in database: database[sub_key] = []
    
    final_file_id = file_id[0] if isinstance(file_id, list) else file_id
    current_link = f"https://{link_domain}/?share={urllib.parse.quote(str(final_file_id))}"

    # Logic categorization
    is_tws = any(kw.lower() in name_lower for kw in TWS_KEYWORDS)
    is_hp_path = "5128" in link_domain or "headphone" in link_domain.lower() or "/hp/" in link_domain
    has_iem_keyword = any(kw.lower() in name_lower for kw in NOT_A_HEADPHONE)
    
    if is_tws:
        current_link += "&type=tws"
    else:
        has_hp_single = any(kw.lower() in name_lower for kw in HP_SINGLES)
        has_hp_pair = any(brand.lower() in name_lower and any(m.lower() in name_lower for m in models) 
                         for brand, models in HP_PAIRS.items())
        is_dedicated_hp = (sub_key == "crinacleHP")
        
        if (is_dedicated_hp or is_hp_path or has_hp_single or has_hp_pair) and not has_iem_keyword:
            if "jaytiss" not in link_domain or (has_hp_single or has_hp_pair):
                current_link += "&type=headphone"

    # Set lookup for performance (converting list to set temporarily)
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

def process_target(sub, database, new_finds):
    """Function to be run in parallel for each subdomain."""
    if sub in OVERRIDES:
        target_url = OVERRIDES[sub]
        data = fetch_data(target_url)
        if data:
            domain_part = target_url.replace("https://", "").split('/data/')[0]
            parse_recursive(data, domain_part, database, sub, new_finds)
    else:
        SCAN_PATHS = ["", "iems", "headphones", "earbuds", "5128", "headphones/5128"]
        for path in SCAN_PATHS:
            base_link = f"{sub}.squig.link/{path}".strip('/')
            url = f"https://{base_link}/data/phone_book.json"
            data = fetch_data(url)
            if data:
                parse_recursive(data, base_link, database, sub, new_finds)
                break # Stop scanning paths once one is found for this sub

def run_check():
    database = {}
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            try: database = json.load(f)
            except: pass

    history = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            try: history = json.load(f)
            except: pass

    new_finds = []
    
    # Merge all unique subdomains to check
    all_targets = list(set(SUBDOMAINS + [k for k in OVERRIDES.keys()] + [k for k in database.keys() if k != 'last_sync']))
    
    # Run network requests in parallel
    with ThreadPoolExecutor(max_workers=10) as executor:
        for sub in all_targets:
            executor.submit(process_target, sub, database, new_finds)

    database["last_sync"] = datetime.now().isoformat()
    
    if new_finds:
        # Sort new finds by name to look cleaner in history
        new_finds.sort(key=lambda x: x['item'])
        history = new_finds + history
        with open(HISTORY_FILE, "w") as f: 
            json.dump(history, f, indent=4)
            
    with open(DB_FILE, "w") as f: 
        json.dump(database, f, indent=4)

if __name__ == "__main__":
    run_check()
