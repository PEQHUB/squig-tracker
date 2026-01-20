import requests
import json
import os
from datetime import datetime

# 1. THE MASTER LIST OF REVIEWERS
# You can add any new squig.link subdomain here easily!
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
        # We add a 'User-Agent' to look like a real browser
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Skipping {subdomain}: {e}")
    return None


def run_check():
    # Load Database
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            try:
                database = json.load(f)
                if not isinstance(database, dict): database = {}
            except:
                database = {}
    else:
        database = {}

    new_finds = []

    for sub in SUBDOMAINS:
        print(f"Checking {sub}...")
        data = fetch_data(sub)
        
        if not data: continue
        if sub not in database: database[sub] = []

        # --- SMART PARSING START ---
        # If it's a Dictionary (e.g., {"Sony": ["IER-Z1R"]})
        if isinstance(data, dict):
            for brand, models in data.items():
                for model in models:
                    process_item(sub, brand, model, database, new_finds)
        
        # If it's a List (e.g., ["Sony IER-Z1R", "Moondrop Kato"])
        elif isinstance(data, list):
            for item in data:
                process_item(sub, "", item, database, new_finds)
        # --- SMART PARSING END ---

    # Save files
    with open(DB_FILE, "w") as f: json.dump(database, f, indent=4)
    if new_finds:
        history = []
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r") as f: history = json.load(f)
        updated_history = new_finds + history
        with open(HISTORY_FILE, "w") as f:
            json.dump(updated_history[:200], f, indent=4)

def process_item(sub, brand, model, database, new_finds):
    # Clean up the name
    full_name = f"{brand} {model}".strip()
    if full_name not in database[sub]:
        database[sub].append(full_name)
        new_finds.append({
            "reviewer": sub.capitalize(),
            "item": full_name,
            "date": datetime.now().strftime("%b %d, %H:%M"),
            "link": f"https://{sub}.squig.link"
        })

    # Save Database
    with open(DB_FILE, "w") as f:
        json.dump(database, f, indent=4)

    # Update History (the feed for your website)
    if new_finds:
        print(f"Success! Found {len(new_finds)} new items.")
        history = []
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r") as f: history = json.load(f)

        # Add newest to top and keep only the last 200 items
        updated_history = new_finds + history
        with open(HISTORY_FILE, "w") as f:
            json.dump(updated_history[:200], f, indent=4)


if __name__ == "__main__":

    run_check()
