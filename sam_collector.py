import requests
import json

API_KEY = "PASTE_YOUR_SAM_API_KEY_HERE"

URL = "https://api.sam.gov/opportunities/v2/search"

params = {
    "api_key": API_KEY,
    "limit": 50,
    "postedFrom": "01/01/2024",
}

response = requests.get(URL, params=params)

data = response.json()

opportunities = []

for item in data.get("opportunitiesData", []):
    
    title = item.get("title")
    solicitation = item.get("solicitationNumber")
    state = item.get("placeOfPerformance", {}).get("state")
    naics = item.get("naicsCode")
    
    opportunities.append({
        "title": title,
        "solicitation": solicitation,
        "state": state,
        "naics": naics
    })

with open("opportunities.json", "w") as f:
    json.dump(opportunities, f, indent=2)

print("SAM opportunities collected.")
