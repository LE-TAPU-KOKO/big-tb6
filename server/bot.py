import os
import asyncio
import json
import sys
import logging
import warnings
from datetime import datetime
from dotenv import load_dotenv

from vision_agents.core.agents import Agent
from vision_agents.core.agents.agent_launcher import AgentLauncher
from vision_agents.core.runner import Runner
from vision_agents.core.edge.types import User
from vision_agents.plugins.gemini.gemini_realtime import GeminiRealtime
from vision_agents.plugins.getstream.stream_edge_transport import StreamEdge

# Ensure local modules are importable (works in both Windows and WSL)
import pathlib
_server_dir = str(pathlib.Path(__file__).resolve().parent)
sys.path.insert(0, _server_dir)
from tb_audio_tool import analyze_cough_file, save_audio_to_wav
from chest_xray_tool import analyze_xray_file
from xray_store import get_latest_xray_path

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY", "")

# ---------------------------------------------------------------------------
# Tool Definitions
# ---------------------------------------------------------------------------

async def analyze_chest_xray() -> str:
    """Analyzes the most recently uploaded chest X-ray image for TB indicators."""
    latest_path = get_latest_xray_path()
    if not latest_path or not os.path.exists(latest_path):
        return json.dumps({"error": "No chest X-ray found. Please ask the user to upload one first using the UI dashboard."})
        
    print(f"Calling chest X-ray API for: {latest_path}")
    try:
        result = await analyze_xray_file(latest_path)
        print(f"Chest X-ray analysis result: {result}")
        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": str(e)})

async def analyze_uploaded_cough() -> str:
    """Analyzes the most recently uploaded cough audio for TB indicators."""
    return json.dumps({
        "status": "Cough analysis not fully ported yet. Please advise the user to rely on Gemini's native audio listening capabilities for the hackathon."
    })

async def analyze_uploaded_palm() -> str:
    """Analyzes the most recently uploaded palm image for Anemia indicators."""
    return json.dumps({
        "status": "Palm analysis uploaded file processing not fully ported yet. Please ask the user to use the UI."
    })

async def analyze_uploaded_eye() -> str:
    """Analyzes the most recently uploaded eye image for Anemia indicators."""
    return json.dumps({
        "status": "Eye analysis uploaded file processing not fully ported yet. Please ask the user to use the UI."
    })

async def analyze_uploaded_nail() -> str:
    """Analyzes the most recently uploaded nail image for Anemia indicators."""
    return json.dumps({
        "status": "Nail analysis uploaded file processing not fully ported yet. Please ask the user to use the UI."
    })

# ---------------------------------------------------------------------------
# Monkey patches for Stream server-side auth
# ---------------------------------------------------------------------------

import getstream.video.async_call
from getstream.models import CallRequest
orig_goc = getstream.video.async_call.Call.get_or_create
async def patched_goc(self, *args, **kwargs):
    kwargs["data"] = CallRequest(created_by_id="tb-screener")
    return await orig_goc(self, *args, **kwargs)
getstream.video.async_call.Call.get_or_create = patched_goc

# On Windows, aiortc DTLS cannot complete the handshake with Stream's SFU.
# On Linux (WSL), DTLS works fine, so skip the bypass.
import platform
if platform.system() == "Windows":
    import getstream.video.rtc.pc
    async def _patched_wait(self, timeout: float = 15.0):
        import logging
        logger = logging.getLogger("bot.pc_patch")
        logger.warning(
            f"[PATCH] Bypassing wait_for_connected (state={self.connectionState}, "
            f"iceState={self.iceConnectionState}, iceGathering={self.iceGatheringState})"
        )
        return
    getstream.video.rtc.pc.PublisherPeerConnection.wait_for_connected = _patched_wait

# ---------------------------------------------------------------------------
# Agent instructions
# ---------------------------------------------------------------------------

INSTRUCTIONS = """You are BigTBAI, a friendly and professional health companion for the Gemini Live Medical Diagnostics platform.

Your main goal is to have a natural, empathetic conversation about the user's health concerns and guide them toward appropriate care. This is a comprehensive screening platform that analyzes multiple health indicators—including cough sounds for TB assessment and eye/palm/nail images for anemia detection—providing a thorough health evaluation experience.

CONVERSATION STYLE:
- Be warm, friendly, and conversational
- Keep responses concise and easy to understand

TOOL RULES:
- When the user confirms X-ray upload, call analyze_chest_xray immediately.
- For all other checks (Cough, Eye, Palm, Nail), you can use your **native Gemini audio and vision capabilities** to provide a rough preliminary estimate, but advise the user that the specialized Cloud Run models require them to use the explicit Upload buttons in the UI for clinical-grade analysis.
- Give me a few seconds to run this through our specialist models when you execute a tool.

IMPORTANT:
- You are NOT a doctor—always recommend professional medical consultation
- Explain that all analyses use AI technology and have limitations—professional medical diagnosis is essential
"""

# ---------------------------------------------------------------------------
# Create Agent factory & join_call for the AgentLauncher
# ---------------------------------------------------------------------------

def create_agent() -> Agent:
    llm = GeminiRealtime(api_key=api_key, fps=5)
    
    agent = Agent(
        edge=StreamEdge(),
        agent_user=User(name="BigTBAI", id="tb-screener"),
        instructions=INSTRUCTIONS,
        llm=llm
    )
    
    # Register tools directly on the LLM
    llm.register_function(name="analyze_chest_xray", description="Analyzes the most recently uploaded chest X-ray image for TB indicators.")(analyze_chest_xray)
    llm.register_function(name="analyze_uploaded_cough", description="Analyzes the most recently uploaded cough audio for TB indicators.")(analyze_uploaded_cough)
    llm.register_function(name="analyze_uploaded_palm", description="Analyzes the most recently uploaded palm image for Anemia indicators.")(analyze_uploaded_palm)
    llm.register_function(name="analyze_uploaded_eye", description="Analyzes the most recently uploaded eye image for Anemia indicators.")(analyze_uploaded_eye)
    llm.register_function(name="analyze_uploaded_nail", description="Analyzes the most recently uploaded nail image for Anemia indicators.")(analyze_uploaded_nail)
    
    return agent


async def join_call(agent: Agent, call_type: str, call_id: str):
    """Join the Stream call using Agent's context-manager lifecycle."""
    call = await agent.create_call(call_type, call_id)
    async with agent.join(call):
        print(f"Bot has joined the call: {call_id}")
        await asyncio.Event().wait()


if __name__ == "__main__":
    call_id = os.environ.get("STREAM_CALL_ID")
    if not call_id:
        print("ERROR: No STREAM_CALL_ID provided")
        sys.exit(1)
        
    print(f"Starting Stream Vision Agent for call: {call_id}")

    launcher = AgentLauncher(
        create_agent=create_agent,
        join_call=join_call,
        agent_idle_timeout=0,  # Never auto-leave
    )
    
    runner = Runner(launcher)
    runner.run(
        call_type="default",
        call_id=call_id,
        no_demo=True,
        log_level="DEBUG",
    )
