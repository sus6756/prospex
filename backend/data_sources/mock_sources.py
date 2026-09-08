import asyncio

from data_sources.base import BaseDataSource, DiscoveredCompany, DiscoveredContact
from data_sources.mock_data import generate_companies


class MockWebScrapeSource(BaseDataSource):
    name = "mock_web"
    label = "Web Scrape (Simulated)"

    async def discover(self, icp_criteria: dict, limit: int = 25) -> list[DiscoveredCompany]:
        await asyncio.sleep(0.4)
        records = generate_companies(icp_criteria, count=limit, source_seed_salt="mock_web")
        companies = []
        for r in records:
            contacts = [DiscoveredContact(**c) for c in r.get("contacts", [])]
            r_src = dict(r)
            r_src.pop("contacts", None)
            company = DiscoveredCompany(**r_src)
            company.source = self.name
            company.confidence = 0.72
            company.contacts = contacts
            companies.append(company)
        return companies


class MockCrunchbaseSource(BaseDataSource):
    name = "mock_crunchbase"
    label = "Crunchbase (Simulated)"

    async def discover(self, icp_criteria: dict, limit: int = 25) -> list[DiscoveredCompany]:
        await asyncio.sleep(0.6)
        records = generate_companies(icp_criteria, count=limit, source_seed_salt="mock_crunchbase")
        companies = []
        for r in records:
            contacts = [DiscoveredContact(**c) for c in r.get("contacts", [])]
            r_src = dict(r)
            r_src.pop("contacts", None)
            company = DiscoveredCompany(**r_src)
            company.source = self.name
            company.funding_total = company.funding_total or 5_000_000
            company.confidence = 0.85
            company.contacts = contacts
            companies.append(company)
        return companies


class MockLinkedInSource(BaseDataSource):
    name = "mock_linkedin"
    label = "LinkedIn (Simulated)"

    async def discover(self, icp_criteria: dict, limit: int = 25) -> list[DiscoveredCompany]:
        await asyncio.sleep(0.8)
        records = generate_companies(icp_criteria, count=limit, source_seed_salt="mock_linkedin")
        companies = []
        for r in records:
            contacts = [
                DiscoveredContact(**c)
                for c in r.get("contacts", [])
                if c.get("is_decision_maker") or c.get("seniority") in ("C-Level", "VP+", "Director")
            ]
            r_src = dict(r)
            r_src.pop("contacts", None)
            company = DiscoveredCompany(**r_src)
            company.source = self.name
            company.linkedin_url = f"https://linkedin.com/company/{r['name'].lower().replace(' ', '-')}"
            company.confidence = 0.78
            company.contacts = contacts
            companies.append(company)
        return companies