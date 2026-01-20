import requests

def get_all_squig_subdomains():
    # Query crt.sh for all subdomains of squig.link
    url = "https://crt.sh/?q=%.squig.link&output=json"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        # Extract unique common names
        subdomains = set()
        for entry in data:
            name = entry['common_name']
            if name.endswith('.squig.link'):
                # Handle cases like *.squig.link
                clean_name = name.replace('*.', '')
                subdomains.add(clean_name)
        return sorted(list(subdomains))
    return []

# Use this to update your database.json reviewers list
new_list = get_all_squig_subdomains()
print(f"Found {len(new_list)} reviewers.")
