from typing import Optional
from pydantic import BaseModel


class ICPCreate(BaseModel):
    raw_input: str
    name: str = ""


class ICPCriteria(BaseModel):
    industries: list[str] = []
    company_size: list[str] = []
    geographies: list[str] = []
    revenue_min: Optional[float] = None
    revenue_max: Optional[float] = None
    tech_stack: list[str] = []
    job_titles: list[str] = []
    keywords: list[str] = []
    funding_status: str = ""
    notes: str = ""


class ICPUpdate(BaseModel):
    name: str = ""
    industries: list[str] = []
    company_size: list[str] = []
    geographies: list[str] = []
    revenue_min: Optional[float] = None
    revenue_max: Optional[float] = None
    tech_stack: list[str] = []
    job_titles: list[str] = []
    keywords: list[str] = []
    funding_status: str = ""
    notes: str = ""


class ICPOut(BaseModel):
    id: int
    name: str
    raw_input: str
    industries: list[str]
    company_size: list[str]
    geographies: list[str]
    revenue_min: Optional[float] = None
    revenue_max: Optional[float] = None
    tech_stack: list[str]
    job_titles: list[str]
    keywords: list[str]
    funding_status: str = ""
    notes: str = ""
    created_at: Optional[str] = None

    class Config:
        from_attributes = True
