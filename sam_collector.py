import os
import json
import requests
import time

API_KEY = os.environ.get("SAM_API_KEY")

URL = "https://api.sam.gov/opportunities/v2/search"

params = {
    "api_key": API_KEY,
    "limit": 50,
    "ptype": "o"
}

print("Requesting SAM opportunities...")

time.sleep(5)

response = requests.get(URL, params=params)

if response.status_code != 200:
    print("SAM returned error:", response.status_code)
    exit()

data = response.json()

results = []

for item in data.get("opportunitiesData", []):

    title = item.get("title","")
    title_lower = title.lower()

    EXCLUDE = [
        "ship",
        "naval",
        "aircraft",
        "weapon",
        "missile",
        "pathology",
        "medical",
        "radar",
        "telecom",
        "software",
        "cyber",
        "vehicle"
    ]

    if any(x in title_lower for x in EXCLUDE):
        continue

    value = None

    if "award" in item and isinstance(item["award"], dict):
        value = item["award"].get("amount")

    results.append({
        "title": title,
        "solicitation": item.get("solicitationNumber"),
        "state": item.get("placeOfPerformanceState","Unknown"),
        "naics": item.get("naicsCode","Unknown"),
        "value": value,
        "score": 10
    })

print("Saving filtered opportunities:", len(results))

with open("opportunities.json","w") as f:
    json.dump(results[:50], f, indent=2)
