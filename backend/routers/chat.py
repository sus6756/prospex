import json
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import get_db
from models import Company, Contact, ICP, Lead, User
from routers.deps import get_current_user
from utils.ai_client import chat_text
from utils.helpers import loads_json

router = APIRouter(prefix="/api/chat", tags=["chat"])

CHAT_SYSTEM_PROMPT = """You are Prospex Assistant, a friendly B2B sales & growth expert embedded inside a lead discovery and qualification platform.

The user runs lead discovery: they describe an Ideal Customer Profile (ICP) in plain English, the platform finds and scores matching companies (0-100), enriches decision-maker contacts, and tracks lead statuses (new / contacted / qualified / unqualified).

You are given a snapshot of the user's workspace. Use it to answer questions concretely and specifically — cite real company names, scores, and statuses when relevant. If asked something not covered by the snapshot, say so and give general best-practice advice.

Be concise, practical, well-structured (short bullet lists are fine). Keep replies under ~180 words unless asked for a deep dive. Never invent data that is not in the snapshot. If the workspace is empty, acknowledge it and guide them to create their first ICP."""


class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., min_length=1, max_length=4000)


class ChatIn(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    history: list[ChatMessage] = []
    lead_id: Optional[int] = None


class ChatOut(BaseModel):
    reply: str


def _workspace_snapshot(db: Session, user_id: int) -> dict:
    leads = db.query(Lead).filter(Lead.owner_id == user_id).all()
    lead_rows = []
    for lead in leads[:6]:
        company = (
            db.query(Company)
            .filter(Company.lead_id == lead.id)
            .first()
        )
        lead_rows.append(
            {
                "company": company.name if company else None,
                "domain": company.domain if company else None,
                "industry": company.industry if company else None,
                "country": company.country if company else None,
                "score": round(lead.score or 0, 1) if lead.score else 0,
                "status": lead.status or "new",
                "source": lead.source or "",
            }
        )

    icps = db.query(ICP).filter(ICP.owner_id == user_id).all()
    icp_rows = [
        {
            "name": icp.name or "Untitled",
            "industries": loads_json(icp.industries),
            "geographies": loads_json(icp.geographies),
            "raw_input": (icp.raw_input or "")[:200],
        }
        for icp in icps[:5]
    ]

    scores = [l.score or 0 for l in leads]
    status_counts: dict[str, int] = {}
    for lead in leads:
        status_counts[lead.status or "new"] = status_counts.get(lead.status or "new", 0) + 1

    total_contacts = (
        db.query(Contact)
        .join(Lead, Lead.id == Contact.lead_id)
        .filter(Lead.owner_id == user_id)
        .count()
    )
    return {
        "total_leads": len(leads),
        "avg_score": round(sum(scores) / len(scores), 1) if scores else None,
        "top_score": round(max(scores), 1) if scores else None,
        "status_counts": status_counts,
        "icps": icp_rows,
        "top_leads": lead_rows,
        "total_contacts": total_contacts,
    }


@router.post("", response_model=ChatOut)
def chat(
    payload: ChatIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    snapshot = _workspace_snapshot(db, current_user.id)

    lead_context = ""
    if payload.lead_id:
        lead = db.query(Lead).filter(Lead.lead_id if False else Lead.id == payload.lead_id, Lead.owner_id == current_user.id).first()
        if lead:
            company = db.query(Company).filter(Company.lead_id == lead.id).first()
            contacts = [
                {"name": c.full_name, "title": c.title, "is_decision_maker": c.is_decision_maker}
                for c in (lead.contacts or [])
            ]
            lead_context = (
                "\n\nActive lead being discussed:\n"
                + json.dumps(
                    {
                        "company": company.name if company else None,
                        "industry": company.industry if company else None,
                        "score": round(lead.score or 0, 1) if lead.score else 0,
                        "status": lead.status or "new",
                        "score_explanation": (lead.score_explanation or "")[:400],
                        "contacts": contacts,
                    },
                    default=str,
                )
            )

    system_prompt = (
        CHAT_SYSTEM_PROMPT
        + "\n\nUser workspace snapshot (JSON):\n"
        + json.dumps(snapshot, default=str)
        + lead_context
    )

    history = [(m.role, m.content) for m in payload.history[-10:]]
    user_prompt = "User's question:\n" + payload.message
    if history:
        transcript = "\n".join(f"{role}: {content}" for role, content in history)
        user_prompt = "Recent conversation:\n" + transcript + "\n\n" + user_prompt

    try:
        reply = chat_text(system_prompt, user_prompt, temperature=0.4, max_tokens=700)
    except Exception as exc:
        reply = (
            "I couldn't reach the AI provider right now. "
            f"(Time to build: this is the fallback message — {str(exc)[:120]})"
        )
    return ChatOut(reply=reply or "No reply generated.")