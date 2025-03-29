import logging
from typing import Dict, Tuple, Optional, Any
from crewai import Crew, Agent, Task
import traceback

from src.model.linkedin_profile import LinkedInProfile
from src.service.linkedin_client_service import LinkedInClientService
from src.agents.prompt_config import (
    email_agents, 
    email_tasks, 
    task_agent_mapping,
    parse_email
)

# Configure logging
logger = logging.getLogger(__name__)

class EmailGenerationService:
    """Service for generating personalized cold emails"""
    
    def __init__(self):
        """Initialize the email generation service"""
        self.linkedin_service = LinkedInClientService()
    
    def generate_email(self, 
                      snapshot_id: str,
                      lead_name: str,
                      linkedin_url: Optional[str] = None,
                      offer: str = "",
                      cta: str = "",
                      seller_name: str = "Sales Team") -> Dict[str, str]:
        """
        Generate a personalized cold email based on LinkedIn profile
        
        Args:
            snapshot_id: ID of the snapshot containing LinkedIn data
            lead_name: Name of the lead
            linkedin_url: Optional URL to filter specific profile
            offer: The offer description
            cta: Call to action
            seller_name: Name of the seller
            
        Returns:
            Dict containing subject, body and raw_result
        """
        try:
            # Fetch LinkedIn profile data
            profile = self.linkedin_service.get_linkedin_profile(snapshot_id, linkedin_url)
            
            if not profile:
                error_msg = f"Failed to retrieve LinkedIn profile for {lead_name} (snapshot: {snapshot_id})"
                logger.error(error_msg)
                return {
                    "status": "error",
                    "message": error_msg
                }
            
            # Create the crew and generate the email
            try:
                email_result = self._run_email_crew(
                    profile=profile,
                    lead_name=lead_name,
                    offer=offer,
                    cta=cta,
                    seller_name=seller_name
                )
                
                # Parse the email result
                subject, body = parse_email(email_result)
                
                if not subject or not body:
                    error_msg = "Generated email is missing subject or body"
                    logger.error(error_msg)
                    return {
                        "status": "error",
                        "message": error_msg
                    }
                
                return {
                    "status": "success",
                    "subject": subject,
                    "body": body,
                    "raw_result": email_result
                }
                
            except Exception as e:
                error_msg = f"Error in email generation crew: {str(e)}"
                logger.error(error_msg)
                logger.error(traceback.format_exc())
                return {
                    "status": "error",
                    "message": error_msg
                }
            
        except Exception as e:
            error_msg = f"Error in email generation process: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return {
                "status": "error",
                "message": error_msg
            }
    
    def _run_email_crew(self, 
                        profile: LinkedInProfile, 
                        lead_name: str,
                        offer: str,
                        cta: str,
                        seller_name: str) -> str:
        """
        Run the email generation crew
        """
        try:
            # Create agents
            agents = {}
            for agent_name, agent_config in email_agents.items():
                agents[agent_name] = Agent(
                    role=agent_config["role"],
                    goal=agent_config["goal"],
                    backstory=agent_config["backstory"],
                    allow_delegation=agent_config.get("allow_delegation", False),
                    llm=agent_config["llm"]
                )
            
            # Prepare initial task variables
            task_variables = {
                "lead_name": lead_name,
                "linkedin_profile": profile.llm_linkedin_person_input,
                "company_profile": profile.llm_linkedin_company_input,
                "offer": offer,
                "cta": cta,
                "seller_name": seller_name
            }
            
            # Create and execute profile analysis task
            profile_analysis_task = Task(
                description=email_tasks["profile_analysis_task"]["description"].format(**task_variables),
                expected_output=email_tasks["profile_analysis_task"]["expected_output"],
                agent=agents[task_agent_mapping["profile_analysis_task"]]
            )
            
            # Create and execute company analysis task
            company_analysis_task = Task(
                description=email_tasks["company_analysis_task"]["description"].format(**task_variables),
                expected_output=email_tasks["company_analysis_task"]["expected_output"],
                agent=agents[task_agent_mapping["company_analysis_task"]]
            )
            
            # Create initial crew for analysis
            analysis_crew = Crew(
                agents=list(agents.values()),
                tasks=[profile_analysis_task, company_analysis_task],
                verbose=True
            )
            
            # Run analysis and get results
            analysis_results = analysis_crew.kickoff()
            
            # Update task variables with analysis results
            task_variables.update({
                "profile_analysis_result": profile_analysis_task.output if hasattr(profile_analysis_task, 'output') else "",
                "company_analysis_result": company_analysis_task.output if hasattr(company_analysis_task, 'output') else ""
            })
            
            # Create email creation task
            email_creation_task = Task(
                description=email_tasks["email_creation_task"]["description"].format(**task_variables),
                expected_output=email_tasks["email_creation_task"]["expected_output"],
                agent=agents[task_agent_mapping["email_creation_task"]]
            )
            
            # Create quality control task
            quality_control_task = Task(
                description=email_tasks["quality_control_task"]["description"].format(
                    email_creation_result="{email_creation_result}"
                ),
                expected_output=email_tasks["quality_control_task"]["expected_output"],
                agent=agents[task_agent_mapping["quality_control_task"]],
                context=[email_creation_task]
            )
            
            # Create final crew for email generation
            email_crew = Crew(
                agents=list(agents.values()),
                tasks=[email_creation_task, quality_control_task],
                verbose=True
            )
            
            # Run the crew and return the result
            return email_crew.kickoff()
            
        except Exception as e:
            logger.error(f"Error in _run_email_crew: {str(e)}")
            logger.error(traceback.format_exc())
            raise