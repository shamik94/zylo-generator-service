import os
import json
import boto3
import logging
from typing import Optional, Dict, Any, List, Union
from fastapi import HTTPException
import traceback

from src.model.linkedin_profile import LinkedInProfile

# Configure logging
logger = logging.getLogger(__name__)

class LinkedInClientService:
    """Service for retrieving LinkedIn profile data from S3"""
    
    def __init__(self):
        """Initialize the LinkedIn client service"""
        self.s3_bucket = os.getenv('S3_BUCKET')
        self.aws_access_key = os.getenv('AWS_ACCESS_KEY')
        self.aws_secret_key = os.getenv('AWS_SECRET_KEY')
        
        # Validate environment variables
        if not all([self.s3_bucket, self.aws_access_key, self.aws_secret_key]):
            logger.error("Missing required S3 environment variables")
            raise ValueError("Missing required S3 environment variables")
        
        # Initialize S3 client
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=self.aws_access_key,
            aws_secret_access_key=self.aws_secret_key
        )
    
    def get_linkedin_profile(self, snapshot_id: str, linkedin_url: Optional[str] = None) -> Optional[LinkedInProfile]:
        """
        Retrieve LinkedIn profile data from S3 and convert to DTO
        
        Args:
            snapshot_id: The ID of the snapshot in S3
            linkedin_url: Optional URL to filter specific profile from snapshot
            
        Returns:
            LinkedInProfile: The LinkedIn profile data as a DTO
        """
        try:
            file_key = f'public/{snapshot_id}.json'
            logger.info(f"Attempting to access S3 key: {file_key} in bucket: {self.s3_bucket}")
            
            # Get the object from S3
            try:
                response = self.s3_client.get_object(Bucket=self.s3_bucket, Key=file_key)
                content = response['Body'].read().decode('utf-8')
                logger.info(f"Successfully read {len(content)} bytes from S3")
            except Exception as e:
                logger.error(f"Failed to read from S3: {str(e)}")
                return None
            
            try:
                # Parse JSON content
                data = json.loads(content)
                if data is None:
                    logger.error("S3 file contains null data")
                    return None
                
                # Handle both list and single object formats
                profiles = data if isinstance(data, list) else [data]
                
                # If URL is provided, find matching profile
                if linkedin_url:
                    for profile in profiles:
                        if profile.get('url') == linkedin_url:
                            return LinkedInProfile.from_s3_data(profile)
                    
                    logger.warning(f"No profile found with URL {linkedin_url} in snapshot {snapshot_id}")
                    return None
                
                # If no URL provided and multiple profiles exist, use the first one
                if profiles:
                    return LinkedInProfile.from_s3_data(profiles[0])
                
                logger.warning(f"No profiles found in snapshot {snapshot_id}")
                return None
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from S3: {str(e)}")
                return None
                
        except Exception as e:
            logger.error(f"Error retrieving LinkedIn profile: {str(e)}")
            logger.error(traceback.format_exc())
            return None
    
    def get_linkedin_profiles(self, snapshot_id: str) -> List[LinkedInProfile]:
        """
        Retrieve all LinkedIn profiles from a snapshot
        
        Args:
            snapshot_id: The ID of the snapshot in S3
            
        Returns:
            List[LinkedInProfile]: A list of LinkedIn profile DTOs
        """
        try:
            # Construct the S3 key
            file_key = f'public/{snapshot_id}.json'
            logger.info(f"Reading from S3 bucket: {self.s3_bucket}, key: {file_key}")
            
            # Get the object from S3
            response = self.s3_client.get_object(Bucket=self.s3_bucket, Key=file_key)
            content = response['Body'].read().decode('utf-8')
            logger.info(f"Successfully read {len(content)} bytes from S3")
            
            # Parse JSON content
            data = json.loads(content)
            if data is None:
                logger.error("S3 file contains null data")
                return []
            
            # Handle both list and single object formats
            profiles = data if isinstance(data, list) else [data]
            
            # Convert each profile to DTO
            return [LinkedInProfile.from_s3_data(profile) for profile in profiles]
            
        except Exception as e:
            logger.error(f"Error retrieving LinkedIn profiles: {str(e)}")
            raise