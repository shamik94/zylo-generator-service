from src.brightdata.linkedin_data_fetcher import LinkedinDataFetcher


class LinkedinProfile:
    def __init__(self, linkedin_url="", snapshot_id=None):
        self.linkedin_profile = LinkedinDataFetcher().get_info(
            linkedin_url=linkedin_url,
            snapshot=snapshot_id
        )

    def get_person_profile(self):
        person = self.linkedin_profile.person
        company_name = person.positions.position_history[0].company_name if person.positions.position_history else ""
        
        self.llm_linkedin_person_input = f"""
            first_name: {person.first_name}
            last_name: {person.last_name}
            headline: {person.headline}
            location: {person.location}
            summary: {person.summary}
            company: {company_name}
            """

    def get_company_profile(self):
        company_description = "As the world's leading local delivery platform, our mission is to deliver an amazing experience, fast, easy, and to your door. We operate in over 70+ countries worldwide, powered by tech but driven by people. As one of Europe's largest tech platforms, we enable ambitious talent to deliver solutions that create impact within our ecosystem. We move fast, take action and adapt. No matter where you're from or what you believe in, we build, we deliver, we lead. We are Delivery Hero."
        company_name = "Delivery Hero"

        self.llm_linkedin_company_input = f"""
            company: {company_name}
            company_description: {company_description}
            """
