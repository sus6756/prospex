import re
from typing import Optional

from utils.ai_client import ai_available, chat_json
from utils.helpers import loads_json
from schemas.icp import ICPCriteria

ICP_SYSTEM_PROMPT = """You are an expert B2B sales and market intelligence analyst.
Extract a structured Ideal Customer Profile (ICP) from the user's natural language description.

Return a strict JSON object with exactly these keys:
{
  "industries": ["list of GICS/NAICS-style industries, lowercase"],
  "company_size": ["e.g. '1-50', '51-200', '201-500', '501-1000', '1001-5000', '5000+', or raw text like 'small', 'startup', 'enterprise'. Normalize to standard ranges when possible."],
  "geographies": ["countries or regions, e.g. 'United States', 'Germany', 'United Kingdom', 'Europe'"],
  "revenue_min": "(number in USD or null)",
  "revenue_max": "(number in USD or null)",
  "tech_stack": ["technologies the company should use, e.g. 'Salesforce', 'Shopify', 'AWS', 'React'"],
  "job_titles": ["decision-maker titles to target, e.g. 'CTO', 'VP of Sales', 'Head of Marketing', 'CEO', 'Founder'"],
  "keywords": ["key phrases that describe the company's offering"],
  "funding_status": "(e.g. 'venture-backed', 'public', 'bootstrapped', 'series b', or empty string)",
  "notes": "a concise 1-2 sentence summary of anything flagged or nuanced"
}

Rules:
- Be precise and conservative; only include criteria that are explicitly or clearly implied.
- Leave empty arrays and nulls for missing criteria.
- Keep notes short."""


def extract_icp(raw_input: str) -> ICPCriteria:
    """Parse a natural-language ICP description into structured criteria."""
    icp = ICPCriteria()
    normalized = raw_input.strip()
    if not normalized:
        return icp

    if ai_available():
        try:
            schema = {
                "type": "object",
                "properties": {
                    "industries": {"type": "array", "items": {"type": "string"}},
                    "company_size": {"type": "array", "items": {"type": "string"}},
                    "geographies": {"type": "array", "items": {"type": "string"}},
                    "revenue_min": {"type": ["number", "null"]},
                    "revenue_max": {"type": ["number", "null"]},
                    "tech_stack": {"type": "array", "items": {"type": "string"}},
                    "job_titles": {"type": "array", "items": {"type": "string"}},
                    "keywords": {"type": "array", "items": {"type": "string"}},
                    "funding_status": {"type": "string"},
                    "notes": {"type": "string"},
                },
                "required": ["industries", "company_size", "geographies", "revenue_min", "revenue_max", "tech_stack", "job_titles", "keywords", "funding_status", "notes"],
                "additionalProperties": False,
            }
            result = chat_json(
                ICP_SYSTEM_PROMPT,
                f"ICP description:\n{normalized}",
                json_schema=schema,
                temperature=0.1,
            )
            icp = ICPCriteria(
                industries=loads_json(__import__("json").dumps(result.get("industries", [])))
                if isinstance(result.get("industries"), list)
                else result.get("industries", []),
                company_size=result.get("company_size", []),
                geographies=result.get("geographies", []),
                revenue_min=result.get("revenue_min"),
                revenue_max=result.get("revenue_max"),
                tech_stack=result.get("tech_stack", []),
                job_titles=result.get("job_titles", []),
                keywords=result.get("keywords", []),
                funding_status=result.get("funding_status", ""),
                notes=result.get("notes", ""),
            )
            return icp
        except Exception:
            pass

    return _heuristic_parse(normalized)


def _heuristic_parse(text: str) -> ICPCriteria:
    """Deterministic fallback extraction when the OpenAI key is absent."""
    icp = ICPCriteria()

    industries = {
        "saas": "saas", "software": "software", "fintech": "fintech", "healthcare": "healthcare",
        "e-commerce": "e-commerce", "ecommerce": "e-commerce", "manufacturing": "manufacturing",
        "finance": "financial services", "retail": "retail", "logistics": "logistics",
        "education": "education", "marketing": "marketing", "cybersecurity": "cybersecurity",
        "ai": "artificial intelligence", "construction": "construction", "real estate": "real estate",
        "hr": "human resources", "travel": "travel", "food": "food & beverage",
        "media": "media", "automotive": "automotive", "energy": "energy",
    }
    for word, industry in industries.items():
        if re.search(rf"\b{word}\b", text.lower()):
            if industry not in icp.industries:
                icp.industries.append(industry)

    size_patterns = [
        (r"\b(startup|seed|early[- ]stage|small)\b", "startup"),
        (r"\b(1[-–]\s?5[05]|small[- ]sized|small\s+company)\b", "1-50"),
        (r"\b(51[-–]\s?2[05][05]|mid[- ]sized|mid[- ]sized|medium)\b", "51-200"),
        (r"\b(201[-–]\s?500)\b", "201-500"),
        (r"\b(501[-–]\s?1000|500[-–]\s?1000)\b", "501-1000"),
        (r"\b(1001[-–]\s?5000)\b", "1001-5000"),
        (r"\b(5000\+|large|enterprise|forbes)\b", "5000+"),
    ]
    for pattern, size in size_patterns:
        if re.search(pattern, text.lower()):
            if size not in icp.company_size:
                icp.company_size.append(size)

    geos = {
        "us": "United States", "usa": "United States", "america": "United States",
        "united states": "United States", "europe": "Europe", "uk": "United Kingdom",
        "united kingdom": "United Kingdom", "germany": "Germany", "france": "France",
        "india": "India", "canada": "Canada", "australia": "Australia",
        "germany": "Germany", "asia": "Asia", "brazil": "Brazil", "japan": "Japan",
        "china": "China",
    }
    for word, geo in geos.items():
        if re.search(rf"\b{word}\b", text.lower()):
            if geo not in icp.geographies:
                icp.geographies.append(geo)

    tech = ["salesforce", "shopify", "aws", "react", "python", "sap", "hubspot", "stripe", "snowflake", "salesloft", "slack", "okta"]
    for t in tech:
        if re.search(rf"\b{t}\b", text.lower()):
            icp.tech_stack.append(t)

    titles = ["cto", "cfo", "ceo", "founder", "vp of sales", "sales", "marketing", "head of product", "chief", "director", "head of talent", "vp of engineering", "coo"]
    for title in titles:
        if re.search(rf"\b{title}\b", text.lower()):
            normalized_title = {
                "cto": "CTO", "cfo": "CFO", "ceo": "CEO", "founder": "Founder",
                "vp of sales": "VP of Sales", "sales": "VP of Sales", "marketing": "Head of Marketing",
                "head of product": "Head of Product", "chief": "Chief Officer",
                "director": "Director", "head of talent": "Head of Talent",
                "vp of engineering": "VP of Engineering", "coo": "COO",
            }[title]
            if normalized_title not in icp.job_titles:
                icp.job_titles.append(normalized_title)

    keywords = [k for k in ["b2b", "b2c", "data", "cloud", "enterprise", "growth", "digital transformation"] if k in text.lower()]
    icp.keywords = keywords

    funding = {
        "venture-backed": "venture-backed", "series a": "series-a", "series b": "series-b",
        "series c": "series-c", "public": "public", "bootstrapped": "bootstrapped",
        "private equity": "private-equity",
    }
    for k, v in funding.items():
        if k in text.lower():
            icp.funding_status = v
            break

    return icp