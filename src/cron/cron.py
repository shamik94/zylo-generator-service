import traceback
from datetime import datetime, timedelta
import boto3
import json
import os
from sqlalchemy.orm import Session
from sqlalchemy import and_
from src.db.session import SessionLocal, engine
from src.model.lead_email_details import LeadEmailDetails
from src.db.base import Base
from src.agents.cold_email_agent.email_crew import EmailCrew
from src.agents.cold_email_agent.run_email_agent import email_parser
from src.brightdata.linkedin_data_fetcher import LinkedinDataFetcher
from src.agents.cold_email_agent.inputs.prepare_linkedin_input import LinkedinProfile
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create tables before running the job
Base.metadata.create_all(bind=engine)

offer = "We provide top-tier corporate training services..."  # Your existing offer
cta = "Reply to this email or schedule..."  # Your existing CTA

def get_profile_from_snapshot(snapshot_id, linkedin_url):
    """Fetch profile data from S3 and find matching URL entry"""
    try:
        s3 = boto3.client('s3')
        bucket_name = os.getenv('S3_BUCKET_NAME')
        response = s3.get_object(Bucket=bucket_name, Key=snapshot_id)
        profiles = json.loads(response['Body'].read().decode('utf-8'))
        
        # Find matching profile
        for profile in profiles:
            if profile.get('url') == linkedin_url:
                return profile
        return None
    except Exception as e:
        print(f"Error fetching from S3: {e}")
        return None

def run_email_generation():
    """Generates emails for leads that are not started and older than 2 minutes"""
    db: Session = SessionLocal()

    try:
        # Get leads with status "not_started" and updated more than 2 minutes ago
        two_mins_ago = datetime.utcnow() - timedelta(minutes=2)
        leads = (
            db.query(LeadEmailDetails)
            .filter(
                and_(
                    LeadEmailDetails.status == "not_started",
                    LeadEmailDetails.updated_at <= two_mins_ago
                )
            )
            .all()
        )

        logger.info("Starting email generation job")
        
        if not leads:
            logger.info("No eligible leads found.")
            return

        for lead in leads:
            try:
                lead.status = "in_progress"
                db.commit()

                linkedin_profile = LinkedinProfile(
                    linkedin_url=lead.linkedin_url,
                    snapshot_id=lead.snapshot_id
                )
                linkedin_profile.get_person_profile()
                linkedin_profile.get_company_profile()

                crew = EmailCrew().add_all_agents().add_all_tasks().get_crew()
                generated_email = crew.kickoff(
                    inputs={
                        "lead_name": lead.lead_name,
                        "seller_name": "John Doe",
                        "cta": lead.cta or cta,
                        "offer": lead.product_desc or offer,
                        "company_profile": linkedin_profile.llm_linkedin_company_input,
                        "linkedin_profile": linkedin_profile.llm_linkedin_person_input,
                    }
                )
                
                print(f"Generated email content: {generated_email}")  # Debug log
                
                subject, email_content = email_parser(generated_email)
                if not email_content:
                    raise ValueError("Failed to parse email content")

                print(f"Parsed subject: {subject}")  # Debug log
                print(f"Parsed email content: {email_content}")  # Debug log

                # Update lead with generated email
                lead.generated_email_greeting = f"Hello {lead.lead_name}"
                lead.generated_email_hook = subject
                lead.generated_email_body = email_content
                
                if not lead.generated_email_body:
                    raise ValueError("Email body is empty")
                
                print(f"Before commit - Email body: {lead.generated_email_body}")  # Debug log
                
                lead.status = "done"
                db.commit()
                
                print(f"After commit - Email body: {lead.generated_email_body}")  # Debug log
                logger.info(f"Successfully processed lead {lead.id}: {lead.lead_name}")

            except Exception as e:
                logger.error(f"Error processing lead {lead.id}: {e}")
                logger.error(traceback.format_exc())
                lead.status = "error"
                db.commit()

    except Exception as e:
        logger.error(f"Job failed: {e}")
        logger.error(traceback.format_exc())
    finally:
        db.close()

def format_linkedin_profile_from_model(person):
    """Format LinkedIn profile data from the model for the email crew"""
    company = ""
    if person.positions.positions_count > 0:
        company = person.positions.position_history[0].company_name
        
    return f"""
    first_name: {person.first_name}
    last_name: {person.last_name}
    headline: {person.headline}
    location: {person.location}
    summary: {person.summary}
    company: {company}
    """

def format_company_profile_from_model(person):
    """Format company profile data from the model for the email crew"""
    company = ""
    company_description = ""
    
    if person.positions.positions_count > 0:
        company = person.positions.position_history[0].company_name
        company_description = person.positions.position_history[0].description or ""
        
    return f"""
    company: {company}
    company_description: {company_description}
    """

# Keep the original format functions for backward compatibility
def format_linkedin_profile(profile_data):
    """Format LinkedIn profile data for the email crew"""
    return f"""
    first_name: {profile_data.get('firstName', '')}
    last_name: {profile_data.get('lastName', '')}
    headline: {profile_data.get('headline', '')}
    location: {profile_data.get('location', '')}
    summary: {profile_data.get('summary', '')}
    company: {profile_data.get('currentCompany', '')}
    """

def format_company_profile(profile_data):
    """Format company profile data for the email crew"""
    return f"""
    company: {profile_data.get('currentCompany', '')}
    company_description: {profile_data.get('companyDescription', '')}
    """

if __name__ == "__main__":
    run_email_generation()