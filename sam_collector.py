import os
import json
import requests
from datetime import datetime, timedelta

API_KEY = os.environ.get("SAM_API_KEY")

url = "https://api.sam.gov/opportunities/v2/search"

today = datetime.utcnow()
posted_to = today.strftime("%m/%d/%Y")
posted_from = (today - timedelta(days=30)).strftime("%m/%d/%Y")

KEYWORDS = [
    "construction",
    "repair",
    "renovation",
    "remediation",
    "environmental",
    "facility",
    "facilities",
    "maintenance",
    "hvac",
    "roofing",
    "drywall",
    "painting",
    "demolition",
    "cleanup",
    "disaster",
    "restoration",
    "mold"
]

PRIORITY_STATES = ["FL", "GA", "Florida", "Georgia"]

params = {
    "api_key": API_KEY,
    "postedFrom": posted_from,
    "postedTo": posted_to,
    "ptype": "o",
    "limit": 200
}

response = requests.get(url, params=params, timeout=60)
response.raise_for_status()
data = response.json()

results = []

for item in data.get("opportunitiesData", []):
    title = item.get("title", "")
    title_lower = title.lower()

    if not any(word in title_lower for word in KEYWORDS):
        continue

    state = item.get("state", "Unknown")
    naics = item.get("ncode", "Unknown")

    amount = item.get("award", 0)
    try:
        amount = float(amount)
    except:
        amount = 0

    if amount < 100000:
        continue

    score = 0

    if any(word in title_lower for word in KEYWORDS):
        score += 10

    if state in PRIORITY_STATES:
        score += 5

    results.append({
        "title": title,
        "solicitation": item.get("solicitationNumber", "N/A"),
        "state": state,
        "naics": naics,
        "value": amount,
        "score": score
    })

results.sort(key=lambda x: x["score"], reverse=True)

with open("opportunities.json", "w") as f:
    json.dump(results[:50], f, indent=2)

print("Updated opportunities:", len(results[:50]))
