import os
import json
import requests
from datetime import datetime, timedelta

API_KEY = os.environ.get("SAM_API_KEY")

url = "https://api.sam.gov/opportunities/v2/search"

today = datetime.utcnow()
posted_to = today.strftime("%m/%d/%Y")
posted_from = (today - timedelta(days=30)).strftime("%m/%d/%Y")

INCLUDE_WORDS = [
    "construction",
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
    "mold",
    "repair"
]

EXCLUDE_WORDS = [
    "antenna",
    "spectrum",
    "electromagnetic",
    "engineering analysis",
    "truck",
    "vehicle",
    "wrecker",
    "actuator",
    "parts",
    "weapon",
    "missile",
    "aircraft",
    "radar",
    "software",
    "cyber",
    "it support",
    "telecom",
    "communications",
    "medical equipment"
]

PRIORITY_STATES = ["FL", "GA", "Florida", "Georgia"]

params = {
    "api_key": API_KEY,
    "postedFrom": posted_from,
    "postedTo": posted_to,
    "ptype": "o",
    "limit": 200,
    "offset": 0
}

response = requests.get(url, params=params, timeout=60)
response.raise_for_status()
data = response.json()

results = []

for item in data.get("opportunitiesData", []):
    title = item.get("title", "")
    title_lower = title.lower()

    if not any(word in title_lower for word in INCLUDE_WORDS):
        continue

    if any(word in title_lower for word in EXCLUDE_WORDS):
        continue

    state = item.get("state", "Unknown")
    naics = item.get("ncode", "Unknown")

    score = 0

    if any(word in title_lower for word in INCLUDE_WORDS):
        score += 10

    if state in PRIORITY_STATES:
        score += 5

    results.append({
        "title": title,
        "solicitation": item.get("solicitationNumber", "N/A"),
        "state": state,
        "naics": naics,
        "value": item.get("award", "Not listed"),
        "score": score
    })

results.sort(key=lambda x: x["score"], reverse=True)

with open("opportunities.json", "w") as f:
    json.dump(results[:50], f, indent=2)

print("Updated filtered opportunities:", len(results[:50]))
