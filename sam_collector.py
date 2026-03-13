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

params = {
"api_key": API_KEY,
"postedFrom": posted_from,
"postedTo": posted_to,
"limit": 200
}

response = requests.get(url, params=params)
data = response.json()

results = []

for item in data.get("opportunitiesData", []):

title = item.get("title","")
title_lower = title.lower()

if not any(word in title_lower for word in KEYWORDS):
continue

results.append({
"title": title,
"solicitation": item.get("solicitationNumber","N/A"),
"state": item.get("placeOfPerformance","Unknown"),
"naics": item.get("naicsCode","Unknown"),
"value": item.get("award","Not listed"),
"agency": item.get("department","Unknown"),
"deadline": item.get("responseDeadLine","Unknown"),
"setaside": item.get("typeOfSetAside","None")
})

with open("opportunities.json","w") as f:
json.dump(results[:50],f,indent=2)

print("Updated opportunities:",len(results))
