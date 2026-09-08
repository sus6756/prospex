import asyncio

from data_sources.base import BaseDataSource
from data_sources.mock_sources import MockWebScrapeSource, MockCrunchbaseSource, MockLinkedInSource
from data_sources.hunter_io import HunterIOSource
from utils.helpers import loads_json

SOURCES_REGISTRY: dict[str, BaseDataSource] = {
    "mock_web": MockWebScrapeSource(),
    "mock_crunchbase": MockCrunchbaseSource(),
    "mock_linkedin": MockLinkedInSource(),
    "hunter_io": HunterIOSource(),
}

ALL_SOURCES = list(SOURCES_REGISTRY.keys())


def normalize_criteria(icp_obj) -> dict:
    return {
        "industries": loads_json(icp_obj.industries),
        "company_size": loads_json(icp_obj.company_size),
        "geographies": loads_json(icp_obj.geographies),
        "revenue_min": icp_obj.revenue_min,
        "revenue_max": icp_obj.revenue_max,
        "tech_stack": loads_json(icp_obj.tech_stack),
        "job_titles": loads_json(icp_obj.job_titles),
        "keywords": loads_json(icp_obj.keywords),
        "funding_status": icp_obj.funding_status or "",
    }


async def discover_from_sources(criteria: dict, sources: list[str] | None = None, limit: int = 25) -> list[dict]:
    selected = sources or ALL_SOURCES
    tasks = []
    for name in selected:
        source = SOURCES_REGISTRY.get(name)
        if source:
            tasks.append(source.discover(criteria, limit=limit))

    results: list[dict] = []
    if tasks:
        gathered = await asyncio.gather(*tasks, return_exceptions=True)
        for res in gathered:
            if isinstance(res, Exception):
                continue
            results.extend([r.to_dict() for r in res])
    return results