import json
import os
import sys

os.environ["DATABASE_URL"] = "sqlite:///./test_smoke.db"
if os.path.exists("test_smoke.db"):
    os.remove("test_smoke.db")

from fastapi.testclient import TestClient  # noqa: E402

from main import app  # noqa: E402

client = TestClient(app)
results = []
fails = 0


def check(name, cond, extra=""):
    status = "PASS" if cond else "FAIL"
    global fails
    if not cond:
        fails += 1
    results.append(f"{status}  {name} {extra}")


# Health
r = client.get("/api/health")
check("health endpoint", r.status_code == 200)

# Register
r = client.post("/api/auth/register", json={"email": "smoke@test.com", "password": "secret123", "full_name": "Smoke Tester"})
check("register user", r.status_code == 201, f"-> {r.status_code}")
token = r.json().get("access_token", "")
check("token issued", bool(token))
headers = {"Authorization": f"Bearer {token}"}

# Duplicate register rejected
r = client.post("/api/auth/register", json={"email": "smoke@test.com", "password": "secret123"})
check("duplicate register 400", r.status_code == 400)

# Login
r = client.post("/api/auth/login", json={"email": "smoke@test.com", "password": "secret123"})
check("login", r.status_code == 200)
r = client.post("/api/auth/login", json={"email": "smoke@test.com", "password": "wrong"})
check("bad login 401", r.status_code == 401)

# Unauthorized access
r = client.get("/api/leads")
check("leads requires auth", r.status_code == 401)

# Parse ICP
icp_text = ("Mid-sized SaaS companies in the United States targeting enterprise clients. "
            "Looking for CTOs, VP of Engineering, and Head of Product decision makers. "
            "They should use Salesforce, AWS and be venture-backed.")
r = client.post("/api/icps/parse", json={"raw_input": icp_text})
check("parse ICP", r.status_code == 200)
c = r.json()["criteria"]
check("ICP industries", "saas" in [i.lower() for i in c["industries"]], f"=> {c['industries']}")
check("ICP has company_size", len(c["company_size"]) > 0, f"=> {c['company_size']}")
check("ICP geographies", len(c["geographies"]) > 0, f"=> {c['geographies']}")
check("ICP job_titles", len(c["job_titles"]) > 0, f"=> {c['job_titles']}")

# Create ICP
r = client.post("/api/icps", json={"raw_input": icp_text, "name": "US SaaS"}, headers=headers)
check("create ICP", r.status_code == 201)
icp_id = r.json()["id"]

# List ICPs
r = client.get("/api/icps", headers=headers)
check("list ICPs", r.status_code == 200 and len(r.json()) >= 1)

# Update ICP
r = client.put(f"/api/icps/{icp_id}", json={"name": "US SaaS v2", "industries": ["saas"], "company_size": ["51-200"], "geographies": ["United States"], "job_titles": ["CTO"]}, headers=headers)
check("update ICP", r.status_code == 200 and r.json()["name"] == "US SaaS v2", f"-> {r.status_code}")

# Discovery
r = client.post("/api/discovery/run", json={"icp_id": icp_id}, headers=headers)
check("discovery run", r.status_code == 200, f"-> {r.status_code} {r.text[:80]}")
disc = r.json()
check("discovery returned leads", disc["total_discovered"] > 0 and disc["scored_count"] > 0, f"=> {disc}")

# Run discovery again -> dedup should catch duplicates
r2 = client.post("/api/discovery/run", json={"icp_id": icp_id}, headers=headers)
check("re-discovery dedups", r2.status_code == 200 and r2.json()["scored_count"] == 0 and r2.json()["duplicates_merged"] > 0, f"=> {r2.json()}")

# List leads
r = client.get("/api/leads?limit=10", headers=headers)
check("list leads", r.status_code == 200)
leads = r.json()["leads"]
check("leads scored", all(l["score"] > 0 for l in leads), f"first scores: {[l['score'] for l in leads[:3]]}")
check("leads enriched", all(len(l["contacts"]) > 0 for l in leads))
check("leads have breakdown", all(len(l["score_breakdown"]) > 0 for l in leads))
check("leads have explanation", all(l["score_explanation"] for l in leads))
check("lead has company", all(l["company"] and l["company"]["name"] for l in leads))

# Filter by min_score
r = client.get("/api/leads?min_score=70", headers=headers)
check("filter min_score", r.status_code == 200 and all(l["score"] >= 70 for l in r.json()["leads"]), f"total={r.json()['total']}")

# Search
r = client.get("/api/leads?q=Nexora", headers=headers)
check("search query", r.status_code == 200)

# Lead detail
lead_id = leads[0]["id"]
r = client.get(f"/api/leads/{lead_id}", headers=headers)
check("lead detail", r.status_code == 200 and r.json()["company"]["name"])
detail = r.json()
check("detail contacts", len(detail["contacts"]) > 0)
check("detail breakdown", len(detail["score_breakdown"]) >= 3, f"=> {len(detail['score_breakdown'])} criteria")

# Update status
r = client.patch(f"/api/leads/{lead_id}?status=contacted", headers=headers)
check("update lead status", r.status_code == 200 and r.json()["status"] == "contacted")

# Stats
r = client.get("/api/leads/stats/summary", headers=headers)
check("stats", r.status_code == 200 and r.json()["total"] >= 1, f"=> {r.json()}")

# Export CSV
r = client.get("/api/export/csv", headers=headers)
check("export csv", r.status_code == 200 and "company_name" in r.text, f"content-type={r.headers.get('content-type')}")
check("csv has row", "lead_id" in r.text and len(r.text.splitlines()) >= 2)

# Export JSON
r = client.get("/api/export/json", headers=headers)
check("export json", r.status_code == 200 and "company_name" in r.text)
data = json.loads(r.text)
check("json rows", len(data) >= 1)

# Delete ICP cascade
r = client.delete(f"/api/icps/{icp_id}", headers=headers)
check("delete ICP", r.status_code == 204)
r = client.get("/api/leads", headers=headers)
check("leads cascaded", r.json()["total"] == 0)

print("\n".join(results))
print(f"\n===== {sum('PASS' in x for x in results)}/{len(results)} passed, {fails} failed =====")
if os.path.exists("test_smoke.db"):
    os.remove("test_smoke.db")
sys.exit(1 if fails else 0)