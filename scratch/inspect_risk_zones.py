import urllib.request
import json

base_url = "http://localhost:8080/api/risk-zones"

# 1. Fetch all risk zones
with urllib.request.urlopen(f"{base_url}") as resp:
    zones = json.loads(resp.read().decode("utf-8"))

print("=== 1. ALL REGISTERED RISK ZONES ===")
for z in zones:
    print(f"ID: {z['id']}")
    print(f"Name: {z['name']}")
    print(f"Risk Level: {z['riskLevel']}")
    print(f"Boundary: {z['boundary']}")
    print(f"Description: {z['description']}")
    print("-" * 50)

# 2. Check if (30.529505, 79.085957) lies inside any zone
kedarnath_url = f"{base_url}/locate?latitude=30.529505&longitude=79.085957"
with urllib.request.urlopen(kedarnath_url) as resp:
    loc_kedarnath = json.loads(resp.read().decode("utf-8"))

print("\n=== 2. LOCATE POINT: KEDARNATH (30.529505, 79.085957) ===")
print(json.dumps(loc_kedarnath, indent=2))

# 3. Check if (30.42, 78.42) lies inside Dehradun zone
dehradun_url = f"{base_url}/locate?latitude=30.42&longitude=78.42"
with urllib.request.urlopen(dehradun_url) as resp:
    loc_dehradun = json.loads(resp.read().decode("utf-8"))

print("\n=== 3. LOCATE POINT: DEHRADUN INTERIOR (30.42, 78.42) ===")
print(json.dumps(loc_dehradun, indent=2))
