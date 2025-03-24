from crewai import Agent, Task, Crew
from typing import List
import os
from langchain_openai import ChatOpenAI

# os.environ["OPENAI_MODEL_NAME"] = "gpt-3.5-turbo"

class CustomCrew:
    def __init__(self):
        self.agents = {}
        self.tasks = {}
        # self.llm = ChatOpenAI(temperature=0.7, model="gpt-4", streaming=False)

    def add_agent(
        self,
        agent_name,
        role: str,
        goal: str,
        backstory: str,
        allow_delegation,
        verbose=True,
        llm=None,
    ):
        new_agent = Agent(
            role=role,
            goal=goal,
            backstory=backstory,
            allow_delegation=allow_delegation,
            verbose=verbose,
            llm=llm,
        )
        self.agents.update({agent_name: new_agent})

    def add_task(
        self, task_name, description: str, expected_output: str, agent_name: Agent
    ):
        assert (
            agent_name in self.agents
        ), "Agent not found! Make sure you have added the agent before assigning task"

        new_task = Task(
            description=description,
            expected_output=expected_output,
            agent=self.agents.get(agent_name),
        )
        self.tasks.update({task_name: new_task})

    def assemble_crew(self, agent_names: List[str], task_names: List[str]) -> Crew:
        assert (
            len(self.agents) > 0
        ), "Cannot assemble crew without any agents. Please add agents"
        assert (
            len(self.tasks) > 0
        ), "Cannot assemble crew without any tasks. Please add tasks"

        for agent in agent_names:
            assert agent in self.agents, f"Agent {agent} not found"
        for task in task_names:
            assert task in self.tasks, f"Task {task} not found"

        crew = Crew(
            agents=[self.agents.get(name) for name in agent_names],
            tasks=[self.tasks.get(name) for name in task_names],
            verbose=True,
        )
        return crew
