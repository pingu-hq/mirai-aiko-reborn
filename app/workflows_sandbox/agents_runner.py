from app.workflows_sandbox.agents_pipeline import AgentCreation, AgentName, TaskName, TaskCreation
from app.workflows_sandbox.agent_engine import AgentEngine


async def run_agent(
    input_message: str,
    semantic_memory_context: str,
    most_recent_conversations: str,
) -> str:
    """
    - Current Message: `{input_message}`
    - Semantic Memories: `{semantic_memory_context}`
    - Recent Conversations: `{most_recent_conversations}`
    """
    input_data = {
        "input_message": input_message,
        "semantic_memory_context": semantic_memory_context,
        "most_recent_conversations": most_recent_conversations,
    }
    create_agent = AgentCreation()
    create_task = TaskCreation()
    agent_1 = create_agent.create_agent(agent_name=AgentName.AGENT_1)
    task_1 = create_task.create_task(task_name=TaskName.TASK_1, agent_assigned=agent_1)
    task_2 = create_task.create_task(task_name=TaskName.TASK_2, agent_assigned=agent_1)
    engine = AgentEngine()
    engine.add_agent(agent_1)
    engine.add_task(task_1)
    engine.add_task(task_2)
    
    return await engine.run(inputs=input_data)
