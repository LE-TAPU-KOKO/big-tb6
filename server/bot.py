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

from palm_anemia_tool import analyze_palm_file
from eye_anemia_tool import analyze_eye_file
from nail_anemia_tool import analyze_nail_file
import time

# ---------------------------------------------------------------------------
# Native Capture Logic & Global State
# ---------------------------------------------------------------------------
import time

latest_video_frame = None
recording_audio = False
audio_buffer = bytearray()

# 1. Monkey-patch GeminiRealtime to capture the latest VideoFrame
old_send_video_frame = GeminiRealtime._send_video_frame
async def new_send_video_frame(self, frame):
    global latest_video_frame
    latest_video_frame = frame
    return await old_send_video_frame(self, frame)
GeminiRealtime._send_video_frame = new_send_video_frame

# 2. Audio tracking event callback
from vision_agents.core.edge.events import AudioReceivedEvent
async def handle_audio(event: AudioReceivedEvent):
    global recording_audio, audio_buffer
    if recording_audio and getattr(event, "pcm_data", None):
        try:
            audio_buffer.extend(event.pcm_data.to_bytes())
        except Exception:
            pass

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
    """Invokes the TB cough analysis endpoint."""
    global recording_audio, audio_buffer
    print("Recording audio for 5 seconds...")
    audio_buffer = bytearray()
    recording_audio = True
    await asyncio.sleep(5.0)
    recording_audio = False
    print("Stopped recording audio.")
    
    if len(audio_buffer) == 0:
        return json.dumps({"error": "No audio was collected."})
        
    path = f"/tmp/cough_{int(time.time())}.wav"
    try:
        save_audio_to_wav(bytes(audio_buffer), 48000, path)
        res = await analyze_cough_file(path)
        return json.dumps({"status": "Success. Present this predicted score to the user.", "tb_prediction": res})
    except Exception as e:
        return json.dumps({"error": str(e)})

async def analyze_uploaded_palm() -> str:
    """Invokes the Palm Anemia endpoint."""
    global latest_video_frame
    if latest_video_frame is None:
        return json.dumps({"error": "No video frame available. Please ask user to turn on their camera."})
        
    path = f"/tmp/palm_{int(time.time())}.jpg"
    try:
        img = latest_video_frame.to_image()
        img.save(path)
        res = await analyze_palm_file(path)
        return json.dumps({"status": "Success. Present this predicted score to the user.", "anemia_prediction": res})
    except Exception as e:
        return json.dumps({"error": str(e)})

async def analyze_uploaded_eye() -> str:
    """Invokes the Eye Anemia endpoint."""
    global latest_video_frame
    if latest_video_frame is None:
        return json.dumps({"error": "No video frame available. Please ask user to turn on their camera."})
        
    path = f"/tmp/eye_{int(time.time())}.jpg"
    try:
        img = latest_video_frame.to_image()
        img.save(path)
        res = await analyze_eye_file(path)
        return json.dumps({"status": "Success. Present this predicted score to the user.", "anemia_prediction": res})
    except Exception as e:
        return json.dumps({"error": str(e)})

async def analyze_uploaded_nail() -> str:
    """Invokes the Nail Anemia endpoint."""
    global latest_video_frame
    if latest_video_frame is None:
        return json.dumps({"error": "No video frame available. Please ask user to turn on their camera."})
        
    path = f"/tmp/nail_{int(time.time())}.jpg"
    try:
        img = latest_video_frame.to_image()
        img.save(path)
        res = await analyze_nail_file(path)
        return json.dumps({"status": "Success. Present this predicted score to the user.", "anemia_prediction": res})
    except Exception as e:
        return json.dumps({"error": str(e)})

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

Your main goal is to have a natural, empathetic conversation about the user's health concerns and guide them toward appropriate care. The platform is a comprehensive screening platform that analyzes multiple health indicators—including cough sounds for TB assessment, eye/palm/nail images for anemia detection, and chest X-rays.

CONVERSATION STYLE & FLOW:
1. Greet the user warmly and interview them about their symptoms (especially TB "B-side" symptoms like fever, weight loss, night sweats, etc.).
2. Do not barrage the user with commands. Guide them step-by-step through the required diagnostic checks.
3. Be warm, concise, and easy to understand.

AUTOMATED CAPTURES & TOOL RULES:
IMPORTANT: You must NOT ask the user to upload anything EXCEPT the Chest X-ray. For all other modalities, you must "automatically capture" the inputs natively.

- EYE, PALM, AND NAIL (Anemia): Instruct the user to position their eye, palm, or fingernail clearly in front of the camera. Once they are in position, execute the corresponding tool (e.g. analyze_eye). The tool will automatically capture the video frame and send it to the specialized clinical endpoint. The tool will return the actual endpoint's estimation score and finding, which you will then verbally present to the user.
- COUGH (TB): Ask the user to cough into the microphone. Once they cough, execute the analyze_cough tool. It will automatically record the audio buffer for a few seconds, process it through the endpoint, and return the true endpoint TB risk score. Present this score to the user.
- CHEST X-RAY: This is the ONLY input the user must explicitly upload. Ask them to upload it via the UI dashboard. When they confirm the upload, execute the `analyze_chest_xray` tool immediately. Wait a few seconds for the result.

FINAL REPORTING (MedGemma):
Once all the tests (Interview, Cough, Eye/Palm/Nail, and Chest X-ray) are completed, tell the user that you are "sending all findings to MedGemma for the final evaluation". 
Then, conclude the conversation by generating a short, cohesive summary of the final report, synthesizing all the probabilities, scores, and interview findings, and advising them on their next clinical steps.

IMPORTANT LIMITATIONS:
- You are not a human doctor—always strongly recommend professional medical consultation.
- Explain that all analyses use AI technology and have limitations.
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
    
    # Attach audio tracker
    agent.events.on(AudioReceivedEvent, handle_audio)
    
    # Register tools directly on the LLM
    llm.register_function(name="analyze_chest_xray", description="Analyzes the most recently uploaded chest X-ray image for TB indicators. THIS IS THE ONLY TOOL THAT USES AN UPLOAD.")(analyze_chest_xray)
    llm.register_function(name="analyze_cough", description="Triggers the TB cough analysis endpoint using the native audio stream you are hearing.")(analyze_uploaded_cough)
    llm.register_function(name="analyze_palm", description="Triggers the Palm anemia endpoint using the native video stream you are seeing.")(analyze_uploaded_palm)
    llm.register_function(name="analyze_eye", description="Triggers the Eye anemia endpoint using the native video stream you are seeing.")(analyze_uploaded_eye)
    llm.register_function(name="analyze_nail", description="Triggers the Nail anemia endpoint using the native video stream you are seeing.")(analyze_uploaded_nail)
    
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
