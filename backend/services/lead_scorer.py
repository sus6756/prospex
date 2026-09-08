import json

from utils.ai_client import ai_available, chat_json
from utils.helpers import clamp_score, loads_json

SCORING_SYSTEM_PROMPT = """You are a B2B lead qualification expert. Score a lead against an Ideal Customer Profile (ICP).

Return strict JSON with these keys:
{
  "score": "integer 0-100 overall match score",
  "breakdown": [
    {"criterion": "e.g. 'Industry'", "score": "0-100", "weight": "0-1", "reason": "string"}
  ],
  "explanation": "2-3 sentence human-readable summary of why this lead scored this way"
}

Scoring rubric:
- Industry match (weight 0.30)
- Company size match (weight 0.20)
- Geography match (weight 0.15)
- Contact/decision-maker relevance (weight 0.20)
- Tech stack / keyword alignment (weight 0.15)

Be fair, precise, and explain reasoning clearly."""
SCORING_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "score": {"type": "integer"},
        "breakdown": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "criterion": {"type": "string"},
                    "score": {"type": "integer"},
                    "weight": {"type": "number"},
                    "reason": {"type": "string"},
                },
                "required": ["criterion", "score", "weight", "reason"],
                "additionalProperties": False,
            },
        },
        "explanation": {"type": "string"},
    },
    "required": ["score", "breakdown", "explanation"],
    "additionalProperties": False,
}


def score_lead(icp_criteria: dict, company: dict) -> dict:
    """Score a discovered company against the ICP. Uses AI when available, else heuristic."""
    if ai_available():
        try:
            return _ai_score(icp_criteria, company)
        except Exception:
            pass
    return _heuristic_score(icp_criteria, company)


def _ai_score(icp_criteria: dict, company: dict) -> dict:
    prompt = (
        "ICP criteria (JSON):\n"
        + json.dumps(icp_criteria, default=str)
        + "\n\nCandidate lead (JSON):\n"
        + json.dumps(
            {
                "name": company.get("name"),
                "domain": company.get("domain"),
                "industry": company.get("industry"),
                "size": company.get("size"),
                "location": company.get("location"),
                "country": company.get("country"),
                "tech_stack": company.get("tech_stack") or [],
                "description": company.get("description"),
                "employee_count": company.get("employee_count"),
                "annual_revenue": company.get("annual_revenue"),
                "contacts": [
                    {"name": c.get("full_name"), "title": c.get("title"), "email": c.get("email")}
                    for c in company.get("contacts", [])
                ],
            },
            default=str,
        )
    )
    raw = chat_json(SCORING_SYSTEM_PROMPT, prompt, json_schema=SCORING_JSON_SCHEMA, temperature=0.2, max_tokens=900)
    breakdown = raw.get("breakdown", [])
    score = clamp_score(float(raw.get("score", 0)))
    return {
        "score": score,
        "breakdown": breakdown,
        "explanation": raw.get("explanation", ""),
    }


def _heuristic_score(icp_criteria: dict, company: dict) -> dict:
    breakdown = []
    industries = [i.lower() for i in icp_criteria.get("industries", [])]
    industry_match = 100 if (not industries or (company.get("industry") or "").lower() in industries) else 20
    breakdown.append({"criterion": "Industry", "score": industry_match, "weight": 0.30,
                      "reason": ("Industry matches ICP." if industry_match > 50 else "Industry does not match ICP.")})

    sizes = [s.lower() for s in icp_criteria.get("company_size", [])]
    size_match = 100 if (not sizes or (company.get("size") or "").lower() in sizes) else 50
    breakdown.append({"criterion": "Company Size", "score": size_match, "weight": 0.20,
                      "reason": "Company size within target range." if size_match > 50 else "Company size outside target range."})

    geos = [g.lower() for g in icp_criteria.get("geographies", [])]
    geo_match = 100 if (not geos or (company.get("country") or "").lower() in geos) else 30
    breakdown.append({"criterion": "Geography", "score": geo_match, "weight": 0.15,
                      "reason": "In target geography." if geo_match > 50 else "Outside target geography."})

    titles = [t.lower() for t in icp_criteria.get("job_titles", [])]
    contacts = company.get("contacts", [])
    if titles:
        found_relevance = any(
            any(term in (c.get("title") or "").lower() for term in titles) or c.get("is_decision_maker")
            for c in contacts
        )
        contact_match = 100 if found_relevance else 40
    elif contacts:
        contact_match = 90
    else:
        contact_match = 30
    breakdown.append({"criterion": "Contact Relevance", "score": contact_match, "weight": 0.20,
                      "reason": "Relevant decision-makers found." if contact_match > 50 else "Few/no relevant decision-makers."})

    tech_stack = [t.lower() for t in icp_criteria.get("tech_stack", [])]
    keywords = [k.lower() for k in icp_criteria.get("keywords", [])]
    company_text = f"{company.get('description', '')} {company.get('industry', '')}".lower()
    alignment = 0
    if tech_stack:
        hits = sum(1 for t in tech_stack if t in " ".join(company.get("tech_stack", [])).lower())
        alignment += hits / len(tech_stack) * 100
    if keywords:
        hits = sum(1 for k in keywords if k in company_text)
        alignment += hits / len(keywords) * 100
    alignment = alignment / (2 if tech_stack and keywords else 1) if (tech_stack or keywords) else 70
    breakdown.append({"criterion": "Tech/Keyword Alignment", "score": round(clamp_score(alignment), 1), "weight": 0.15,
                      "reason": "Stack/keywords overlap with ICP." if alignment > 50 else "Limited tech/keyword overlap."})

    weighted = sum(b["score"] * b["weight"] for b in breakdown)
    explanation = (
        f"{company.get('name')} scored {round(weighted)}/100. "
        + ("Strong fit" if weighted >= 75 else "Moderate fit" if weighted >= 50 else "Weak fit")
        + f" for this ICP, primarily driven by {'industry alignment' if industry_match > 50 else 'gaps in industry alignment'}."
    )
    return {"score": round(clamp_score(weighted), 1), "breakdown": breakdown, "explanation": explanation}


def score_from_lead_db(icp_criteria: dict, company_dict: dict) -> dict:
    return score_lead(icp_criteria, company_dict)