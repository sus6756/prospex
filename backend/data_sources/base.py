from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DiscoveredCompany:
    name: str
    domain: str
    industry: str = ""
    description: str = ""
    size: str = ""
    location: str = ""
    country: str = ""
    founded: Optional[int] = None
    website: str = ""
    linkedin_url: str = ""
    phone: str = ""
    annual_revenue: Optional[float] = None
    funding_total: Optional[float] = None
    employee_count: Optional[int] = None
    tech_stack: list = field(default_factory=list)
    source: str = ""
    contacts: list = field(default_factory=list)
    confidence: float = 0.5

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "domain": self.domain,
            "industry": self.industry,
            "description": self.description,
            "size": self.size,
            "location": self.location,
            "country": self.country,
            "founded": self.founded,
            "website": self.website,
            "linkedin_url": self.linkedin_url,
            "phone": self.phone,
            "annual_revenue": self.annual_revenue,
            "funding_total": self.funding_total,
            "employee_count": self.employee_count,
            "tech_stack": self.tech_stack,
            "source": self.source,
            "contacts": [c.to_dict() if hasattr(c, "to_dict") else c for c in self.contacts],
            "confidence": self.confidence,
        }


@dataclass
class DiscoveredContact:
    full_name: str
    title: str = ""
    email: str = ""
    phone: str = ""
    linkedin_url: str = ""
    location: str = ""
    is_decision_maker: bool = False
    seniority: str = ""

    def to_dict(self) -> dict:
        return {
            "full_name": self.full_name,
            "title": self.title,
            "email": self.email,
            "phone": self.phone,
            "linkedin_url": self.linkedin_url,
            "location": self.location,
            "is_decision_maker": self.is_decision_maker,
            "seniority": self.seniority,
        }


class BaseDataSource(ABC):
    name: str = "base"
    label: str = "Base Source"

    @abstractmethod
    async def discover(self, icp_criteria: dict, limit: int = 25) -> list[DiscoveredCompany]:
        raise NotImplementedError