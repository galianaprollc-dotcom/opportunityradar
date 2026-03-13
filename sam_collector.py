import os
import json
import time
import requests
from datetime import datetime, timedelta

API_KEY = os.environ.get("SAM_API_KEY")
URL = "https://api.sam.gov/opportunities/v2/search"

print("Waiting 30 seconds before SAM request to avoid rate limits...")
time.sleep(30)

today = datetime.utcnow()
posted_to = today.strftime("%m/%d/%Y")
posted_from = (today - timedelta(days=7)).strftime("%m/%d/%Y")

params = {
    "api_key": API_KEY,
    "ptype": "o",
    "postedFrom": posted_from,
    "postedTo": posted_to,
    "limit": 10
}

response = None

for attempt in range(5):

    print(f"Attempt {attempt+1} contacting SAM...")
    response = requests.get(URL, params=params, timeout=60)

    if response.status_code == 200:
        break

    if response.status_code == 429:
        print("Rate limited. Waiting 40 seconds...")
        time.sleep(40)
        continue

    print("SAM error:", response.status_code)
    raise Exception("SAM request failed")

if response.status_code != 200:
    raise Exception("SAM request failed after retries")

data = response.json()

results = []

for item in data.get("opportunitiesData", []):

    title = item.get("title","")
    state = item.get("placeOfPerformanceState","Unknown")
    naics = item.get("naicsCode","Unknown")

    results.append({
        "title": title,
        "solicitation": item.get("solicitationNumber","N/A"),
        "state": state,
        "naics": naics,
        "value": "Unknown",
        "score": 10
    })

with open("opportunities.json","w") as f:
    json.dump(results, f, indent=2)

print("Opportunities written:", len(results))
