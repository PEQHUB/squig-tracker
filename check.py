import requests
import json
import os
from datetime import datetime

SUBDOMAINS = [
    "crinacle", "superreview", "hbb", "precog", "timmyv", 
    "namedkenn", "rg", "wolfhawk", "akros", "paulwasabii", 
    "vortex", "teds", "banbeucmas", "jaytiss", "tonedeafmonk", 
    "aftersound", "hypethewiev", "tks", "venerable", "regancipher",
    "den-fi", "kr0mka", "marcelo", "nick", "rohit", "shuji"
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

def process_item(sub, brand, model, database, new_finds):
    full_name = f"{brand} {model}".strip()
    if sub not in database:
        database[sub] = []
    
    if full_name not in database[sub]:
        database[sub].append(full_name)
        new_finds.append({
            "reviewer": sub.capitalize(),
            "item": full_name,
            "date": datetime.now().strftime("%b %d, %H:%M"),
            "link": f"https://{sub}.squig.link"
        })

def run_check():
    # Load Database (The lookup list)
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            try:
                database = json.load(f)
                if not isinstance(database, dict): database = {}
            except: database = {}
    else:
        database = {}

    new_finds = []

    for sub in SUBDOMAINS:
        print(f"Checking {sub}...")
        data = fetch_data(sub)
        if not data: continue

        if isinstance(data, dict):
            for brand, models in data.items():
                if isinstance(models, list):
                    for model in models:
                        process_item(sub, brand, model, database, new_finds)
        elif isinstance(data, list):
            for item in data:
                process_item(sub, "", item, database, new_finds)

    # Save the lookup database
    with open(DB_FILE, "w") as f:
        json.dump(database, f, indent=4)

    # Save the visual history for the website
    if new_finds:
        print(f"Found {len(new_finds)} new items!")
        history = []
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r") as f:
                try:
                    history = json.load(f)
                    if not isinstance(history, list): history = []
                except: history = []
        
        # Combine the lists correctly
        updated_history = new_finds + history
        with open(HISTORY_FILE, "w") as f:
            json.dump(updated_history[:200], f, indent=4)

if __name__ == "__main__":
    run_check()
