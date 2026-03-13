import os
import json
import time
import requests
from datetime import datetime, timedelta

API_KEY = os.environ.get("SAM_API_KEY")
URL = "https://api.sam.gov/opportunities/v2/search"

MIN_VALUE = 100000
PRIORITY_STATES = {"FL", "GA", "Florida", "Georgia"}

NAICS_CODES = {
    "236115", "236116", "236117", "236118",
    "236210", "236220",
    "237110", "237130", "237310", "237990",
    "238110", "238120", "238130", "238140", "238160", "238170", "238190",
    "238210", "238220", "238290",
    "238310", "238320", "238330", "238340", "238350", "238390",
    "238910", "238990",
    "541620",
    "561210", "561720", "561790",
    "562910", "562998"
}

INCLUDE_WORDS = [
    "construction",
    "repair",
    "renovation",
    "remediation",
    "environmental",
    "facility",
    "facilities",
    "maintenance",
    "building maintenance",
    "maintenance building",
    "hvac",
    "roofing",
    "drywall",
    "painting",
    "demolition",
    "cleanup",
    "disaster",
    "restoration",
    "mold",
    "concrete",
    "carpentry",
    "flooring",
    "site work",
    "sidewalk",
    "storm damage",
    "water damage",
    "repair and minor construction",
    "alterations",
    "rehabilitation"
]

EXCLUDE_WORDS = [
    "antenna",
    "spectrum",
    "electromagnetic",
    "analyzer",
    "pathology",
    "medical",
    "truck",
    "vehicle",
    "wrecker",
    "actuator",
    "parts",
    "ship",
    "voyage",
    "vessel",
    "marine",
    "naval",
    "aircraft",
    "missile",
    "weapon",
    "cyber",
    "software",
    "telecom",
    "communications",
    "radar",
    "engineering analysis",
    "laboratory",
    "test equipment"
]

TRIBAL_WORDS = [
    "tribal",
    "native american",
    "buy indian",
    "isbee",
    "indian small business economic enterprise",
    "tribe",
    "bureau of indian affairs",
    "bureau of indian education",
    "indian health service"
]

SET_ASIDE_WORDS = [
    "8(a)",
    "hubzone",
    "sdvosb",
    "wosb",
    "small business",
    "set-aside",
    "set aside"
]


def pick_first(d, keys, default=None):
    for key in keys:
        value = d.get(key)
        if value not in [None, "", [], {}]:
            return value
    return default


def parse_amount(item):
    candidates = [
        item.get("award"),
        item.get("awardAmount"),
        item.get("estimatedValue"),
        item.get("estimatedvalue"),
        item.get("value"),
        item.get("amount"),
        item.get("baseAndAllOptionsValue"),
        item.get("baseandalloptionsvalue")
    ]

    for candidate in candidates:
        if isinstance(candidate, dict):
            for subkey in ["amount", "value", "totalAmount", "estimatedAmount"]:
                subvalue = candidate.get(subkey)
                if subvalue not in [None, "", {}]:
                    try:
                        return float(str(subvalue).replace(",", "").replace("$", ""))
                    except Exception:
                        pass
        else:
            if candidate not in [None, "", {}]:
                try:
                    return float(str(candidate).replace(",", "").replace("$", ""))
                except Exception:
                    pass

    return 0.0


today = datetime.utcnow()
posted_to = today.strftime("%m/%d/%Y")
posted_from = (today - timedelta(days=30)).strftime("%m/%d/%Y")

params = {
    "api_key": API_KEY,
    "postedFrom": posted_from,
    "postedTo": posted_to,
    "ptype": "o",
    "limit": 100,
    "offset": 0
}

response = None
for attempt in range(3):
    response = requests.get(URL, params=params, timeout=60)
    if response.status_code == 429:
        time.sleep(15)
        continue
    response.raise_for_status()
    break

if response is None or response.status_code == 429:
    raise Exception("SAM API rate limit hit after retries")

data = response.json()
results = []

for item in data.get("opportunitiesData", []):
    title = pick_first(item, ["title"], "")
    title_lower = title.lower()

    naics = str(pick_first(item, ["ncode", "naicsCode", "naicscode"], "")).strip()
    state = pick_first(item, ["state", "placeOfPerformanceState", "placeofperformancestate"], "Unknown")
    solicitation = pick_first(item, ["solicitationNumber", "solicitationnumber"], "N/A")

    agency = pick_first(
        item,
        ["fullParentPathName", "department", "organizationName", "office", "officeAddress"],
        "Unknown"
    )

    posted_date = pick_first(item, ["postedDate", "posteddate", "publishDate"], "Unknown")
    due_date = pick_first(item, ["responseDeadLine", "responsedeadline", "archiveDate", "archivedate"], "Unknown")
    set_aside = pick_first(
        item,
        ["typeOfSetAsideDescription", "typeOfSetAside", "typeofsetaside", "setAside", "setaside"],
        "Not listed"
    )

    description = pick_first(item, ["description", "synopsis"], "")
    desc_lower = description.lower() if isinstance(description, str) else ""

    value = parse_amount(item)

    if value < MIN_VALUE:
        continue

    if any(word in title_lower for word in EXCLUDE_WORDS):
        continue
    if any(word in desc_lower for word in EXCLUDE_WORDS):
        continue

    keyword_match = any(word in title_lower for word in INCLUDE_WORDS) or any(word in desc_lower for word in INCLUDE_WORDS)
    naics_match = naics in NAICS_CODES

    if not keyword_match and not naics_match:
        continue

    score = 0
    if keyword_match:
        score += 10
    if naics_match:
        score += 20
    if state in PRIORITY_STATES:
        score += 10

    text_blob = f"{title_lower} {desc_lower} {str(set_aside).lower()}"

    tribal_priority = any(word in text_blob for word in TRIBAL_WORDS)
    if tribal_priority:
        score += 15

    if any(word in text_blob for word in SET_ASIDE_WORDS):
        score += 5

    results.append({
        "title": title or "Unknown Opportunity",
        "solicitation": solicitation,
        "state": state,
        "naics": naics if naics else "Unknown",
        "value": value,
        "score": score,
        "agency": agency,
        "posted_date": posted_date,
        "due_date": due_date,
        "set_aside": set_aside,
        "tribal_priority": tribal_priority
    })

results.sort(key=lambda x: (x["score"], x["value"]), reverse=True)

with open("opportunities.json", "w") as f:
    json.dump(results[:50], f, indent=2)

print("Updated opportunities:", len(results[:50]))
