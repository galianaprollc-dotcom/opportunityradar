import os
import json
import time
import requests
from datetime import datetime, timedelta

API_KEY = os.environ.get("SAM_API_KEY")
URL = "https://api.sam.gov/opportunities/v2/search"

today = datetime.utcnow()
posted_to = today.strftime("%m/%d/%Y")
posted_from = (today - timedelta(days=30)).strftime("%m/%d/%Y")

NAICS_FILTER = {
    "236220",  # Commercial building construction
    "237310",  # Highway / street / site
    "238220",  # Plumbing / HVAC
    "238320",  # Painting / wall covering
    "238330",  # Flooring
    "238350",  # Finish carpentry
    "238910",  # Site prep
    "238990",  # Specialty trade
    "562910"   # Environmental remediation
}

EXCLUDE_WORDS = [
    "ship",
    "voyage",
    "vessel",
    "antenna",
    "spectrum",
    "electromagnetic",
    "analyzer",
    "pathology",
    "medical",
    "vehicle",
    "truck",
    "wrecker",
    "actuator",
    "parts",
    "aircraft",
    "missile",
    "weapon",
    "cyber",
    "software",
    "telecom",
    "communications",
    "radar",
    "naval",
    "marine"
]

PRIORITY_STATES = {"FL", "GA", "Florida", "Georgia"}

params = {
    "api_key": API_KEY,
    "limit": 100,
    "ptype": "o",
    "postedFrom": posted_from,
    "postedTo": posted_to
}

response = None

for attempt in range(5):
    response = requests.get(URL, params=params, timeout=60)

    if response.status_code == 200:
        break

    if response.status_code == 429:
        print("SAM rate limit hit. Waiting 15 seconds...")
        time.sleep(15)
        continue

    print("SAM returned error:", response.status_code)
    raise Exception("SAM request failed")

if response is None or response.status_code != 200:
    raise Exception("SAM request failed after retries")

data = response.json()
results = []

for item in data.get("opportunitiesData", []):
    title = item.get("title", "")
    title_lower = title.lower()

    naics = str(item.get("naicsCode", "")).strip()
    state = item.get("placeOfPerformanceState", "Unknown")

    if naics not in NAICS_FILTER:
        continue

    if any(word in title_lower for word in EXCLUDE_WORDS):
        continue

    score = 10
    if state in PRIORITY_STATES:
        score += 5

    value = item.get("award")
    if isinstance(value, dict):
        value = value.get("amount")

    results.append({
        "title": title,
        "solicitation": item.get("solicitationNumber", "N/A"),
        "state": state,
        "naics": naics if naics else "Unknown",
        "value": value if value else "Not listed",
        "score": score
    })

with open("opportunities.json", "w") as f:
    json.dump(results[:50], f, indent=2)

print("Updated filtered opportunities:", len(results[:50]))
