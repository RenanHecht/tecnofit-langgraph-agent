import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from app.graph import app_graph
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="Tecnofit Assistant API",
    version="1.0.0",
    description="API do Assistente Virtual Inteligente"
)

memory = MemorySaver()

class ChatRequest(BaseModel):
    message: str
    thread_id: str = "default_thread"

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        callbacks = []
        langfuse_handler = None
        
        if os.getenv("LANGFUSE_PUBLIC_KEY"):
            from langfuse.callback import CallbackHandler
            langfuse_handler = CallbackHandler(
                public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
                secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
                host=os.getenv("LANGFUSE_HOST"),
                session_id=request.thread_id
            )
            callbacks.append(langfuse_handler)

        config = {
            "configurable": {"thread_id": request.thread_id},
            "callbacks": callbacks
        }
        
        inputs = {
            "messages": [HumanMessage(content=request.message)]
        }
        
        final_state = app_graph.invoke(
            inputs, 
            config=config
        )
        
        if langfuse_handler:
            langfuse_handler.flush()
        
        response_message = final_state["messages"][-1].content
        
        return {
            "message": response_message,
            "thread_id": request.thread_id
        }

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))