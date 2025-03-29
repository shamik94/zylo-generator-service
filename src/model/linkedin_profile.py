from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List


class CompanyInfo(BaseModel):
    """Company information model"""
    name: Optional[str] = None
    link: Optional[str] = None
    company_id: Optional[str] = None
    description: Optional[str] = None


class Position(BaseModel):
    """Position information model"""
    title: Optional[str] = None
    company_name: Optional[str] = None
    duration: Optional[str] = None
    description: Optional[str] = None
    is_current: bool = False


class Positions(BaseModel):
    """Collection of positions"""
    positions_count: int = 0
    position_history: List[Position] = Field(default_factory=list)


class Education(BaseModel):
    """Education information model"""
    title: Optional[str] = None
    institution: Optional[str] = None
    start_year: Optional[str] = None
    end_year: Optional[str] = None
    description: Optional[str] = None


class LinkedInProfile(BaseModel):
    """Model for LinkedIn profile data"""
    # Basic profile information
    id: Optional[str] = None
    name: str = ""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    headline: Optional[str] = None
    location: Optional[str] = None
    about: Optional[str] = None
    summary: Optional[str] = None
    url: Optional[str] = None
    avatar: Optional[str] = None
    
    # Company information
    current_company: Optional[CompanyInfo] = None
    
    # Work experience
    positions: Positions = Field(default_factory=Positions)
    
    # Education
    education: List[Education] = Field(default_factory=list)
    
    # Skills
    skills: List[str] = Field(default_factory=list)
    
    # Languages
    languages: List[Dict[str, str]] = Field(default_factory=list)
    
    # Formatted text for LLM input
    llm_linkedin_person_input: Optional[str] = None
    llm_linkedin_company_input: Optional[str] = None
    
    @classmethod
    def from_s3_data(cls, data: Dict[str, Any]) -> "LinkedInProfile":
        """Create a LinkedInProfile instance from the S3 data format"""
        # Ensure data is not None
        if data is None:
            data = {}
            
        # Extract first and last name
        full_name = data.get("name", "")
        name_parts = full_name.split(maxsplit=1) if full_name else []
        first_name = name_parts[0] if name_parts else ""
        last_name = name_parts[1] if len(name_parts) > 1 else ""
        
        # Create positions list if available
        positions = Positions(positions_count=0, position_history=[])
        if data.get("experience"):
            position_list = []
            for exp in data.get("experience", []) or []:  # Handle None case
                if exp and isinstance(exp, dict):  # Ensure exp is a valid dict
                    position_list.append(
                        Position(
                            title=exp.get("title"),
                            company_name=exp.get("company_name"),
                            duration=exp.get("duration"),
                            description=exp.get("description"),
                            is_current=exp.get("is_current", False)
                        )
                    )
            positions = Positions(
                positions_count=len(position_list),
                position_history=position_list
            )
        
        # Create education list if available
        education_list = []
        for edu in data.get("education", []) or []:  # Handle None case
            if edu and isinstance(edu, dict):  # Ensure edu is a valid dict
                education_list.append(
                    Education(
                        title=edu.get("title"),
                        institution=edu.get("school_name"),
                        start_year=edu.get("start_year"),
                        end_year=edu.get("end_year"),
                        description=edu.get("description")
                    )
                )
        
        # Create skills list if available
        skills_list = data.get("skills", []) or []  # Handle None case
        if isinstance(skills_list, list):
            skills = [skill.get("name") if isinstance(skill, dict) else skill 
                     for skill in skills_list 
                     if skill and (isinstance(skill, dict) or isinstance(skill, str))]
        else:
            skills = []
        
        # Create languages list if available
        languages_list = []
        for lang in data.get("languages", []) or []:  # Handle None case
            if lang and isinstance(lang, dict):
                languages_list.append({
                    "title": lang.get("title", ""),
                    "proficiency": lang.get("subtitle", "")
                })
        
        # Create profile instance with safe defaults
        profile = cls(
            id=data.get("id") or data.get("linkedin_id"),
            name=data.get("name", ""),
            first_name=first_name,
            last_name=last_name,
            headline=data.get("headline", ""),
            location=data.get("location", ""),
            about=data.get("about", ""),
            summary=data.get("summary", ""),
            url=data.get("url", ""),
            avatar=data.get("avatar", ""),
            current_company=CompanyInfo(
                name=data.get("current_company", {}).get("name") if data.get("current_company") else None,
                link=data.get("current_company", {}).get("link") if data.get("current_company") else None,
                company_id=data.get("current_company", {}).get("company_id") if data.get("current_company") else None
            ) if data.get("current_company") else None,
            positions=positions,
            education=education_list,
            skills=skills,
            languages=languages_list
        )
        
        # Generate formatted input for LLMs
        profile.llm_linkedin_person_input = profile._format_person_input()
        profile.llm_linkedin_company_input = profile._format_company_input()
        
        return profile
    
    def _format_person_input(self) -> str:
        """Format person profile data for LLM input"""
        company_name = ""
        if self.current_company and self.current_company.name:
            company_name = self.current_company.name
        elif self.positions.positions_count > 0:
            company_name = self.positions.position_history[0].company_name or ""
        
        current_role = ""
        if self.positions.positions_count > 0:
            current_role = self.positions.position_history[0].title or ""
        
        # Format skills as a comma-separated string
        skills_str = ", ".join(self.skills) if self.skills else ""
        
        # Format education
        education_str = ""
        for edu in self.education:
            institution = edu.institution or ""
            title = edu.title or ""
            years = f"{edu.start_year or ''}-{edu.end_year or ''}"
            education_str += f"{institution} - {title} ({years})\n"
        
        return f"""
LinkedIn Profile:
Name: {self.name}
Current Role: {current_role}
Current Company: {company_name}
Headline: {self.headline or ''}
Location: {self.location or ''}
About/Summary: {self.about or self.summary or ''}
Skills: {skills_str}
Education: 
{education_str}
URL: {self.url or ''}
"""
    
    def _format_company_input(self) -> str:
        """Format company data for LLM input"""
        company_name = ""
        company_description = ""
        
        if self.current_company and self.current_company.name:
            company_name = self.current_company.name
            company_description = self.current_company.description or ""
        elif self.positions.positions_count > 0:
            company_name = self.positions.position_history[0].company_name or ""
            company_description = self.positions.position_history[0].description or ""
        
        return f"""
Company Information:
Company Name: {company_name}
Company Description: {company_description}
"""