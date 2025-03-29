import warnings
import traceback
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_

from src.db.session import SessionLocal, engine
from src.model.lead_email_details import LeadEmailDetails, Base
from src.service.email_generation_service import EmailGenerationService

# Suppress specific Pydantic warning about V1/V2 mixing
warnings.filterwarnings(
    "ignore",
    message="Mixing V1 models and V2 models.*",
    category=UserWarning,
    module="pydantic.*"
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default offer and CTA text
DEFAULT_OFFER = "We provide top-tier corporate training services designed to enhance team productivity and skill development through customized workshops and ongoing support."
DEFAULT_CTA = "Reply to this email or schedule a 15-minute call to learn how we can tailor our training to your team's specific needs."
DEFAULT_SELLER_NAME = "John Doe"

def run_email_generation_job():
    """
    Cron job to generate emails for leads that are not started and older than 2 minutes
    """
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    # Initialize services
    email_service = EmailGenerationService()
    
    # Create database session
    db: Session = SessionLocal()

    try:
        logger.info("Starting email generation job")
        
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
        
        if not leads:
            logger.info("No eligible leads found.")
            return

        logger.info(f"Found {len(leads)} leads to process")
        
        for lead in leads:
            try:
                # Mark as in progress to prevent duplicate processing
                lead.status = "in_progress"
                db.commit()

                logger.info(f"Processing lead {lead.id}: {lead.lead_name}")
                
                # Use default values if not provided
                offer = lead.product_desc or DEFAULT_OFFER
                cta = lead.cta or DEFAULT_CTA
                
                # Generate email
                result = email_service.generate_email(
                    snapshot_id=lead.snapshot_id,
                    lead_name=lead.lead_name,
                    linkedin_url=lead.linkedin_url,
                    offer=offer,
                    cta=cta,
                    seller_name=DEFAULT_SELLER_NAME
                )
                
                if result.get("status") == "error":
                    logger.error(f"Error generating email for lead {lead.id}: {result.get('message')}")
                    lead.status = "error"
                    lead.error_message = result.get("message", "Unknown error")
                    db.commit()
                    continue
                
                # Update lead with generated email
                lead.generated_email_greeting = f"Hello {lead.lead_name}"
                lead.generated_email_hook = result.get("subject", "")
                lead.generated_email_body = result.get("body", "")
                
                # Validate email body
                if not lead.generated_email_body:
                    raise ValueError("Generated email body is empty")
                
                lead.status = "done"
                db.commit()
                logger.info(f"Successfully processed lead {lead.id}: {lead.lead_name}")
                
            except Exception as e:
                logger.error(f"Error processing lead {lead.id}: {str(e)}")
                logger.error(traceback.format_exc())
                lead.status = "error"
                lead.error_message = str(e)
                db.commit()

    except Exception as e:
        logger.error(f"Job failed: {str(e)}")
        logger.error(traceback.format_exc())
    finally:
        db.close()
        logger.info("Email generation job completed")

if __name__ == "__main__":
    run_email_generation_job()