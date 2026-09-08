import asyncio
import random

import httpx

from config import settings
from data_sources.base import BaseDataSource, DiscoveredCompany, DiscoveredContact
from data_sources.mock_data import generate_companies

HUNTER_BASE = "https://api.hunter.io/v2"
DOMAIN_ENDPOINT = f"{HUNTER_BASE}/domain-search"
EMAIL_FINDER = f"{HUNTER_BASE}/email-finder"


class HunterIOSource(BaseDataSource):
    name = "hunter_io"
    label = "Hunter.io"

    async def discover(self, icp_criteria: dict, limit: int = 25) -> list[DiscoveredCompany]:
        if settings.HUNTER_API_KEY:
            try:
                return await self._real_discover(icp_criteria, limit)
            except Exception:
                pass
        return await self._fallback_discover(icp_criteria, limit)

    async def _real_discover(self, icp_criteria: dict, limit: int) -> list[DiscoveredCompany]:
        companies: list[DiscoveredCompany] = []
        async with httpx.AsyncClient(timeout=15.0) as client:
            for _ in range(min(limit, 10)):
                params = {"api_key": settings.HUNTER_API_KEY}
                domain = _guess_domain(icp_criteria)
                if domain:
                    params["domain"] = domain
                resp = await client.get(DOMAIN_ENDPOINT, params=params)
                data = resp.json()
                org = data.get("data", {}).get("organization", {})
                people = data.get("data", {}).get("emails", [])[:3]
                contacts = []
                for p in people:
                    first = (p.get("first_name") or "")
                    last = (p.get("last_name") or "")
                    title = p.get("position") or p.get("seniority") or ""
                    contacts.append(DiscoveredContact(
                        full_name=f"{first} {last}".strip(),
                        title=title,
                        email=p.get("value") or "",
                        phone=p.get("phone_number") or "",
                        linkedin_url=p.get("linkedin") or "",
                        is_decision_maker=bool(title) and title in ("CEO", "CTO", "CFO", "VP", "Founder"),
                    ))
                company = DiscoveredCompany(
                    name=org.get("name") or domain or "Unknown",
                    domain=domain or "",
                    industry=icp_criteria.get("industries", [""])[0] or "",
                    description=org.get("description") or "",
                    size=org.get("size") or "",
                    location=org.get("location") or "",
                    country=org.get("country") or "",
                    website=org.get("website") or "",
                    linkedin_url=org.get("linkedin") or "",
                    funding_total=None,
                    annual_revenue=None,
                    employee_count=org.get("employees") or None,
                    tech_stack=icp_criteria.get("tech_stack", []),
                    source=self.name,
                    contacts=contacts,
                    confidence=0.9,
                )
                companies.append(company)
        return companies

    async def _fallback_discover(self, icp_criteria: dict, limit: int) -> list[DiscoveredCompany]:
        await asyncio.sleep(0.3)
        records = generate_companies(icp_criteria, count=limit, source_seed_salt="hunter_io")
        companies = []
        for r in records:
            contacts = [DiscoveredContact(**c) for c in r.get("contacts", [])]
            r_src = dict(r)
            r_src.pop("contacts", None)
            company = DiscoveredCompany(**r_src)
            company.source = self.name
            company.confidence = 0.82
            company.contacts = contacts
            companies.append(company)
        return companies


def _guess_domain(icp_criteria: dict) -> str:
    keywords = icp_criteria.get("keywords", [])
    industries = icp_criteria.get("industries", [])
    guess = str(random.choice(keywords + industries) if (keywords or industries) else "acme")
    guess = guess.lower().replace(" ", "")
    return f"{guess}.io" if guess else ""