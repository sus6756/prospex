import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import asc, desc, func, or_
from sqlalchemy.orm import Session, joinedload

from database import get_db
from models import Company, Contact, ICP, Lead, User
from routers.deps import get_current_user
from schemas.lead import LeadBulkStatusIn, LeadBulkStatusOut, LeadListOut, LeadOut
from utils.helpers import loads_json

router = APIRouter(prefix="/api/leads", tags=["leads"])


def _lead_to_out(lead: Lead) -> LeadOut:
    company_out = None
    if lead.company:
        company = lead.company
        company_out = dict(
            id=company.id,
            name=company.name or "",
            domain=company.domain or "",
            industry=company.industry or "",
            description=company.description or "",
            size=company.size or "",
            location=company.location or "",
            country=company.country or "",
            website=company.website or "",
            linkedin_url=company.linkedin_url or "",
            phone=company.phone or "",
            annual_revenue=company.annual_revenue,
            employee_count=company.employee_count,
            tech_stack=loads_json(company.tech_stack),
        )

    contacts_out = []
    contacts = lead.contacts if getattr(lead, "contacts", None) else []
    for c in (contacts or []):
        contact_out = dict(
            id=c.id,
            full_name=c.full_name or "",
            first_name=c.first_name or "",
            last_name=c.last_name or "",
            title=c.title or "",
            email=c.email or "",
            phone=c.phone or "",
            linkedin_url=c.linkedin_url or "",
            location=c.location or "",
            is_decision_maker=bool(c.is_decision_maker),
            seniority=c.seniority or "",
        )
        contacts_out.append(contact_out)

    return LeadOut(
        id=lead.id,
        icp_id=lead.icp_id,
        owner_id=lead.owner_id,
        score=round(lead.score or 0, 1) if lead.score else 0,
        score_breakdown=loads_json(lead.score_breakdown, {}),
        score_explanation=lead.score_explanation or "",
        status=lead.status or "new",
        source=lead.source or "",
        is_duplicate=bool(lead.is_duplicate),
        created_at=lead.created_at.isoformat() if lead.created_at else None,
        company=company_out,
        contacts=contacts_out,
    )


@router.get("", response_model=LeadListOut)
def list_leads(
    icp_id: Optional[int] = None,
    q: Optional[str] = None,
    min_score: Optional[float] = Query(default=None, ge=0, le=100),
    max_score: Optional[float] = Query(default=None, ge=0, le=100),
    status: Optional[str] = None,
    industry: Optional[str] = None,
    country: Optional[str] = None,
    source: Optional[str] = None,
    include_duplicates: bool = True,
    sort_by: str = "score",
    sort_order: str = "desc",
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = (
        db.query(Lead)
        .options(joinedload(Lead.company), joinedload(Lead.contacts))
        .filter(Lead.owner_id == current_user.id)
    )

    if icp_id:
        owned_icp = db.query(ICP).filter(ICP.id == icp_id, ICP.owner_id == current_user.id).first()
        if not owned_icp:
            raise HTTPException(status_code=404, detail="ICP not found")
        query = query.filter(Lead.icp_id == icp_id)
    if min_score is not None:
        query = query.filter(Lead.score >= min_score)
    if max_score is not None:
        query = query.filter(Lead.score <= max_score)
    if status:
        query = query.filter(Lead.status == status)
    if not include_duplicates:
        query = query.filter(Lead.is_duplicate == False)  # noqa: E712
    if industry:
        query = query.join(Lead.company).filter(Company.industry.ilike(f"%{industry}%"))
    if country:
        query = query.join(Lead.company).filter(Company.country.ilike(f"%{country}%"))
    if source:
        query = query.filter(Lead.source == source)
    if q:
        query = query.join(Lead.company, isouter=True).join(Lead.contacts, isouter=True).filter(
            or_(
                Company.name.ilike(f"%{q}%"),
                Company.domain.ilike(f"%{q}%"),
                Company.description.ilike(f"%{q}%"),
                Contact.full_name.ilike(f"%{q}%"),
                Contact.title.ilike(f"%{q}%"),
                Contact.email.ilike(f"%{q}%"),
            )
        )

    order_dir = desc if sort_order == "desc" else asc
    order_cols = {
        "score": Lead.score,
        "created_at": Lead.created_at,
        "name": Company.name,
    }
    col = order_cols.get(sort_by, Lead.score)
    query = query.order_by(order_dir(col)).distinct()

    total = query.count()
    query = query.order_by(order_dir(col)).limit(limit).offset(offset)
    leads = query.all()
    return LeadListOut(total=total, leads=[_lead_to_out(l) for l in leads])


@router.get("/{lead_id}", response_model=LeadOut)
def get_lead(lead_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    lead = (
        db.query(Lead)
        .options(joinedload(Lead.company), joinedload(Lead.contacts))
        .filter(Lead.id == lead_id, Lead.owner_id == current_user.id)
        .first()
    )
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return _lead_to_out(lead)


@router.patch("/{lead_id}", response_model=LeadOut)
def update_lead_status(
    lead_id: int,
    status: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.owner_id == current_user.id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    lead.status = status
    db.commit()
    db.refresh(lead)
    return _lead_to_out(lead)


@router.get("/stats/summary")
def lead_stats(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    leads = db.query(Lead).filter(Lead.owner_id == current_user.id).all()
    buckets = [
        {"range": "0-19", "min": None, "max": 20, "count": 0},
        {"range": "20-39", "min": 20, "max": 40, "count": 0},
        {"range": "40-59", "min": 40, "max": 60, "count": 0},
        {"range": "60-79", "min": 60, "max": 80, "count": 0},
        {"range": "80+", "min": 80, "max": None, "count": 0},
    ]
    if not leads:
        return {
            "total": 0,
            "avg_score": 0,
            "top_score": 0,
            "status_counts": {},
            "source_counts": {},
            "countries": [],
            "score_distribution": buckets,
            "active_icps": 0,
        }

    scores = [l.score or 0 for l in leads]
    status_counts = {}
    source_counts = {}
    countries = {}
    for lead in leads:
        status_counts[lead.status or "new"] = status_counts.get(lead.status or "new", 0) + 1
        source_counts[lead.source or "unknown"] = source_counts.get(lead.source or "unknown", 0) + 1
        if lead.company and lead.company.country:
            countries[lead.company.country] = countries.get(lead.company.country, 0) + 1
        for bucket in buckets:
            if bucket["min"] is None:
                in_bucket = (lead.score or 0) < bucket["max"]
            elif bucket["max"] is None:
                in_bucket = (lead.score or 0) >= bucket["min"]
            else:
                in_bucket = bucket["min"] <= (lead.score or 0) < bucket["max"]
            if in_bucket:
                bucket["count"] += 1
                break

    active_icps = (
        db.query(Lead.icp_id).filter(Lead.owner_id == current_user.id).distinct().count()
    )

    icp_counts = {}
    for row in db.query(Lead.icp_id, func.count(Lead.id)).filter(Lead.owner_id == current_user.id).group_by(Lead.icp_id).all():
        icp_counts[row[0]] = row[1]

    return {
        "total": len(leads),
        "avg_score": round(sum(scores) / len(scores), 1) if scores else 0,
        "top_score": round(max(scores), 1) if scores else 0,
        "status_counts": status_counts,
        "source_counts": source_counts,
        "countries": sorted(countries.items(), key=lambda x: -x[1])[:10],
        "score_distribution": buckets,
        "active_icps": active_icps,
        "icp_counts": icp_counts,
    }


@router.post("/bulk-status", response_model=LeadBulkStatusOut)
def bulk_update_status(
    payload: LeadBulkStatusIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not payload.lead_ids:
        return LeadBulkStatusOut(updated=0)
    updated = (
        db.query(Lead)
        .filter(Lead.id.in_(payload.lead_ids), Lead.owner_id == current_user.id)
        .update({Lead.status: payload.status}, synchronize_session=False)
    )
    db.commit()
    return LeadBulkStatusOut(updated=updated)