import os
import json
import requests
from datetime import datetime, timedelta

API_KEY = os.environ.get("SAM_API_KEY")

url = "https://api.sam.gov/opportunities/v2/search"

today = datetime.utcnow()
posted_to = today.strftime("%m/%d/%Y")
posted_from = (today - timedelta(days=30)).strftime("%m/%d/%Y")

params = {
    "api_key": API_KEY,
    "postedFrom": posted_from,
    "postedTo": posted_to,
    "ptype": "o",
    "limit": 20,
    "offset": 0
}

response = requests.get(url, params=params, timeout=60)

print("STATUS:", response.status_code)
print("TEXT:", response.text[:500])

response.raise_for_status()

data = response.json()

opportunities = []

for item in data.get("opportunitiesData", []):
    opportunities.append({
        "title": item.get("title", "Unknown Opportunity"),
        "solicitation": item.get("solicitationNumber", "N/A"),
        "state": item.get("state", "Unknown"),
        "naics": item.get("ncode", "Unknown")
    })

with open("opportunities.json", "w") as f:
    json.dump(opportunities, f, indent=2)

print(f"Opportunities updated: {len(opportunities)}")
