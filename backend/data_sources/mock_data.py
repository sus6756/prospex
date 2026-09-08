import hashlib
import random
import re

COMPANY_POOL = [
    {"name": "Nexora Cloud", "industry": "saas", "size": "51-200", "country": "United States", "employees": 140, "founded": 2016},
    {"name": "Brightloop Analytics", "industry": "data & analytics", "size": "1-50", "country": "United States", "employees": 38, "founded": 2020},
    {"name": "Fermion Health", "industry": "healthcare", "size": "201-500", "country": "Germany", "employees": 320, "founded": 2012},
    {"name": "Cartiserve Commerce", "industry": "e-commerce", "size": "51-200", "country": "United Kingdom", "employees": 95, "founded": 2018},
    {"name": "Primevault Finance", "industry": "fintech", "size": "501-1000", "country": "United States", "employees": 640, "founded": 2014},
    {"name": "Gridworks Energy", "industry": "energy", "size": "1001-5000", "country": "Canada", "employees": 2100, "founded": 2008},
    {"name": "Synthedge AI", "industry": "artificial intelligence", "size": "1-50", "country": "United States", "employees": 45, "founded": 2021},
    {"name": "MediTrust Systems", "industry": "healthcare", "size": "1001-5000", "country": "United States", "employees": 3500, "founded": 2005},
    {"name": "LogiStay Travel", "industry": "travel", "size": "201-500", "country": "France", "employees": 260, "founded": 2013},
    {"name": "Swiftdocs Legal", "industry": "legal", "size": "51-200", "country": "United Kingdom", "employees": 85, "founded": 2019},
    {"name": "Hirelane HR", "industry": "human resources", "size": "1-50", "country": "United States", "employees": 30, "founded": 2022},
    {"name": "Blueforge Manufacturing", "industry": "manufacturing", "size": "1001-5000", "country": "Germany", "employees": 4200, "founded": 1999},
    {"name": "Cognitex Security", "industry": "cybersecurity", "size": "51-200", "country": "Israel", "employees": 160, "founded": 2017},
    {"name": "Freshfarm Foods", "industry": "food & beverage", "size": "201-500", "country": "United States", "employees": 310, "founded": 2010},
    {"name": "Urbanlift Realty", "industry": "real estate", "size": "1-50", "country": "Australia", "employees": 42, "founded": 2015},
    {"name": "Vantegra Robotics", "industry": "automotive", "size": "51-200", "country": "Japan", "employees": 130, "founded": 2018},
    {"name": "Nimbusmart Media", "industry": "media", "size": "1-50", "country": "Netherlands", "employees": 27, "founded": 2021},
    {"name": "Quantia Bio", "industry": "healthcare", "size": "201-500", "country": "Switzerland", "employees": 380, "founded": 2011},
    {"name": "Terraform Logistics", "industry": "logistics", "size": "1001-5000", "country": "Singapore", "employees": 2700, "founded": 2006},
    {"name": "Pixelforge Gaming", "industry": "gaming", "size": "51-200", "country": "Sweden", "employees": 110, "founded": 2017},
    {"name": "Aperture Construction", "industry": "construction", "size": "201-500", "country": "United States", "employees": 340, "founded": 2003},
    {"name": "Viviero Education", "industry": "education", "size": "51-200", "country": "United Kingdom", "employees": 75, "founded": 2016},
    {"name": "Pentos Intranet", "industry": "saas", "size": "5000+", "country": "United States", "employees": 8500, "founded": 2002},
    {"name": "Cirro Finance", "industry": "fintech", "size": "51-200", "country": "Brazil", "employees": 90, "founded": 2019},
    {"name": "Halcyon Cloud", "industry": "saas", "size": "201-500", "country": "Ireland", "employees": 230, "founded": 2015},
    {"name": "OmniRetail Hub", "industry": "e-commerce", "size": "5000+", "country": "China", "employees": 12000, "founded": 2004},
    {"name": "Vertex Bioethics", "industry": "healthcare", "size": "1-50", "country": "United States", "employees": 35, "founded": 2023},
    {"name": "Solarflare Energy", "industry": "energy", "size": "501-1000", "country": "Spain", "employees": 720, "founded": 2012},
    {"name": "Kernelbase OS", "industry": "software", "size": "1001-5000", "country": "United States", "employees": 1600, "founded": 2007},
    {"name": "Wavetide Aqua", "industry": "food & beverage", "size": "51-200", "country": "New Zealand", "employees": 60, "founded": 2014},
]

TITLE_MAP = [
    "CEO", "CTO", "CFO", "COO", "Founder", "VP of Sales", "Head of Marketing",
    "VP of Engineering", "Director of Operations", "Head of Product", "CMO",
    "VP of Finance", "Chief Revenue Officer", "Head of Talent",
]

INDUSTRY_KEYWORDS = {
    "saas": "cloud software", "software": "software solutions", "fintech": "financial technology",
    "healthcare": "medical care", "e-commerce": "online commerce", "manufacturing": "industrial production",
    "financial services": "finance", "retail": "retail", "logistics": "supply chain",
    "education": "learning", "marketing": "marketing automation", "cybersecurity": "data security",
    "artificial intelligence": "machine learning", "construction": "construction", "real estate": "property",
    "human resources": "workforce management", "travel": "travel", "food & beverage": "food",
    "media": "media", "automotive": "automotive", "energy": "clean energy", "gaming": "gaming",
    "legal": "legal", "data & analytics": "business intelligence",
}

FIRST_NAMES = ["James", "Sarah", "Michael", "Emma", "David", "Olivia", "Daniel", "Sophia", "Matthew", "Isabella", "Chris", "Ava", "Andrew", "Mia", "Ryan", "Charlotte", "Thomas", "Amelia", "Kevin", "Harper"]
LAST_NAMES = ["Smith", "Johnson", "Brown", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson", "White"]

INDUSTRY_TITLE_BIAS = {
    "fintech": ["CFO", "VP of Finance", "CEO"],
    "healthcare": ["CEO", "COO", "Head of Product"],
    "cybersecurity": ["CTO", "CISO"],
    "saas": ["CEO", "VP of Sales", "CMO", "Head of Marketing"],
    "artificial intelligence": ["CTO", "CEO", "VP of Engineering"],
}


def _is_decision_maker(title: str) -> bool:
    return title in {
        "CEO", "CTO", "CFO", "COO", "Founder", "VP of Sales", "CMO",
        "VP of Engineering", "Chief Revenue Officer", "VP of Finance", "CISO",
    }


def _seniority(title: str) -> str:
    if title.startswith("C"):
        return "C-Level"
    if title.startswith("VP") or title.startswith("Chief"):
        return "VP+"
    if title.startswith("Director") or title.startswith("Head"):
        return "Director"
    return "Manager"


def _deterministic_rand(seed: str) -> random.Random:
    return random.Random(int(hashlib.md5(seed.encode()).hexdigest()[:8], 16))


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", name.lower())


def _domain_for(name: str, country: str) -> str:
    base = _slug(name)
    country_tld = {
        "United States": ".com", "Germany": ".de", "United Kingdom": ".co.uk",
        "Canada": ".ca", "France": ".fr", "Israel": ".com", "Japan": ".jp",
        "Australia": ".com.au", "Netherlands": ".nl", "Switzerland": ".ch",
        "Singapore": ".sg", "Sweden": ".se", "Brazil": ".com.br", "Ireland": ".ie",
        "China": ".cn", "Spain": ".es", "New Zealand": ".co.nz", "India": ".in",
    }
    return f"{base}{country_tld.get(country, '.com')}"


def _email_for(first: str, last: str, domain: str) -> str:
    return f"{first.lower()}.{last.lower()}@{domain}"


SIZE_POOL_MAP = {
    "startup": "1-50", "small": "1-50", "seed": "1-50", "1-50": "1-50", "1-100": "1-50",
    "mid-sized": "51-200", "mid-size": "51-200", "medium": "51-200", "51-200": "51-200", "51-250": "51-200",
    "201-500": "201-500", "251-500": "201-500",
    "501-1000": "501-1000", "500-1000": "501-1000",
    "1001-5000": "1001-5000",
    "5000+": "5000+", "large": "5000+", "enterprise": "5000+",
}


def _normalize_sizes(sizes: list[str]) -> list[str]:
    out = []
    for s in sizes:
        normalized = SIZE_POOL_MAP.get(s.lower(), s.lower())
        if normalized not in out:
            out.append(normalized)
    return out


def generate_companies(icp_criteria: dict, count: int = 20, source_seed_salt: str = "") -> list[dict]:
    industries = [i.lower() for i in icp_criteria.get("industries", [])]
    countries = [c.lower() for c in icp_criteria.get("geographies", []) if c]
    sizes = _normalize_sizes(icp_criteria.get("company_size", []))

    def matches(company: dict) -> bool:
        if industries and company["industry"].lower() not in industries:
            return False
        if sizes and company["size"].lower() not in sizes:
            return False
        if countries and company["country"].lower() not in countries:
            return False
        return True

    matched = [c for c in COMPANY_POOL if matches(c)]
    selected = list(matched[:count])

    if len(selected) < count:
        selected.extend(_synthesize_matching(count - len(selected), icp_criteria))

    results = []
    for i, company in enumerate(selected):
        rng = _deterministic_rand(company["name"] + source_seed_salt)
        domain = _domain_for(company["name"], company["country"])
        industry = company["industry"].lower()
        desc_keyword = INDUSTRY_KEYWORDS.get(industry, industry)
        company_record = {
            "name": company["name"],
            "domain": domain,
            "industry": industry.title(),
            "description": f"{company['name']} is a leading provider of {desc_keyword} solutions serving {company['country']} and global markets.",
            "size": company["size"],
            "location": f"{company['country']} (remote-friendly)",
            "country": company["country"],
            "founded": company["founded"],
            "website": f"https://{domain}",
            "linkedin_url": f"https://linkedin.com/company/{_slug(company['name'])}",
            "phone": f"+1-{rng.randint(200, 989)}-{rng.randint(200, 989)}-{rng.randint(1000, 9999)}",
            "annual_revenue": round(rng.uniform(2e6, 4e8), 0),
            "funding_total": round(rng.uniform(0, 1.2e8), 0) if rng.random() > 0.4 else None,
            "employee_count": company["employees"],
            "tech_stack": _pick_tech_stack(rng, industries),
            "source": source_seed_salt or "mock_web",
        }
        company_record["contacts"] = _generate_contacts(company_record, rng)
        results.append(company_record)

    return results


def _synthesize_matching(needed: int, icp_criteria: dict) -> list[dict]:
    industries = [i.lower() for i in icp_criteria.get("industries", [])]
    countries = [c.lower() for c in icp_criteria.get("geographies", []) if c]
    sizes = [s.lower() for s in icp_criteria.get("company_size", [])]

    industry = industries[0] if industries else _random_industry()
    country = countries[0].title() if countries else "United States"
    size = sizes[0] if sizes else "51-200"
    employees = {
        "1-50": 30, "51-200": 120, "201-500": 300, "501-1000": 700,
        "1001-5000": 2500, "5000+": 8000, "startup": 25, "enterprise": 8000,
    }.get(size, 120)

    companies = []
    for i in range(needed):
        name = f"{_random_prefix(i)} {_random_suffix(i)}"
        companies.append({
            "name": name,
            "industry": industry,
            "size": size,
            "country": country,
            "employees": employees,
            "founded": 2003 + (i % 19),
        })
    return companies


def _random_industry() -> str:
    return random.choice(list(INDUSTRY_KEYWORDS.keys()))


def _pick_tech_stack(rng: random.Random, industries: list[str]) -> list[str]:
    stack = [
        "Cloud (AWS)", "Docker", "Kubernetes", "React", "Node.js", "Python",
        "PostgreSQL", "Salesforce", "HubSpot", "Snowflake", "GCP", "SAP",
        "Stripe", "Shopify", "Kafka", "Redis",
    ]
    selected = rng.sample(stack, min(rng.randint(2, 5), len(stack)))
    if "cybersecurity" in industries:
        selected.append("Okta")
    if "fintech" in industries:
        selected.append("Stripe")
    if "e-commerce" in industries:
        selected.append("Shopify")
    return list(dict.fromkeys(selected))


def _generate_contacts(company: dict, rng: random.Random) -> list[dict]:
    industry = company["industry"].lower()
    preferred = INDUSTRY_TITLE_BIAS.get(industry, ["CEO", "VP of Sales", "Head of Marketing"])
    titles = []
    for t in preferred:
        if t not in titles and rng.random() > 0.25:
            titles.append(t)
    while len(titles) < rng.randint(2, 4):
        cand = rng.choice(TITLE_MAP)
        if cand not in titles:
            titles.append(cand)

    contacts = []
    for title in titles:
        if title in {"CISO", "SVP"}:
            continue
        first = rng.choice(FIRST_NAMES)
        last = rng.choice(LAST_NAMES)
        contacts.append({
            "full_name": f"{first} {last}",
            "title": title,
            "email": _email_for(first, last, company["domain"]),
            "phone": f"+1-{rng.randint(200, 989)}-{rng.randint(200, 989)}-{rng.randint(1000, 9999)}",
            "linkedin_url": f"https://linkedin.com/in/{_slug(first) + _slug(last)}",
            "location": company["location"],
            "is_decision_maker": _is_decision_maker(title),
            "seniority": _seniority(title),
        })
    return contacts


def _random_prefix(i: int) -> str:
    return ["Apex", "Nova", "Quantum", "Vertex", "Prime", "Stellar", "Core", "Zenith", "Orbit", "Rocksteady"][i % 10]


def _random_suffix(i: int) -> str:
    return ["Labs", "Group", "Solutions", "Systems", "Networks", "Digital", "Technologies", "Software", "Industries", "Works"][i % 10]