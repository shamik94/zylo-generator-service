from src.agents.cold_email_agent.email_crew import EmailCrew
from src.agents.cold_email_agent.inputs.prepare_linkedin_input import (
    LinkedinProfile,
)
import re


def linkedin_based_email(lead, seller):
    crew = EmailCrew().add_all_agents().add_all_tasks().get_crew()
    linkedin_profile = LinkedinProfile(
        linkedin_url=lead.linkedin_url,
        snapshot_id=lead.snapshot_id
    )
    linkedin_profile.get_person_profile()
    linkedin_profile.get_company_profile()

    generated_email = crew.kickoff(
        inputs={
            "lead_name": lead.lead_name,
            "seller_name": seller,
            "cta": lead.cta,
            "offer": lead.product_desc,
            "company_profile": linkedin_profile.llm_linkedin_company_input,
            "linkedin_profile": linkedin_profile.llm_linkedin_person_input,
        }
    )

    return generated_email.raw


def email_parser(email_text):
    """Parse the email text to extract subject and content."""
    print(f"Input email text: {email_text}")  # Debug log
    
    # Extract subject
    subject_match = re.search(r"Subject:\s*(.+)", email_text)
    subject = subject_match.group(1) if subject_match else None
    
    # Extract email content - Updated pattern to match the actual format
    email_match = re.search(r"Email:\s*(.*?)(?=\Z)", email_text, re.DOTALL)
    # If the above pattern doesn't match, try alternative pattern
    if not email_match:
        email_match = re.search(r"Email:(.*)", email_text, re.DOTALL)
    
    email_content = email_match.group(1).strip() if email_match else None
    
    print(f"Parsed subject: {subject}")  # Debug log
    print(f"Parsed content: {email_content}")  # Debug log
    
    if not subject or not email_content:
        print("Warning: Could not parse subject or email content")  # Debug log
        return subject, email_content
        
    return subject, email_content
