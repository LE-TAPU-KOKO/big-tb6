import os
import asyncio
import subprocess
import aiohttp
import time
import json
from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from xray_store import set_latest_xray_path

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STREAM_API_KEY = os.getenv("STREAM_API_KEY")
STREAM_API_SECRET = os.getenv("STREAM_API_SECRET")

try:
    if STREAM_API_KEY and STREAM_API_SECRET:
        from getstream import Stream
        stream_client = Stream(api_key=STREAM_API_KEY, api_secret=STREAM_API_SECRET)
    else:
        stream_client = None
except Exception as e:
    print(f"Failed to initialize Stream client: {e}")
    stream_client = None

# SSE subscribers for bot transcript streaming.
_bot_text_subscribers: set[asyncio.Queue] = set()


@app.on_event("startup")
async def _on_startup():
    app.state.loop = asyncio.get_running_loop()


async def _broadcast_bot_text(payload: dict) -> None:
    message = json.dumps(payload)
    for queue in list(_bot_text_subscribers):
        await queue.put(message)


def _publish_bot_text_from_thread(payload: dict) -> None:
    loop = getattr(app.state, "loop", None)
    if not loop or not loop.is_running():
        return
    asyncio.run_coroutine_threadsafe(_broadcast_bot_text(payload), loop)


class RoomResponse(BaseModel):
    url: str
    token: str


async def create_stream_session():
    """Create a Stream session token and generated call ID"""
    if not stream_client:
        raise HTTPException(
            status_code=500, detail="Missing Stream API credentials in environment variables"
        )
    user_id = "tb-screener-user"
    token = stream_client.create_token(user_id)
    call_id = f"tb-screening-{int(time.time())}"
    return {"url": call_id, "token": token}


@app.get("/")
async def root():
    return {"status": "ok", "message": "Medical Brain API is running"}


@app.post("/create-room", response_model=RoomResponse)
async def create_room():
    """Create a new Stream Session for a session"""
    try:
        room_data = await create_stream_session()
        return RoomResponse(**room_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/start-bot")
async def start_bot(request: Request):
    """Start the Pipecat bot in the specified room"""
    try:
        body = await request.json()
        room_url = body.get("room_url")
        token = body.get("token")

        if not room_url or not token:
            raise HTTPException(status_code=400, detail="Missing room_url or token")

        # Build env vars to pass to the bot
        env_exports = []
        env_exports.append(f'export STREAM_CALL_ID="{room_url}"')
        if STREAM_API_KEY:
            env_exports.append(f'export STREAM_API_KEY="{STREAM_API_KEY}"')
        if STREAM_API_SECRET:
            env_exports.append(f'export STREAM_API_SECRET="{STREAM_API_SECRET}"')
        google_key = os.environ.get("GOOGLE_API_KEY", "")
        if google_key:
            env_exports.append(f'export GOOGLE_API_KEY="{google_key}"')

        # Convert Windows server path to WSL path
        server_dir = os.path.dirname(os.path.abspath(__file__))
        # X:\med\server -> /mnt/x/med/server
        wsl_server_dir = server_dir.replace("\\", "/")
        drive_letter = wsl_server_dir[0].lower()
        wsl_server_dir = f"/mnt/{drive_letter}/{wsl_server_dir[3:]}"

        env_str = " && ".join(env_exports)
        wsl_cmd = (
            f"cd {wsl_server_dir} && "
            f"{env_str} && "
            f"source ~/med-venv/bin/activate && "
            f"python bot.py"
        )

        process = subprocess.Popen(
            ["wsl", "-d", "Ubuntu", "--", "bash", "-c", wsl_cmd],
            cwd=server_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            bufsize=1,
        )

        import threading

        def _stream_logs(stream, prefix: str):
            for line in iter(stream.readline, ""):
                if line:
                    if line.startswith("BOT_TEXT:"):
                        raw = line[len("BOT_TEXT:") :].strip()
                        try:
                            payload = json.loads(raw)
                        except json.JSONDecodeError:
                            payload = {"text": raw}
                        _publish_bot_text_from_thread(payload)
                    print(f"{prefix}{line.rstrip()}")
            stream.close()

        def _log_bot_exit(proc: subprocess.Popen):
            return_code = proc.wait()
            print(f"Bot process exited with code {return_code}")

        if process.stdout:
            threading.Thread(
                target=_stream_logs, args=(process.stdout, "[bot][stdout] "), daemon=True
            ).start()
        if process.stderr:
            threading.Thread(
                target=_stream_logs, args=(process.stderr, "[bot][stderr] "), daemon=True
            ).start()
        threading.Thread(target=_log_bot_exit, args=(process,), daemon=True).start()
        return {"status": "started", "pid": process.pid}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/events")
async def events():
    """Server-sent events stream for bot transcripts."""
    queue: asyncio.Queue[str] = asyncio.Queue()
    _bot_text_subscribers.add(queue)

    async def event_generator():
        try:
            while True:
                data = await queue.get()
                yield f"data: {data}\n\n"
        except asyncio.CancelledError:
            pass  # Client disconnected or server is shutting down
        finally:
            _bot_text_subscribers.discard(queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/upload_xray")
async def upload_xray(file: UploadFile = File(...)):
    """Upload a chest X-ray image and store latest path for analysis."""
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="Missing filename")

        safe_name = "".join(
            c if c.isalnum() or c in "-_." else "_" for c in file.filename
        )
        capture_dir = os.path.join(os.path.dirname(__file__), "xray_images")
        os.makedirs(capture_dir, exist_ok=True)

        timestamp = int(time.time())
        file_path = os.path.join(capture_dir, f"xray_{timestamp}_{safe_name}")

        contents = await file.read()
        if not contents:
            raise HTTPException(status_code=400, detail="Empty file")

        with open(file_path, "wb") as f:
            f.write(contents)

        set_latest_xray_path(file_path)
        return {"status": "ok", "path": file_path}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
