import csv
import io
import json
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload

from database import get_db
from models import Lead, User
from routers.deps import get_current_user
from utils.helpers import loads_json

router = APIRouter(prefix="/api/export", tags=["export"])

CORE_FIELDS = [
    "lead_id", "score", "status", "source",
    "company_name", "company_domain", "company_industry", "company_size",
    "company_country", "company_location", "company_website", "company_linkedin",
    "contact_name", "contact_title", "contact_email", "contact_phone", "contact_linkedin",
]


def _flatten_leads(leads: list[Lead]) -> list[dict]:
    rows = []
    for lead in leads:
        company = lead.company
        contacts = lead.contacts or []
        if contacts:
            for c in contacts:
                rows.append({
                    "lead_id": lead.id,
                    "score": round(lead.score or 0, 1) if lead.score else 0,
                    "status": lead.status or "new",
                    "source": lead.source or "",
                    "company_name": company.name if company else "",
                    "company_domain": company.domain if company else "",
                    "company_industry": company.industry if company else "",
                    "company_size": company.size if company else "",
                    "company_country": company.country if company else "",
                    "company_location": company.location if company else "",
                    "company_website": company.website if company else "",
                    "company_linkedin": company.linkedin_url if company else "",
                    "contact_name": c.full_name or "",
                    "contact_title": c.title or "",
                    "contact_email": c.email or "",
                    "contact_phone": c.phone or "",
                    "contact_linkedin": c.linkedin_url or "",
                })
        else:
            rows.append({
                "lead_id": lead.id,
                "score": round(lead.score or 0, 1) if lead.score else 0,
                "status": lead.status or "new",
                "source": lead.source or "",
                "company_name": company.name if company else "",
                "company_domain": company.domain if company else "",
                "company_industry": company.industry if company else "",
                "company_size": company.size if company else "",
                "company_country": company.country if company else "",
                "company_location": company.location if company else "",
                "company_website": company.website if company else "",
                "company_linkedin": company.linkedin_url if company else "",
                "contact_name": "",
                "contact_title": "",
                "contact_email": "",
                "contact_phone": "",
                "contact_linkedin": "",
            })
    return rows


def _build_query(
    db: Session,
    user_id: int,
    icp_id: Optional[int],
    q: Optional[str],
    min_score: Optional[float],
    status: Optional[str] = None,
    source: Optional[str] = None,
):
    from sqlalchemy import or_
    from models import Company, Contact

    query = db.query(Lead).options(joinedload(Lead.company), joinedload(Lead.contacts)).filter(Lead.owner_id == user_id)
    if icp_id:
        query = query.filter(Lead.icp_id == icp_id)
    if min_score is not None:
        query = query.filter(Lead.score >= min_score)
    if status:
        query = query.filter(Lead.status == status)
    if source:
        query = query.filter(Lead.source == source)
    if q:
        query = query.join(Lead.company, isouter=True).join(Lead.contacts, isouter=True).filter(
            or_(
                Company.name.ilike(f"%{q}%"),
                Company.domain.ilike(f"%{q}%"),
                Contact.full_name.ilike(f"%{q}%"),
                Contact.email.ilike(f"%{q}%"),
            )
        )
    return query


@router.get("/csv")
def export_csv(
    icp_id: Optional[int] = None,
    q: Optional[str] = None,
    min_score: Optional[float] = Query(default=None, ge=0, le=100),
    status: Optional[str] = None,
    source: Optional[str] = None,
    fields: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = _build_query(db, current_user.id, icp_id, q, min_score, status, source)
    leads = query.all()
    rows = _flatten_leads(leads)

    selected_fields = CORE_FIELDS
    if fields:
        selected_fields = [f.strip() for f in fields.split(",") if f.strip() in CORE_FIELDS]
        if not selected_fields:
            selected_fields = CORE_FIELDS

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=selected_fields, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow(row)

    filename = "leads.csv"
    return _text_response(buf.getvalue(), filename, "text/csv")


@router.get("/json")
def export_json(
    icp_id: Optional[int] = None,
    q: Optional[str] = None,
    min_score: Optional[float] = Query(default=None, ge=0, le=100),
    status: Optional[str] = None,
    source: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = _build_query(db, current_user.id, icp_id, q, min_score, status, source)
    leads = query.all()
    rows = _flatten_leads(leads)
    content = json.dumps(rows, indent=2)
    return _text_response(content, "leads.json", "application/json")


def _text_response(content: str, filename: str, media_type: str):
    from fastapi import Response

    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
    }
    return Response(content=content, media_type=media_type, headers=headers)