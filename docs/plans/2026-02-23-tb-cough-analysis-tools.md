# TB Cough Analysis Tool Integration Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create two Gemini Live tools - one to record user cough audio to a WAV file, and one to analyze that WAV file via external TB detection API.

**Architecture:** Use Pipecat's AudioBufferProcessor to capture user audio from the live conversation pipeline. When `record_cough_sound` is triggered, ask user to cough, capture audio via turn events, save as WAV to /tmp/. When `analyze_cough_for_tb` is triggered with a file path, send to external API and return parsed result.

**Tech Stack:** Python, aiohttp, wave, numpy, Pipecat (AudioBufferProcessor, ToolsSchema, FunctionSchema), Google Gemini Live API

---

## Background

The external TB detection API accepts audio files via multipart form data:
```bash
curl -X POST -F "file=@/path/to/audio.wav" https://hear-tb-1039179580375.us-central1.run.app/predict
```

Expected API response:
```json
{"tb_probability": 0.7507437467575073}
```

We need two separate tools:
1. `record_cough_sound` - Captures audio from conversation and saves to /tmp/cough_<timestamp>.wav
2. `analyze_cough_for_tb` - Sends saved WAV to API and returns parsed result

---

### Task 1: Create TB Audio Tool Module

**Files:**
- Create: `/home/sach/GEMINI_LIVE/server/tb_audio_tool.py`

**Step 1: Write the failing test**

Create `/home/sach/GEMINI_LIVE/server/tests/test_tb_audio_tool.py`:

```python
import pytest
import os
import tempfile

def test_save_audio_to_wav_creates_valid_file():
    import numpy as np
    from tb_audio_tool import save_audio_to_wav
    
    sample_rate = 16000
    duration = 1
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio_data = (np.sin(2 * np.pi * 440 * t) * 32767).astype(np.int16).tobytes()
    
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        temp_path = f.name
    
    try:
        save_audio_to_wav(audio_data, sample_rate, temp_path)
        assert os.path.exists(temp_path)
        assert os.path.getsize(temp_path) > 44
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
```

Run: `cd /home/sach/GEMINI_LIVE/server && ./venv/bin/python -m pytest tests/test_tb_audio_tool.py::test_save_audio_to_wav_creates_valid_file -v`
Expected: FAIL - ModuleNotFoundError: No module named 'tb_audio_tool'

**Step 2: Write minimal implementation**

Create `/home/sach/GEMINI_LIVE/server/tb_audio_tool.py`:

```python
"""TB Audio Tool - Record and analyze cough sounds for TB detection."""

import os
import time
import wave
import numpy as np
import aiohttp
from typing import Dict, Any


TB_API_URL = "https://hear-tb-1039179580375.us-central1.run.app/predict"


def save_audio_to_wav(audio_data: bytes, sample_rate: int, file_path: str) -> str:
    """Save raw PCM audio data to a WAV file.
    
    Args:
        audio_data: Raw PCM audio bytes (16-bit signed integers)
        sample_rate: Sample rate in Hz
        file_path: Path where the WAV file will be saved
        
    Returns:
        The file path where the audio was saved
    """
    audio_array = np.frombuffer(audio_data, dtype=np.int16)
    
    with wave.open(file_path, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_array.tobytes())
    
    return file_path


async def analyze_cough_file(file_path: str) -> Dict[str, Any]:
    """Analyze a cough sound file for TB indicators.
    
    Args:
        file_path: Path to the WAV audio file
        
    Returns:
        Dict containing either:
        - "result": {"tb_probability": float, "interpretation": str}
        - "error": Error message if the request failed
    """
    if not os.path.exists(file_path):
        return {"error": f"File not found: {file_path}"}
    
    try:
        async with aiohttp.ClientSession() as session:
            with open(file_path, 'rb') as audio_file:
                data = aiohttp.FormData()
                data.add_field(
                    "file",
                    audio_file,
                    filename="cough.wav",
                    content_type="audio/wav"
                )
                
                async with session.post(TB_API_URL, data=data) as response:
                    if response.status == 200:
                        api_result = await response.json()
                        tb_prob = api_result.get("tb_probability", 0)
                        
                        if tb_prob >= 0.7:
                            interpretation = "High probability of TB - recommend immediate professional consultation"
                        elif tb_prob >= 0.4:
                            interpretation = "Moderate probability - recommend getting tested"
                        else:
                            interpretation = "Low probability - monitor symptoms"
                        
                        return {
                            "result": {
                                "tb_probability": tb_prob,
                                "interpretation": interpretation
                            }
                        }
                    else:
                        error_text = await response.text()
                        return {"error": f"API error {response.status}: {error_text}"}
    except Exception as e:
        return {"error": str(e)}


class AudioCapture:
    """Captures audio from Pipecat pipeline for TB analysis."""
    
    def __init__(self):
        self._audio_buffer: bytearray = bytearray()
        self._sample_rate: int = 24000
        self._recording: bool = False
    
    async def start_recording(self):
        """Start capturing audio."""
        self._audio_buffer = bytearray()
        self._recording = True
    
    def add_audio(self, audio_chunk: bytes):
        """Add audio chunk to buffer."""
        if self._recording:
            self._audio_buffer.extend(audio_chunk)
    
    async def stop_recording(self) -> bytes:
        """Stop capturing and return audio data."""
        self._recording = False
        return bytes(self._audio_buffer)
    
    @property
    def audio_data(self) -> bytes:
        """Get current audio buffer."""
        return bytes(self._audio_buffer)
    
    def clear(self):
        """Clear the audio buffer."""
        self._audio_buffer = bytearray()
    
    def save_to_wav(self, sample_rate: int = 24000) -> str:
        """Save current audio buffer to a WAV file in /tmp/.
        
        Returns:
            Path to the saved WAV file
        """
        timestamp = int(time.time() * 1000)
        file_path = f"/tmp/cough_{timestamp}.wav"
        return save_audio_to_wav(self.audio_data, sample_rate, file_path)
```

**Step 3: Run test to verify it passes**

Run: `cd /home/sach/GEMINI_LIVE/server && ./venv/bin/python -m pytest tests/test_tb_audio_tool.py::test_save_audio_to_wav_creates_valid_file -v`
Expected: PASS

**Step 4: Commit**

```bash
cd /home/sach/GEMINI_LIVE
git add server/tb_audio_tool.py server/tests/test_tb_audio_tool.py
git commit -m "feat: add TB audio tool module with record and analyze functions"
```

---

### Task 2: Integrate Two Tools into Gemini Live Bot

**Files:**
- Modify: `/home/sach/GEMINI_LIVE/server/bot.py:1-145`

**Step 1: Verify current state**

Run: `grep -n "tools\|FunctionSchema\|ToolsSchema" /home/sach/GEMINI_LIVE/server/bot.py`
Expected: No output (no tools configured yet)

**Step 2: Add imports at top of bot.py**

Add after existing imports (around line 4):

```python
from pipecat.adapters.schemas.function_schema import FunctionSchema
from pipecat.adapters.schemas.tools_schema import ToolsSchema
from pipecat.services.llm_service import FunctionCallParams
from pipecat.processors.audio.audio_buffer_processor import AudioBufferProcessor
import asyncio

import sys
sys.path.insert(0, "/home/sach/GEMINI_LIVE/server")
from tb_audio_tool import analyze_cough_file, AudioCapture
```

**Step 3: Create audio capture instance**

Add after imports (around line 16):

```python
audio_capture = AudioCapture()
```

**Step 4: Add tool schemas**

Add before `async def run_bot` (around line 26):

```python
def get_record_tool() -> FunctionSchema:
    """Tool to record user's cough sound."""
    return FunctionSchema(
        name="record_cough_sound",
        description="Record the user's cough sound for TB analysis. When called, tell the user to cough clearly into the microphone for 3-5 seconds. This will capture and save their cough as a WAV file. Returns the file path of the recorded audio.",
        properties={},
        required=[],
    )


def get_analyze_tool() -> FunctionSchema:
    """Tool to analyze recorded cough for TB probability."""
    return FunctionSchema(
        name="analyze_cough_for_tb",
        description="Analyze a previously recorded cough sound file to determine TB probability. Use this after record_cough_sound has been called. Input is the file path returned from the recording tool.",
        properties={
            "file_path": {
                "type": "string",
                "description": "The file path of the recorded cough audio (returned from record_cough_sound)",
            }
        },
        required=["file_path"],
    )
```

**Step 5: Update LLM initialization**

In `run_bot` function, find the GeminiLiveLLMService creation (around line 43) and update:

```python
record_tool = get_record_tool()
analyze_tool = get_analyze_tool()
tools_schema = ToolsSchema(standard_tools=[record_tool, analyze_tool])

llm = GeminiLiveLLMService(
    api_key=api_key,
    model="gemini-2.5-flash-native-audio-preview-12-2025",
    voice_id="Charon",
    system_instruction="""You are BigTB6, a personal health companion specializing in Tuberculosis (TB) diagnosis.
            
Your primary role is to help users determine if they might have TB symptoms and guide them through a diagnostic conversation.

CONVERSATION FLOW:
1. GREETING: As soon as the user connects, warmly greet them and introduce yourself.
2. SYMPTOM INQUIRY: Ask one question at a time about TB-related symptoms.
3. COUGH ANALYSIS: If the user has a cough and wants to analyze it, use the tools:
   - First call record_cough_sound to record their cough
   - Then call analyze_cough_for_tb with the file path returned
   - Explain the results to the user

IMPORTANT TOOLS USAGE:
- When user wants cough analysis, say: "I'll record your cough now. Please cough clearly into your microphone for a few seconds."
- Call record_cough_sound tool
- After getting file path, call analyze_cough_for_tb with that path
- Present results with interpretation

IMPORTANT:
- You are NOT a doctor - always recommend professional medical consultation
- Never prescribe medication
- Handle sensitive health information with care
- Your output will be spoken aloud, so avoid special characters and emojis
- Keep responses concise and natural-sounding
""",
    tools=tools_schema,
)
```

**Step 6: Add function handler**

After llm initialization (around line 98, before pipeline creation):

```python
@llm.function_call_handler()
async def handle_tool_calls(params: FunctionCallParams):
    """Handle TB analysis tool calls from Gemini."""
    function_name = params.function_name
    args = params.arguments
    
    if function_name == "record_cough_sound":
        await audio_capture.start_recording()
        await asyncio.sleep(4)
        audio_data = await audio_capture.stop_recording()
        
        if len(audio_data) == 0:
            return {"error": "No audio recorded. Please try again and cough clearly."}
        
        file_path = audio_capture.save_to_wav(24000)
        return {"file_path": file_path, "status": "recorded"}
    
    elif function_name == "analyze_cough_for_tb":
        file_path = args.get("file_path")
        if not file_path:
            return {"error": "No file path provided"}
        
        result = await analyze_cough_file(file_path)
        return result
    
    return {"error": f"Unknown function: {function_name}"}
```

**Step 7: Add AudioBufferProcessor to pipeline**

After llm initialization, before pipeline creation (around line 130):

```python
audio_buffer = AudioBufferProcessor(
    enable_turn_audio=True,
    num_channels=1,
    sample_rate=24000,
)


@audio_buffer.event_handler("on_user_turn_audio_data")
async def on_user_audio(audio_bytes: bytes, sample_rate: int, channels: int):
    audio_capture.add_audio(audio_bytes)


pipeline = Pipeline([transport.input(), audio_buffer, llm, transport.output()])
```

**Step 8: Test the bot starts**

Run: `cd /home/sach/GEMINI_LIVE/server && timeout 10 ./venv/bin/python bot.py -t webrtc --host localhost --port 7860 2>&1 || true`
Expected: No errors about missing modules or syntax errors

**Step 9: Commit**

```bash
cd /home/sach/GEMINI_LIVE
git add server/bot.py
git commit -m "feat: integrate record and analyze tools into Gemini Live bot"
```

---

### Task 3: Test End-to-End Tool Calling

**Step 1: Start the backend**

Terminal 1:
```bash
cd /home/sach/GEMINI_LIVE/server
./venv/bin/python bot.py -t webrtc --host localhost --port 7860
```

**Step 2: Start the frontend**

Terminal 2:
```bash
cd /home/sach/GEMINI_LIVE/client
npm run dev
```

**Step 3: Verify tool works**

1. Open http://localhost:3000
2. Click "Start Consultation"
3. Say: "I'd like to analyze my cough for TB"

Expected flow:
- Gemini triggers `record_cough_sound` → says "Please cough clearly..."
- Audio captured for ~4 seconds → saved to /tmp/cough_<timestamp>.wav
- Gemini triggers `analyze_cough_for_tb` with file path
- API returns `{"tb_probability": 0.75}`
- Gemini says: "Based on your cough analysis, there's a 75% probability... High probability of TB - recommend immediate professional consultation"

**Step 4: Commit**

```bash
cd /home/sach/GEMINI_LIVE
git add -A
git commit -m "test: verify TB cough analysis tools work end-to-end"
```

---

## Summary

This implementation adds:

1. `/home/sach/GEMINI_LIVE/server/tb_audio_tool.py`:
   - `save_audio_to_wav()` - Saves PCM bytes to WAV file
   - `analyze_cough_file()` - Sends WAV to TB API, returns parsed result
   - `AudioCapture` class - Manages audio buffer from pipeline

2. Modified `/home/sach/GEMINI_LIVE/server/bot.py`:
   - Added two tool schemas: `record_cough_sound` and `analyze_cough_for_tb`
   - Registered tools with GeminiLiveLLMService
   - Added function handler to process tool calls
   - Added AudioBufferProcessor to pipeline to capture user audio

The user can now say "analyze my cough" and Gemini will guide them through recording and analyzing their cough sound.
