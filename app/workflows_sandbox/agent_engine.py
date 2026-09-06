from crewai import Agent, Task, Crew, Process


class AgentEngine:
    def __init__(self):
        self.agents: list[Agent] = []
        self.tasks: list[Task] = []
        self.crew: Crew | None = None
        
    def add_agent(self, agent):
        self.agents.append(agent)

    def add_task(self, task):
        self.tasks.append(task)

    def create_crew(self):
        if not self.agents or not self.tasks:
            raise ValueError("Agents and tasks must be added before creating a crew.")
        self.crew = Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
        )
    async def run(self, inputs: dict[str, str]):
        if self.crew is None:
            self.create_crew()
        return await self.crew.kickoff_async(inputs=inputs)
