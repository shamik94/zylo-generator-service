# backend/model/lead_email_details.py

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Text
)
from sqlalchemy.sql import func
from src.db.base import Base
from datetime import datetime

class LeadEmailDetails(Base):
    __tablename__ = "lead_email_details"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    
    # Provided by user
    lead_name = Column(String, nullable=True)

    linkedin_url = Column(String, nullable=True)
    company_name = Column(String, nullable=True)
    product_desc = Column(String, nullable=True)
    cta = Column(String, nullable=True)
    email_salutation = Column(String, nullable=True)

    status = Column(String, default="not_started", nullable=False)
    
    generated_email_greeting = Column(String, nullable=True)
    generated_email_hook = Column(String, nullable=True)
    generated_email_body = Column(String, nullable=True)
    
    snapshot_id = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
