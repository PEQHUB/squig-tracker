import requests
import json
import os
from datetime import datetime

SUBDOMAINS = [
    # The Essentials
    "crinacle", "superreview", "hbb", 
    
    # Major Reviewers & Databases
    "precog", "timmyv", "aftersound", "paulwasabii", "vortexreviews", 
    "tonedeafmonk", "rg", "nymz", "gadgetrytech", "eliseaudio", "den-fi",
    
    # Community & Niche Databases (A-Z)
    "achoreviews", "aden", "adri-n", "animagus", "ankramutt", "arc", 
    "atechreviews", "arn", "audioamigo", "theaudiostore", "awsmdanny", 
    "bakkwatan", "banzai1122", "bassyalexander", "bassaudio", "bedrock", 
    "boizoff", "breampike", "bryaudioreviews", "bukanaudiophile", "csi-zone", 
    "dchpgall", "dhrme", "dl", "doltonius", "ducbloke", "ekaudio", "fahryst", 
    "enemyspider", "eplv", "flare", "foxtoldmeso", "freeryder05", "hadoe", 
    "harpo", "hore", "hu-fi", "ianfann", "ideru", "iemocean", "iemworld", 
    "isaiahse", "jacstone", "jaytiss", "joshtbvo", "kazi", "kr0mka", 
    "lestat", "listener", "loomynarty", "lown-fi", "melatonin", "mmagtech", 
    "musicafe", "obodio", "practiphile", "pw", "ragnarok", "recode", 
    "regancipher", "riz", "smirk", "soundignity", "suporsalad", "tgx78", 
    "therollo9", "scboy", "seanwee", "silicagel", "sl0the", "soundcheck39", 
    "tanchjim", "tedthepraimortis", "treblewellxtended", "vsg", "yanyin", 
    "yoshiultra", "kuulokenurkka", "sai", "earphonesarchive"
]

DB_FILE = "database.json"
HISTORY_FILE = "history.json"

def fetch_data(subdomain):
    url = f"https://{subdomain}.squig.link/data/phone_book.json"
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

def process_item(sub, name, share_id, database, new_finds):
    # 'name' = The pretty text (e.g., "Moondrop Kato")
    # 'share_id' = The hidden filename (e.g., "Moondrop_Kato_Sample_1")
    
    # Generate the link using the EXACT ID from the source
    import urllib.parse
    encoded_id = urllib.parse.quote(share_id)
    deep_link = f"https://{sub}.squig.link/?share={encoded_id}"

    # Database logic
    if sub not in database:
        database[sub] = []
    
    # We check against the display name to avoid duplicates
    if name not in database[sub]:
        database[sub].append(name)
        new_finds.append({
            "reviewer": sub.capitalize(),
            "item": name,
            "date": datetime.now().strftime("%b %d, %H:%M"),
            "link": deep_link
        })

def run_check():
    # ... (Keep your existing database loading code) ...
    
    for sub in SUBDOMAINS:
        print(f"Checking {sub}...")
        
        # Helper to try main URL + subfolders
        data = None
        valid_path = sub # To remember which path worked (e.g., "crinacle" vs "crinacle/headphones")
        
        # Try finding the phonebook in common locations
        paths_to_try = ["", "headphones", "earbuds", "iems"]
        
        for path in paths_to_try:
            # Construct URL: https://crinacle.squig.link/data/phone_book.json
            # OR https://crinacle.squig.link/headphones/data/phone_book.json
            base_url = f"https://{sub}.squig.link"
            if path: 
                base_url += f"/{path}"
                
            check_url = f"{base_url}/data/phone_book.json"
            
            fetched = fetch_data_from_url(check_url)
            if fetched:
                data = fetched
                valid_path = f"{sub}/{path}" if path else sub
                # We need the base subdomain for the link, not the full path
                # actually, if it's in a subfolder, the share link usually needs that folder too
                # e.g. crinacle.squig.link/headphones/?share=...
                link_domain = f"{sub}.squig.link/{path}" if path else f"{sub}.squig.link"
                break
        
        if not data: continue
        
        # --- ROBUST PARSING START ---
        
        # Type 1: Dictionary {"Unique_ID": "Display Name"} (Most common/Accurate)
        if isinstance(data, dict):
            for share_id, display_name in data.items():
                # Sometimes the value is a list (Old format: {"Brand": ["Model"]})
                if isinstance(display_name, list):
                    # In this rare case, we fall back to assuming ID = Name
                    for model in display_name:
                        process_item(link_domain, f"{share_id} {model}", model, database, new_finds)
                else:
                    # The Standard Format
                    process_item(link_domain, display_name, share_id, database, new_finds)

        # Type 2: Simple List ["Model A", "Model B"]
        elif isinstance(data, list):
            for item in data:
                # In lists, the ID and Name are identical
                process_item(link_domain, item, item, database, new_finds)
                
        # --- ROBUST PARSING END ---
        
        time.sleep(1) # Safety delay
