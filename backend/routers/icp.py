from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db
from models import ICP, Lead, User
from routers.deps import get_current_user
from schemas.icp import ICPCreate, ICPCriteria, ICPOut, ICPUpdate
from services.icp_parser import extract_icp
from utils.helpers import dumps_json

router = APIRouter(prefix="/api/icps", tags=["icp"])


class ICPParseResult(BaseModel):
    criteria: ICPCriteria


def _criteria_from_orm(icp: ICP) -> ICPCriteria:
    return ICPCriteria(
        industries=_to_list(icp.industries),
        company_size=_to_list(icp.company_size),
        geographies=_to_list(icp.geographies),
        revenue_min=icp.revenue_min,
        revenue_max=icp.revenue_max,
        tech_stack=_to_list(icp.tech_stack),
        job_titles=_to_list(icp.job_titles),
        keywords=_to_list(icp.keywords),
        funding_status=icp.funding_status or "",
        notes=icp.notes or "",
    )


def _to_list(value) -> list[str]:
    try:
        import json

        if isinstance(value, str) and value:
            return json.loads(value)
    except Exception:
        pass
    return value or []


def _apply_criteria(icp: ICP, criteria: ICPCriteria):
    icp.industries = dumps_json(criteria.industries)
    icp.company_size = dumps_json(criteria.company_size)
    icp.geographies = dumps_json(criteria.geographies)
    icp.revenue_min = criteria.revenue_min
    icp.revenue_max = criteria.revenue_max
    icp.tech_stack = dumps_json(criteria.tech_stack)
    icp.job_titles = dumps_json(criteria.job_titles)
    icp.keywords = dumps_json(criteria.keywords)
    icp.funding_status = criteria.funding_status or ""
    icp.notes = criteria.notes or ""


@router.post("/parse", response_model=ICPParseResult)
def parse_icp(payload: ICPCreate):
    criteria = extract_icp(payload.raw_input)
    return ICPParseResult(criteria=criteria)


@router.post("", response_model=ICPOut, status_code=201)
def create_icp(payload: ICPCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    criteria = extract_icp(payload.raw_input)
    icp = ICP(
        owner_id=current_user.id,
        raw_input=payload.raw_input,
        name=payload.name or payload.raw_input[:60],
    )
    _apply_criteria(icp, criteria)
    db.add(icp)
    db.commit()
    db.refresh(icp)
    return _to_out(icp, db)


def _to_out(icp: ICP, db: Session) -> ICPOut:
    out = ICPOut(
        id=icp.id,
        name=icp.name or "",
        raw_input=icp.raw_input,
        industries=_to_list(icp.industries),
        company_size=_to_list(icp.company_size),
        geographies=_to_list(icp.geographies),
        revenue_min=icp.revenue_min,
        revenue_max=icp.revenue_max,
        tech_stack=_to_list(icp.tech_stack),
        job_titles=_to_list(icp.job_titles),
        keywords=_to_list(icp.keywords),
        funding_status=icp.funding_status or "",
        notes=icp.notes or "",
        created_at=icp.created_at.isoformat() if icp.created_at else None,
    )
    return out


@router.get("", response_model=list[ICPOut])
def list_icps(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    icps = db.query(ICP).filter(ICP.owner_id == current_user.id).order_by(ICP.created_at.desc()).all()
    return [_to_out(icp, db) for icp in icps]


@router.get("/{icp_id}", response_model=ICPOut)
def get_icp(icp_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    icp = _get_owned_icp(db, icp_id, current_user.id)
    return _to_out(icp, db)


@router.put("/{icp_id}", response_model=ICPOut)
def update_icp(icp_id: int, payload: ICPUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    icp = _get_owned_icp(db, icp_id, current_user.id)
    if payload.name is not None:
        icp.name = payload.name
    _apply_criteria(icp, ICPCriteria(**payload.model_dump()))
    db.commit()
    db.refresh(icp)
    return _to_out(icp, db)


@router.delete("/{icp_id}", status_code=204)
def delete_icp(icp_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    icp = _get_owned_icp(db, icp_id, current_user.id)
    db.delete(icp)
    db.commit()


def _get_owned_icp(db: Session, icp_id: int, owner_id: int) -> ICP:
    icp = db.query(ICP).filter(ICP.id == icp_id, ICP.owner_id == owner_id).first()
    if not icp:
        raise HTTPException(status_code=404, detail="ICP not found")
    return icp