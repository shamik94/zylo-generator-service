from pydantic import BaseModel
from typing import List, Optional

class Position(BaseModel):
    company_name: str = ""

class Positions(BaseModel):
    positions_count: int = 0
    position_history: List[Position] = []

class LinkedInPerson(BaseModel):
    first_name: str = ""
    last_name: str = ""
    headline: str = ""
    location: str = ""
    summary: str = ""
    positions: Positions = Positions()

class LinkedInResponse(BaseModel):
    success: bool = True
    person: LinkedInPerson
