from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import json
import logging

logger = logging.getLogger(__name__)


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
        logger.debug(f"Creating LinkedInProfile from data: {json.dumps(data, indent=2)}")
        
        # Ensure data is not None
        if data is None:
            logger.error("Input data is None")
            data = {}
        
        # Extract first and last name
        full_name = data.get("name", "")
        if not full_name and (data.get("first_name") or data.get("last_name")):
            full_name = f"{data.get('first_name', '')} {data.get('last_name', '')}".strip()
        
        name_parts = full_name.split(maxsplit=1) if full_name else []
        first_name = name_parts[0] if name_parts else data.get("first_name", "")
        last_name = name_parts[1] if len(name_parts) > 1 else data.get("last_name", "")
        
        # Try different field names for job title/role
        current_role = (
            data.get("headline") or 
            data.get("job_title") or 
            data.get("title") or 
            (data.get("experience", []) or [{}])[0].get("title", "")
        )
        
        # Try different field names for company
        current_company = data.get("current_company", {}) or {}
        if not current_company and data.get("experience"):
            current_exp = data["experience"][0] if isinstance(data["experience"], list) and data["experience"] else {}
            current_company = {
                "name": current_exp.get("company_name"),
                "description": current_exp.get("company_description")
            }
        
        # Create profile instance with enhanced data extraction
        profile = cls(
            id=data.get("id") or data.get("linkedin_id"),
            name=full_name,
            first_name=first_name,
            last_name=last_name,
            headline=current_role,
            location=data.get("location") or data.get("city", ""),
            about=data.get("about") or data.get("summary") or data.get("description", ""),
            summary=data.get("summary") or data.get("about") or data.get("description", ""),
            url=data.get("url") or data.get("profile_url", ""),
            avatar=data.get("avatar") or data.get("profile_picture", ""),
            current_company=CompanyInfo(
                name=current_company.get("name"),
                link=current_company.get("link"),
                company_id=current_company.get("company_id"),
                description=current_company.get("description")
            ) if current_company else None,
            positions=cls._extract_positions(data),
            education=cls._extract_education(data),
            skills=cls._extract_skills(data),
            languages=cls._extract_languages(data)
        )
        
        # Generate formatted input for LLMs
        profile.llm_linkedin_person_input = profile._format_person_input()
        profile.llm_linkedin_company_input = profile._format_company_input()
        
        logger.debug(f"Created profile with person input: {profile.llm_linkedin_person_input}")
        logger.debug(f"Created profile with company input: {profile.llm_linkedin_company_input}")
        
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

    @staticmethod
    def _extract_positions(data: Dict[str, Any]) -> Positions:
        positions_data = data.get("experience", []) or []
        if not isinstance(positions_data, list):
            positions_data = []
            
        position_list = []
        for exp in positions_data:
            if exp and isinstance(exp, dict):
                position_list.append(
                    Position(
                        title=exp.get("title"),
                        company_name=exp.get("company_name"),
                        duration=exp.get("duration"),
                        description=exp.get("description"),
                        is_current=exp.get("is_current", False)
                    )
                )
        
        return Positions(
            positions_count=len(position_list),
            position_history=position_list
        )

    @staticmethod
    def _extract_education(data: Dict[str, Any]) -> List[Education]:
        education_data = data.get("education", []) or []
        if not isinstance(education_data, list):
            education_data = []
            
        education_list = []
        for edu in education_data:
            if edu and isinstance(edu, dict):
                education_list.append(
                    Education(
                        title=edu.get("title") or edu.get("degree"),
                        institution=edu.get("school_name") or edu.get("institution"),
                        start_year=edu.get("start_year") or edu.get("start_date"),
                        end_year=edu.get("end_year") or edu.get("end_date"),
                        description=edu.get("description")
                    )
                )
        return education_list

    @staticmethod
    def _extract_skills(data: Dict[str, Any]) -> List[str]:
        """Extract skills from profile data"""
        skills_data = data.get("skills", []) or []
        if not isinstance(skills_data, list):
            return []
            
        skills = []
        for skill in skills_data:
            if isinstance(skill, dict):
                # Handle case where skill is an object
                skill_name = skill.get("name") or skill.get("skill")
                if skill_name:
                    skills.append(skill_name)
            elif isinstance(skill, str):
                # Handle case where skill is just a string
                skills.append(skill)
                
        logger.debug(f"Extracted skills: {skills}")
        return skills

    @staticmethod
    def _extract_languages(data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Extract languages from profile data"""
        languages_data = data.get("languages", []) or []
        if not isinstance(languages_data, list):
            return []
            
        languages = []
        for lang in languages_data:
            if isinstance(lang, dict):
                language = {
                    "title": lang.get("title") or lang.get("language", ""),
                    "proficiency": lang.get("subtitle") or lang.get("proficiency", "")
                }
                if language["title"]:  # Only add if we have at least a language name
                    languages.append(language)
                    
        logger.debug(f"Extracted languages: {languages}")
        return languages