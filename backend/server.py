import uuid
import json
import asyncio

import structlog
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from backend.logging_config import setup_logging
from backend.pharmacy_lookup import lookup_by_phone
from backend.prompts import build_system_prompt
from backend.agent import SalesAgent

load_dotenv()
setup_logging()

logger = structlog.get_logger()

app = FastAPI(title="Pharmesol Sales Agent API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session storage
sessions: dict[str, SalesAgent] = {}
session_pharmacy: dict[str, dict | None] = {}


class StartRequest(BaseModel):
    phone: str


class ChatRequest(BaseModel):
    session_id: str
    message: str


@app.post("/api/start")
async def start_session(req: StartRequest):
    """Start a new sales call session. Looks up pharmacy and returns greeting."""
    session_id = str(uuid.uuid4())
    log = logger.bind(session_id=session_id)

    try:
        pharmacy = await asyncio.to_thread(lookup_by_phone, req.phone)
        system_prompt = build_system_prompt(pharmacy, caller_phone=req.phone)
        agent = SalesAgent(system_prompt, session_id=session_id)
        greeting = await asyncio.to_thread(agent.generate_greeting)

        sessions[session_id] = agent
        session_pharmacy[session_id] = pharmacy

        pharmacy_info = None
        if pharmacy:
            pharmacy_info = {
                "name": pharmacy.get("name"),
                "city": pharmacy.get("city"),
                "state": pharmacy.get("state"),
                "rx_volume": pharmacy.get("rx_volume"),
            }

        log.info("session.started", pharmacy=pharmacy_info)

        return {
            "session_id": session_id,
            "greeting": greeting,
            "pharmacy": pharmacy_info,
        }
    except Exception:
        log.exception("session.start_failed")
        raise HTTPException(status_code=500, detail="Failed to start session")


@app.post("/api/chat")
async def chat(req: ChatRequest):
    """Send a message and receive a streaming response via SSE."""
    agent = sessions.get(req.session_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Session not found")

    log = logger.bind(session_id=req.session_id)
    log.info("chat.message_received", message_length=len(req.message))

    async def event_stream():
        sent_done = False
        try:
            generator = agent.chat_stream(req.message)

            for item in generator:
                if "token" in item:
                    data = json.dumps({"token": item["token"]})
                    yield f"data: {data}\n\n"
                elif "retract" in item:
                    data = json.dumps({
                        "retract": True,
                        "replacement": item.get("replacement", ""),
                    })
                    yield f"data: {data}\n\n"
                elif "done" in item:
                    sent_done = True
                    data = json.dumps({"done": True, "actions": item.get("actions", [])})
                    yield f"data: {data}\n\n"
        except Exception:
            log.exception("chat.stream_error")
            error_data = json.dumps({"error": "An error occurred processing your message."})
            yield f"data: {error_data}\n\n"
        finally:
            if not sent_done:
                yield f"data: {json.dumps({'done': True, 'actions': []})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
