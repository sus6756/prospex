from typing import Optional
from pydantic import BaseModel


class CompanyOut(BaseModel):
    id: int
    name: str
    domain: str = ""
    industry: str = ""
    description: str = ""
    size: str = ""
    location: str = ""
    country: str = ""
    website: str = ""
    linkedin_url: str = ""
    phone: str = ""
    annual_revenue: Optional[float] = None
    employee_count: Optional[int] = None
    tech_stack: list[str] = []

    class Config:
        from_attributes = True


class ContactOut(BaseModel):
    id: int
    full_name: str = ""
    first_name: str = ""
    last_name: str = ""
    title: str = ""
    email: str = ""
    phone: str = ""
    linkedin_url: str = ""
    location: str = ""
    is_decision_maker: bool = False
    seniority: str = ""

    class Config:
        from_attributes = True


class LeadOut(BaseModel):
    id: int
    icp_id: int
    owner_id: int
    score: float = 0.0
    score_breakdown: dict | list = {}
    score_explanation: str = ""
    status: str = "new"
    source: str = ""
    is_duplicate: bool = False
    created_at: Optional[str] = None
    company: Optional[CompanyOut] = None
    contacts: list[ContactOut] = []

    class Config:
        from_attributes = True


class LeadListOut(BaseModel):
    total: int
    leads: list[LeadOut]


class DiscoveryRequest(BaseModel):
    icp_id: int
    sources: list[str] = ["mock_web", "mock_crunchbase", "mock_linkedin", "hunter_io"]


class DiscoveryResult(BaseModel):
    lead_ids: list[int]
    total_discovered: int
    enriched_count: int
    scored_count: int
    duplicates_merged: int


class ExportOut(BaseModel):
    filename: str
    content: str
    media_type: str


class ScoreBreakdownItem(BaseModel):
    criterion: str
    score: float
    weight: float
    reason: str


class LeadBulkStatusIn(BaseModel):
    lead_ids: list[int]
    status: str


class LeadBulkStatusOut(BaseModel):
    updated: int
