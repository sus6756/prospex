import json
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Company, Contact, ICP, Lead, User
from routers.deps import get_current_user
from schemas.lead import DiscoveryRequest, DiscoveryResult
from services.deduplication import dedup_key_for_company
from services.lead_discovery import discover_from_sources, normalize_criteria
from services.lead_scorer import score_lead
from utils.helpers import dumps_json
import services.contact_enrichment as enrichment

router = APIRouter(prefix="/api/discovery", tags=["discovery"])


@router.post("/run", response_model=DiscoveryResult)
async def run_discovery(
    payload: DiscoveryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    icp = db.query(ICP).filter(ICP.id == payload.icp_id, ICP.owner_id == current_user.id).first()
    if not icp:
        raise HTTPException(status_code=404, detail="ICP not found")

    criteria = normalize_criteria(icp)

    # Suppress JSON-fields not used by light-weight query
    discovered = await discover_from_sources(criteria, payload.sources, limit=15)

    existing_dedup_keys = set()
    for existing_lead in db.query(Lead).filter(Lead.icp_id == icp.id).all():
        if existing_lead.dedup_key:
            existing_dedup_keys.add(existing_lead.dedup_key)

    stored_ids = []
    duplicates_merged = 0
    seen_in_batch = {}

    to_score = []
    for raw in discovered:
        company = enrichment.enrich_lead_payload(raw)
        dedup_key = dedup_key_for_company(company)

        if dedup_key in existing_dedup_keys or dedup_key in seen_in_batch:
            duplicates_merged += 1
            continue

        existing_lead = _find_existing_by_domain(db, icp.id, company.get("domain") or "")
        if existing_lead:
            seen_in_batch[dedup_key] = True
            duplicates_merged += 1
            continue

        to_score.append((company, dedup_key, raw))

    with ThreadPoolExecutor(max_workers=min(8, max(1, len(to_score)))) as pool:
        scored = list(
            pool.map(
                lambda x: (x[0], x[1], x[2], score_lead(criteria, x[0])),
                to_score,
            )
        )

    for company, dedup_key, raw, scoring in scored:

        lead = Lead(
            icp_id=icp.id,
            owner_id=current_user.id,
            score=scoring["score"],
            score_breakdown=dumps_json(scoring.get("breakdown", [])),
            score_explanation=scoring.get("explanation", ""),
            status="new",
            source=company.get("source") or "unknown",
            dedup_key=dedup_key,
            is_duplicate=False,
        )
        db.add(lead)
        db.flush()

        company.pop("contacts", None)
        company_obj = Company(
            lead_id=lead.id,
            name=company.get("name") or "",
            domain=company.get("domain") or "",
            industry=company.get("industry") or "",
            description=company.get("description") or "",
            size=company.get("size") or "",
            location=company.get("location") or "",
            country=company.get("country") or "",
            founded=company.get("founded"),
            website=company.get("website") or "",
            linkedin_url=company.get("linkedin_url") or "",
            phone=company.get("phone") or "",
            annual_revenue=company.get("annual_revenue"),
            funding_total=company.get("funding_total"),
            employee_count=company.get("employee_count"),
            tech_stack=dumps_json(company.get("tech_stack") or []),
        )
        db.add(company_obj)
        db.flush()

        for contact_data in raw.get("contacts", []):
            contact_entry = enrichment.enrich_contact(contact_data, company_obj.domain)
            contact = Contact(
                company_id=company_obj.id,
                lead_id=lead.id,
                full_name=contact_entry.get("full_name") or "",
                first_name=contact_entry.get("first_name") or "",
                last_name=contact_entry.get("last_name") or "",
                title=contact_entry.get("title") or "",
                email=contact_entry.get("email") or "",
                phone=contact_entry.get("phone") or "",
                linkedin_url=contact_entry.get("linkedin_url") or "",
                location=contact_entry.get("location") or "",
                is_decision_maker=bool(contact_entry.get("is_decision_maker")),
                seniority=contact_entry.get("seniority") or "",
            )
            db.add(contact)

        seen_in_batch[dedup_key] = True
        existing_dedup_keys.add(dedup_key)
        stored_ids.append(lead.id)

    db.commit()

    return DiscoveryResult(
        lead_ids=stored_ids,
        total_discovered=len(discovered),
        enriched_count=len(stored_ids),
        scored_count=len(stored_ids),
        duplicates_merged=duplicates_merged,
    )


def _find_existing_by_domain(db: Session, icp_id: int, domain: str) -> Lead | None:
    if not domain:
        return None
    company = db.query(Company).filter(Company.domain == domain).first()
    if company and company.lead_id:
        return db.query(Lead).filter(Lead.id == company.lead_id, Lead.icp_id == icp_id).first()
    return None