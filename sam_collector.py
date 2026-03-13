import os
import requests
import json

API_KEY = os.environ.get("SAM_API_KEY")

url = "https://api.sam.gov/prod/opportunities/v2/search"

params = {
    "api_key": API_KEY,
    "limit": 10
}

response = requests.get(url, params=params)

data = response.json()

opportunities = []

if "opportunitiesData" in data:
    for item in data["opportunitiesData"]:
        opportunities.append({
            "title": item.get("title", "Unknown Opportunity"),
            "solicitation": item.get("solicitationNumber", "N/A"),
            "state": item.get("placeOfPerformance", {}).get("state", "Unknown"),
            "naics": item.get("naicsCode", "Unknown")
        })

with open("opportunities.json", "w") as f:
    json.dump(opportunities, f, indent=2)

print("Opportunities updated.")
