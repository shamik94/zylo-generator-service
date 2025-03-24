from src.agents.agent_utils import CustomCrew
from src.agents.cold_email_agent.prompt_config import *


class EmailCrew:
    def __init__(self):
        self.custom = CustomCrew()

    def add_all_agents(self):
        for agent_name, params in hb_cta_agent_template.items():
            self.custom.add_agent(
                agent_name=agent_name,
                role=params.get("role"),
                goal=params.get("goal"),
                backstory=params.get("backstory"),
                allow_delegation=params.get("allow_delegation"),
                llm=params.get("llm"),
            )
        return self

    def add_all_tasks(self):
        for task_name, params in hb_cta_task_template.items():
            self.custom.add_task(
                task_name=task_name,
                description=params.get("description"),
                expected_output=params.get("expected_output"),
                agent_name=task_agent_mapping.get(task_name),
            )
        return self

    def get_crew(self):
        return self.custom.assemble_crew(
            agent_names=list(hb_cta_agent_template.keys()),
            task_names=list(hb_cta_task_template.keys()),
        )
