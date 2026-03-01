# TB Audio Analysis Tool Integration Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create a wrapper for the TB audio analysis API and integrate it as a callable tool in the Gemini Live bot.

**Architecture:** Create a Python module that wraps the external API call, then register it as a function tool with the Gemini Live LLM service using Pipecat's unified function calling framework.

**Tech Stack:** Python, aiohttp, Pipecat (ToolsSchema, FunctionSchema), Google Gemini Live API

---

## Background

The external API accepts audio files via multipart form data:
```bash
curl -X POST -F "file=@/path/to/audio.wav" https://hear-tb-1039179580375.us-central1.run.app/predict
```

We need to wrap this in an async Python function and expose it to Gemini Live as a tool.

---

### Task 1: Create TB Audio Analysis API Wrapper Module

**Files:**
- Create: `/home/sach/GEMINI_LIVE/server/tb_audio_tool.py`
- Test: `/home/sach/GEMINI_LIVE/server/tests/test_tb_audio_tool.py`

**Step 1: Write the failing test**

```python
# /home/sach/GEMINI_LIVE/server/tests/test_tb_audio_tool.py
import pytest
import asyncio

# Test will fail because analyze_cough_sound doesn't exist yet
def test_analyze_cough_sound_returns_prediction():
    result = asyncio.run(analyze_cough_sound("/path/to/test.wav"))
    assert "result" in result or "error" in result
```

Run: `cd /home/sach/GEMINI_LIVE/server && python -m pytest tests/test_tb_audio_tool.py::test_analyze_cough_sound_returns_prediction -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'tb_audio_tool'"

**Step 2: Write minimal implementation**

```python
# /home/sach/GEMINI_LIVE/server/tb_audio_tool.py
"""
TB Audio Analysis Tool - Wrapper for external TB detection API.

This module provides an async function to analyze cough sounds
for TB detection using an external API.
"""

import aiohttp
from typing import Dict, Any, Optional


TB_API_URL = "https://hear-tb-1039179580375.us-central1.run.app/predict"


async def analyze_cough_sound(file_path: str) -> Dict[str, Any]:
    """Analyze a cough sound file for TB indicators.
    
    Args:
        file_path: Path to the audio file (WAV format).
        
    Returns:
        Dict containing either:
        - "result": API response data (TB prediction result)
        - "error": Error message if the request failed
    """
    try:
        async with aiohttp.ClientSession() as session:
            with open(file_path, "rb") as audio_file:
                data = aiohttp.FormData()
                data.add_field(
                    "file",
                    audio_file,
                    filename="cough.wav",
                    content_type="audio/wav"
                )
                
                async with session.post(TB_API_URL, data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {"result": result}
                    else:
                        error_text = await response.text()
                        return {"error": f"API error {response.status}: {error_text}"}
    except FileNotFoundError:
        return {"error": f"File not found: {file_path}"}
    except Exception as e:
        return {"error": str(e)}
```

**Step 3: Run test to verify it passes**

Run: `cd /home/sach/GEMINI_LIVE/server && python -m pytest tests/test_tb_audio_tool.py::test_analyze_cough_sound_returns_prediction -v`
Expected: PASS (or SKIP if file doesn't exist)

**Step 4: Commit**

```bash
cd /home/sach/GEMINI_LIVE
git add server/tb_audio_tool.py server/tests/test_tb_audio_tool.py
git commit -m "feat: add TB audio analysis API wrapper module"
```

---

### Task 2: Integrate TB Tool into Gemini Live Bot

**Files:**
- Modify: `/home/sach/GEMINI_LIVE/server/bot.py`

**Step 1: Write the failing test**

First, verify the current bot.py doesn't have tool integration:
Run: `grep -n "tools" /home/sach/GEMINI_LIVE/server/bot.py`
Expected: No matches (no tools configured yet)

**Step 2: Modify bot.py to add tool integration**

Update `/home/sach/GEMINI_LIVE/server/bot.py` to add:

1. Import the required modules at the top (after existing imports):
```python
from pipecat.adapters.schemas.function_schema import FunctionSchema
from pipecat.adapters.schemas.tools_schema import ToolsSchema
from pipecat.services.llm_service import FunctionCallParams

# Import the TB audio tool
import sys
sys.path.insert(0, "/home/sach/GEMINI_LIVE/server")
from tb_audio_tool import analyze_cough_sound
```

2. Define the tool schema (add before `async def run_bot`):
```python
def get_tb_audio_tool() -> FunctionSchema:
    """Create the TB audio analysis tool schema."""
    return FunctionSchema(
        name="analyze_cough_for_tb",
        description="Analyze a recorded cough sound to help determine if it might indicate Tuberculosis. Use this when the user has a cough and wants to understand if their cough sound patterns suggest TB. Returns probability or assessment results.",
        properties={
            "file_path": {
                "type": "string",
                "description": "The file path to the audio recording of the cough sound to analyze.",
            }
        },
        required=["file_path"],
    )
```

3. Update the LLM initialization in `run_bot` to include tools:
```python
# Create tools schema
tb_tool = get_tb_audio_tool()
tools_schema = ToolsSchema(standard_tools=[tb_tool])

llm = GeminiLiveLLMService(
    api_key=api_key,
    model="gemini-2.5-flash-native-audio-preview-12-2025",
    voice_id="Charon",
    system_instruction="""[existing system prompt]""",
    tools=tools_schema,
)
```

4. Register the function handler (after llm initialization, before pipeline creation):
```python
@llm.function_call_handler()
async def handle_tb_analysis(params: FunctionCallParams):
    """Handle TB audio analysis function calls from Gemini."""
    function_name = params.function_name
    args = params.arguments
    
    if function_name == "analyze_cough_for_tb":
        file_path = args.get("file_path")
        if not file_path:
            return {"error": "No file path provided"}
        
        result = await analyze_cough_sound(file_path)
        return result
    
    return {"error": f"Unknown function: {function_name}"}
```

**Step 3: Run to verify it works**

Run backend:
```bash
cd /home/sach/GEMINI_LIVE/server
./venv/bin/python bot.py -t webrtc --host localhost --port 7860
```

Expected: Bot starts without errors, LLM service shows tools are loaded

**Step 4: Commit**

```bash
cd /home/sach/GEMINI_LIVE
git add server/bot.py
git commit -m "feat: integrate TB audio analysis tool into Gemini Live bot"
```

---

### Task 3: Test End-to-End Tool Calling

**Step 1: Start the backend**

```bash
cd /home/sach/GEMINI_LIVE/server
./venv/bin/python bot.py -t webrtc --host localhost --port 7860
```

**Step 2: Start the frontend**

```bash
cd /home/sach/GEMINI_LIVE/client
npm run dev
```

**Step 3: Test the tool**

1. Open http://localhost:3000
2. Click "Start Consultation"
3. Say: "I'd like to analyze my cough for TB. The recording is at /home/sach/Downloads/Telegram Desktop/2.wav"
4. Gemini should recognize the tool call and return results

Expected: Tool is called, results are returned to Gemini, Gemini explains the results to user

**Step 4: Commit**

```bash
cd /home/sach/GEMINI_LIVE
git add -A
git commit -m "test: verify TB audio tool integration works end-to-end"
```

---

## Summary

This implementation adds:
1. `server/tb_audio_tool.py` - Async wrapper for the TB audio analysis API
2. Tool registration in `server/bot.py` - Exposes the tool to Gemini Live via ToolsSchema
3. Function handler - Processes tool calls and returns results to Gemini

The tool can now be called by saying something like "analyze my cough sound" during the consultation.
