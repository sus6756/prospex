from thefuzz import fuzz

from utils.helpers import normalize_domain


def dedup_key_for_company(company: dict) -> str:
    """Normalized key used for exact-match dedup."""
    domain = normalize_domain(company.get("domain") or "")
    name = (company.get("name") or "").strip().lower()
    return domain or name


def are_duplicates(company_a: dict, company_b: dict, threshold: int = 82) -> bool:
    """Fuzzy duplicate detection on domain / name / email pair."""
    domain_a = normalize_domain(company_a.get("domain") or "")
    domain_b = normalize_domain(company_b.get("domain") or "")
    if domain_a and domain_b and domain_a == domain_b:
        return True

    name_a = (company_a.get("name") or "").strip().lower()
    name_b = (company_b.get("name") or "").strip().lower()
    if name_a and name_b:
        if fuzz.ratio(name_a, name_b) >= threshold:
            return True
        if fuzz.token_set_ratio(name_a, name_b) >= threshold:
            return True

    emails_a = {c.get("email", "").lower() for c in company_a.get("contacts", []) if c.get("email")}
    emails_b = {c.get("email", "").lower() for c in company_b.get("contacts", []) if c.get("email")}
    if emails_a and emails_b and emails_a & emails_b:
        return True

    return False


def merge_companies(primary: dict, duplicate: dict) -> dict:
    """Merge a duplicate into the primary company record, preferring non-empty fields."""
    merged = dict(primary)
    preview_fields = ["industry", "location", "country", "description", "size", "linkdefin_url", "linkedin_url", "phone"]

    for field in preview_fields:
        if not merged.get(field) and duplicate.get(field):
            merged[field] = duplicate[field]

    stores = {
        "tech_stack": "tech_stack",
        "contacts": "contacts",
    }
    for src_key, dst_key in stores.items():
        existing = merged.get(dst_key) or []
        existing_ids = set()
        for item in existing:
            if isinstance(item, dict):
                existing_ids.add(item.get("email") or item.get("full_name"))
        for item in duplicate.get(src_key) or []:
            if isinstance(item, dict):
                marker = item.get("email") or item.get("full_name")
                if marker and marker not in existing_ids:
                    existing.append(item)
                    if item.get("email"):
                        existing_ids.add(marker)
            elif item not in existing:
                existing.append(item)
        merged[dst_key] = existing

    for k in ["employee_count", "annual_revenue", "funding_total"]:
        if not merged.get(k) and duplicate.get(k):
            merged[k] = duplicate[k]

    return merged