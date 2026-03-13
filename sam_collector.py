import os
import json
import time
import requests
from datetime import datetime, timedelta

API_KEY = os.environ.get("SAM_API_KEY")
URL = "https://api.sam.gov/opportunities/v2/search"

# Keep the request small and inside the required date window
today = datetime.utcnow()
posted_to = today.strftime("%m/%d/%Y")
posted_from = (today - timedelta(days=30)).strftime("%m/%d/%Y")

params = {
    "api_key": API_KEY,
    "ptype": "o",          # solicitation
    "postedFrom": posted_from,
    "postedTo": posted_to,
    "limit": 25,
    "offset": 0
}

def safe_amount(item):
    award = item.get("award")
    if isinstance(award, dict):
        amt = award.get("amount")
        if amt not in [None, "", {}]:
            return amt
    return None

def safe_due_date(item):
    # SAM docs show this field as reponseDeadLine in the response docs,
    # but keep a fallback in case the payload varies.
    return (
        item.get("reponseDeadLine")
        or item.get("responseDeadLine")
        or item.get("archiveDate")
        or "Unknown"
    )

def safe_agency(item):
    return (
        item.get("fullParentPathName")
        or item.get("organizationName")
        or item.get("department")
        or item.get("subtier")
        or "Unknown"
    )

response = None

for attempt in range(5):
    response = requests.get(URL, params=params, timeout=60)

    if response.status_code == 200:
        break

    if response.status_code == 429:
        print(f"SAM rate limit hit on attempt {attempt + 1}. Waiting 20 seconds...")
        time.sleep(20)
        continue

    print("SAM returned error:", response.status_code)
    print(response.text[:500])
    raise Exception("SAM request failed")

if response is None or response.status_code != 200:
    raise Exception("SAM request failed after retries")

data = response.json()

# Save raw response too, so we can inspect exactly what SAM is returning
with open("sam_raw.json", "w") as raw_file:
    json.dump(data, raw_file, indent=2)

results = []

for item in data.get("opportunitiesData", []):
    results.append({
        "title": item.get("title", "Unknown"),
        "solicitation": item.get("solicitationNumber", "N/A"),
        "agency": safe_agency(item),
        "posted_date": item.get("postedDate", "Unknown"),
        "due_date": safe_due_date(item),
        "naics": item.get("naicsCode", "Unknown"),
        "set_aside": item.get("setAside", "Not listed"),
        "value": safe_amount(item),
        "score": 0
    })

with open("opportunities.json", "w") as f:
    json.dump(results, f, indent=2)

print("Updated opportunities:", len(results))
