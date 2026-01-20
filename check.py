import requests
import json
import os
import urllib.parse
from datetime import datetime

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
    "superreview": "https://squig.link/data/phone_book.json",
    "den-fi": "https://ish.squig.link/data/phone_book.json",
    "paulwasabii": "https://pw.squig.link/data/phone_book.json",
    "listener5128": "https://listener800.github.io/5128/data/phone_book.json"
}

# --- Massive Over-Ear Keyword List ---
HP_KEYWORDS = [
    "(OE)", "Headphone", "Over-Ear", "On-Ear", "Closed-back", "Open-back", 
    "Circumaural", "Supra-aural", "Full-size", "Cans", "Electrostatic",
    "HD400", "HD450", "HD500", "HD518", "HD555", "HD558", "HD559", "HD560", 
    "HD569", "HD579", "HD580", "HD58X", "HD598", "HD599", "HD600", "HD620", 
    "HD630", "HD650", "HD660", "HD6XX", "HD700", "HD800", "HD820", "Momentum",
    "HE-1", "Orpheus", "HD25", "HD280", "HD300", "HD380", "Sundara", "Ananda", 
    "Arya", "Susvara", "HE400", "HE4XX", "HE5XX", "HE6", "HE1000", "Edition XS", 
    "Jade", "Shangri-La", "Deva", "Audivina", "HE-R9", "HE-R10", "DT770", "DT880", 
    "DT990", "DT1770", "DT1990", "DT700", "DT900", "Amiron", "Custom One", 
    "T1", "T5", "T5p", "Tygr", "MMX 300", "Utopia", "Stellia", "Clear", "Elex", 
    "Elear", "Radiance", "Celestee", "Bathys", "Listen", "Hadenys", "Azurys", 
    "LCD-2", "LCD-3", "LCD-4", "LCD-5", "LCD-X", "LCD-XC", "LCD-MX4", "LCD-GX", 
    "Maxwell", "Mobius", "Penrose", "MM-500", "MM-100", "CRBN", "ATH-M20", 
    "ATH-M30", "ATH-M40", "ATH-M50", "ATH-M60", "ATH-M70", "ATH-AD", "ATH-A900", 
    "ATH-R70x", "ATH-W", "Air Dynamic", "ATH-AP2000", "MDR-V", "MDR-7506", 
    "MDR-CD900ST", "MDR-M1", "MDR-Z", "MDR-1", "MDR-SA", "WH-1000X", "WH-CH", 
    "WH-XB", "ULT Wear", "MV1", "K121", "K141", "K240", "K271", "K371", "K361", 
    "K550", "K601", "K612", "K701", "K702", "K712", "K7XX", "K812", "K872", 
    "Stealth", "Expanse", "Ether", "Aeon", "Corina", "Voce", "Mad Dog", "Alpha Dog",
    "Atrium", "Verite", "Aeolus", "Eikon", "Auteur", "Caldera", "Bokeh", 
    "Empyrean", "Elite", "Liric", "109 Pro", "99 Classic", "99 Neo", "Diana", 
    "AB-1266", "SR60", "SR80", "SR125", "SR225", "SR325", "RS1", "RS2", "GS1000", 
    "QuietComfort", "QC35", "QC45", "QC Ultra", "AirPods Max", "Austrian Audio Hi-X", 
    "Bowers & Wilkins PX", "Denon AH-D", "Fostex TH", "Fostex T50RP", "HEDDphone", 
    "Kennerton", "Koss ESP", "Koss Porta Pro", "Koss KSC75", "LSA HP", "Monolith M", 
    "Nectar Hive", "Ollo Audio", "Raal-Requisite", "Rosson", "Sivga SV", 
    "Sivga Luan", "Sonos Ace", "Stax SR", "Verum 1", "Yamaha YH"
]

# --- TWS / Earbud Keywords (Third Category) ---
TWS_KEYWORDS = [
    "Earbud", "TWS", "Wireless", "Buds", "Pods", "True Wireless", "AirPods", 
    "Earfree", "Monk Plus", "Flathead", "LBBS", "EB2S"
]

DB_FILE = "database.json"
HISTORY_FILE = "history.json"

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

    # Logic 1: Detect TWS/Earbud (Highest priority to avoid Bose QC false positives)
    is_tws = any(kw.lower() in clean_name.lower() for kw in TWS_KEYWORDS)
    
    # Logic 2: Detect Over-Ear
    is_hp = any(kw.lower() in clean_name.lower() for kw in HP_KEYWORDS)

    # Apply Tags
    if is_tws:
        current_link += "&type=tws"
    elif is_hp and "headphones" not in current_link:
        # Extra safety: Ensure we aren't tagging something that was just marked as TWS
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

    all_targets = list(set(SUBDOMAINS + [k for k in database.keys() if k != 'last_sync']))
    
    # Deep nested scanning for all rig types
    SCAN_PATHS = ["", "iems", "headphones", "earbuds", "5128", "headphones/5128", "5128/headphones"]

    for sub in all_targets:
        if sub in OVERRIDES: continue 
        print(f"Checking {sub}...")
        for path in SCAN_PATHS:
            base = f"{sub}.squig.link/{path}".strip('/')
            url = f"https://{base}/data/phone_book.json"
            data = fetch_data(url)
            if data:
                parse_recursive(data, base, database, sub, new_finds)

    database["last_sync"] = datetime.now().isoformat()

    if new_finds:
        history = new_finds + history 
        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=4)
            
    with open(DB_FILE, "w") as f:
        json.dump(database, f, indent=4)

if __name__ == "__main__":
    run_check()
