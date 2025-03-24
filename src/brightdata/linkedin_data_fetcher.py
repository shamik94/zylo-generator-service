import os
import json
import boto3
from fastapi import HTTPException
from src.model.linkedin_profile import (
    LinkedInResponse,
    LinkedInPerson,
    Position,
    Positions,
)

class LinkedinDataFetcher:
    """Fetches LinkedIn data from S3."""

    def read_linkedin_data_from_file(self, snapshot: str = None) -> dict:
        if not snapshot:
            raise HTTPException(
                status_code=400,
                detail="Snapshot ID is required"
            )

        try:
            bucket_name = os.getenv('S3_BUCKET')
            if not bucket_name:
                raise HTTPException(
                    status_code=500,
                    detail="S3_BUCKET environment variable not set"
                )

            s3_client = boto3.client(
                's3',
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY'),
                aws_secret_access_key=os.getenv('AWS_SECRET_KEY')
            )
            
            file_key = f'public/{snapshot}.json'
            print(f"Reading from S3 bucket: {bucket_name}, key: {file_key}")
            
            response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
            content = response['Body'].read().decode('utf-8')
            print(f"Successfully read {len(content)} bytes from S3")
            
            data = json.loads(content)
            if data is None:
                raise HTTPException(
                    status_code=500,
                    detail="S3 file contains null data"
                )
            return data
            
        except Exception as e:
            print(f"Failed to read from S3: {str(e)}")
            raise

    def get_info(self, linkedin_url: str = "", profile_data: dict = None, snapshot: str = None) -> LinkedInResponse:
        """
        Main interface method that returns structured LinkedIn profile data.
        Fetches data from S3 using the snapshot ID.
        """
        if profile_data:
            return self._convert_to_model(profile_data)
        
        raw_data = self.read_linkedin_data_from_file(snapshot=snapshot)
        
        if raw_data is None:
            raise HTTPException(
                status_code=500,
                detail="Failed to fetch LinkedIn data: No data returned"
            )
        
        return self._convert_to_model(raw_data)

    def _convert_to_model(self, data: dict) -> LinkedInResponse:
        """Convert S3 data to simplified LinkedInResponse model"""
        # If data is None or empty, initialize it as an empty dict
        if not data:
            data = {}
        
        # If data is a list, take the first item
        if isinstance(data, list):
            data = data[0] if data else {}
        
        print(f"Raw data from S3: {data}")  # Debug log
        
        # Extract company from current_company field
        positions = []
        current_company = data.get('current_company', {}) or {}
        company_name = current_company.get('name', '')
        if current_company:
            positions.append(Position(
                company_name=company_name
            ))
        
        # Split name into first and last name
        full_name = data.get('name', '').split()
        first_name = full_name[0] if full_name else ''
        last_name = ' '.join(full_name[1:]) if len(full_name) > 1 else ''
        
        # Create simplified person object with correct field mappings
        person = LinkedInPerson(
            first_name=first_name,
            last_name=last_name,
            headline=data.get('about', ''),  # Use 'about' field for headline
            location=data.get('city', ''),   # Use 'city' field for location
            summary=data.get('about', ''),   # Use 'about' field for summary
            positions=Positions(
                positions_count=len(positions),
                position_history=positions
            )
        )

        print(f"Converted person object: {person}")  # Debug log
        return LinkedInResponse(
            success=True,
            person=person
        )