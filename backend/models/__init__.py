from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    icps = relationship("ICP", back_populates="owner", cascade="all, delete-orphan")


class ICP(Base):
    __tablename__ = "icps"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    raw_input = Column(Text, nullable=False)
    name = Column(String(255), default="")
    industries = Column(Text, default="[]")
    company_size = Column(Text, default="[]")
    geographies = Column(Text, default="[]")
    revenue_min = Column(Float, nullable=True)
    revenue_max = Column(Float, nullable=True)
    tech_stack = Column(Text, default="[]")
    job_titles = Column(Text, default="[]")
    keywords = Column(Text, default="[]")
    funding_status = Column(String(100), default="")
    notes = Column(Text, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User", back_populates="icps")
    leads = relationship("Lead", back_populates="icp", cascade="all, delete-orphan")


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=True)
    name = Column(String(255), index=True)
    domain = Column(String(255), index=True)
    industry = Column(String(255), default="")
    description = Column(Text, default="")
    size = Column(String(255), default="")
    location = Column(String(255), default="")
    country = Column(String(255), default="")
    founded = Column(Integer, nullable=True)
    website = Column(String(255), default="")
    linkedin_url = Column(String(255), default="")
    phone = Column(String(100), default="")
    annual_revenue = Column(Float, nullable=True)
    funding_total = Column(Float, nullable=True)
    employee_count = Column(Integer, nullable=True)
    tech_stack = Column(Text, default="[]")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    lead = relationship("Lead", back_populates="company")
    contacts = relationship("Contact", back_populates="company")


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=True)
    full_name = Column(String(255), default="")
    first_name = Column(String(255), default="")
    last_name = Column(String(255), default="")
    title = Column(String(255), default="")
    email = Column(String(255), default="")
    phone = Column(String(100), default="")
    linkedin_url = Column(String(255), default="")
    location = Column(String(255), default="")
    is_decision_maker = Column(Boolean, default=False)
    seniority = Column(String(255), default="")
    last_contacted = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    company = relationship("Company", back_populates="contacts")
    lead = relationship("Lead", back_populates="contacts")


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    icp_id = Column(Integer, ForeignKey("icps.id"), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    score = Column(Float, default=0.0)
    score_breakdown = Column(Text, default="{}")
    score_explanation = Column(Text, default="")
    status = Column(String(100), default="new")
    source = Column(String(255), default="")
    dedup_key = Column(String(255), default="", index=True)
    is_duplicate = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    icp = relationship("ICP", back_populates="leads")
    contacts = relationship("Contact", back_populates="lead")
    company = relationship("Company", back_populates="lead", uselist=False)

    def to_overview_dict(self):
        return {
            "id": self.id,
            "score": round(self.score, 1) if self.score else 0,
            "status": self.status,
            "source": self.source,
            "is_duplicate": self.is_duplicate,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
