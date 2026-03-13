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
    "limit": 100
}

response = requests.get(url, params=params)
data = response.json()

opportunities = []

for item in data.get("opportunitiesData", []):

    title = item.get("title","")
    title_lower = title.lower()

    keywords = [
        "construction",
        "repair",
        "renovation",
        "remediation",
        "environmental",
        "facility",
        "maintenance",
        "hvac",
        "roofing",
        "drywall",
        "painting",
        "demolition",
        "cleanup"
    ]

    if not any(k in title_lower for k in keywords):
        continue

    opportunities.append({
        "title": title,
        "solicitation": item.get("solicitationNumber","N/A"),
        "state": item.get("state","Unknown"),
        "naics": item.get("ncode","Unknown")
    })

with open("opportunities.json","w") as f:
    json.dump(opportunities[:50],f,indent=2)

print("Updated opportunities:",len(opportunities[:50]))
