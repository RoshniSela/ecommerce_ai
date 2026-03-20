from fastapi import APIRouter
from agent.agent import ask_llm

router = APIRouter()


@router.post("/agent")
def run_agent(query: str):
    result = ask_llm(query)
    return {"response": result}