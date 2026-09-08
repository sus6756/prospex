import re

from utils.helpers import slugify


def enrich_contact(contact_data: dict, company_domain: str) -> dict:
    """Fill in missing contact fields using heuristic / deterministic logic."""
    enriched = dict(contact_data)
    domain = company_domain or ""
    full_name = enriched.get("full_name") or ""
    parts = [p.strip() for p in full_name.split() if p.strip()]

    if parts:
        if len(parts) >= 2:
            enriched["first_name"] = parts[0]
            enriched["last_name"] = parts[-1]
        else:
            enriched["first_name"] = parts[0]
            enriched["last_name"] = enriched.get("last_name") or ""

    if not enriched.get("email") and parts and domain:
        first = (parts[0] or "").lower()
        last = (parts[-1] or "").lower()
        candidates = [
            f"{first}@{domain}",
            f"{first}{last}@{domain}",
            f"{first}.{last}@{domain}",
            f"{first[0]}{last}@{domain}",
        ]
        # Pick deterministic candidate
        idx = sum(ord(c) for c in full_name + domain) % len(candidates)
        enriched["email"] = candidates[idx]

    if not enriched.get("linkedin_url") and parts:
        enriched["linkedin_url"] = f"https://linkedin.com/in/{slugify(full_name)}"

    if not enriched.get("phone"):
        enriched["phone"] = ""

    if not enriched.get("is_decision_maker"):
        title = (enriched.get("title") or "").lower()
        enriched["is_decision_maker"] = title in {
            "ceo", "cto", "cfo", "coo", "founder", "cmo", "crous", "ciso",
            "vice president", "vp", "vp of sales", "chief revenue officer",
            "vp of finance", "vp of engineering", "head of sales", "head of marketing",
        }
        enriched["seniority"] = _seniority_for_title(enriched.get("title")) or enriched.get("seniority") or ""

    return enriched


def enrich_company(company_data: dict) -> dict:
    enriched = dict(company_data)
    if not enriched.get("website") and enriched.get("domain"):
        enriched["website"] = f"https://{enriched['domain']}"
    if not enriched.get("linkedin_url") and enriched.get("name"):
        enriched["linkedin_url"] = f"https://linkedin.com/company/{slugify(enriched['name'])}"
    return enriched


def enrich_lead_payload(company_data: dict) -> dict:
    """Full enrichment pass on a discovered company payload."""
    company = enrich_company(company_data)
    contacts = []
    for c in company.get("contacts", []):
        enriched_contact = enrich_contact(c, company.get("domain") or "")
        contacts.append(enriched_contact)
    company["contacts"] = contacts
    return company


def _seniority_for_title(title: str) -> str:
    if not title:
        return ""
    t = title.lower()
    if t.startswith("c") and t in ("ceo", "cto", "cfo", "coo", "cmo", "ciso"):
        return "C-Level"
    if t.startswith("vp") or "chief" in t:
        return "VP+"
    if t.startswith(("director", "head", "head of")):
        return "Director"
    return "Manager"


def guess_email_pattern(company: dict) -> str:
    domain = company.get("domain") or ""
    if not domain:
        return ""
    return f"{{first}}.{{last}}@{domain}"