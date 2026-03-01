This setup uses a Client-Server architecture. Your frontend (React/Next.js) handles the screen capture and microphone (the "eyes and ears"), sending a continuous WebRTC stream to your backend (Python). The backend runs Pipecat, which feeds the stream directly into Gemini Live, allowing it to "see" your screen and trigger your 6 diagnostic models in real-time.

Real-Time Multimodal Brain Setup (Pipecat + Gemini Live)
Prerequisites
Python 3.10+ (For the Pipecat backend)

Node.js 18+ (For the frontend client)

API Keys Required:

GOOGLE_API_KEY (From Google AI Studio for Gemini)

DAILY_API_KEY (Create a free account at Daily.co for the WebRTC transport layer)

Step 1: Environment Setup
Create a new directory for your project and set up the backend and frontend folders.

Bash

mkdir hackathon-brain
cd hackathon-brain

# Backend setup
mkdir server && cd server
python3 -m venv venv
source venv/bin/activate
pip install "pipecat-ai[google,daily]" python-dotenv fastapi uvicorn

# Frontend setup (in a new terminal tab)
cd ../
npx create-next-app@latest client
cd client
npm install @pipecat-ai/client-js @pipecat-ai/client-react
Create a .env file inside your server/ directory:

Code snippet

GOOGLE_API_KEY=your_google_api_key_here
DAILY_API_KEY=your_daily_api_key_here
Step 2: The Backend (The "Brain")
Create server/bot.py. This script sets up the Gemini Live connection, defines your 6 diagnostic models as tools, and streams the incoming WebRTC video/audio directly to the LLM.

Python

import os
import asyncio
from dotenv import load_dotenv
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask
from pipecat.services.google.gemini_live import GeminiLiveLLMService
from pipecat.transports.services.daily import DailyTransport, DailyParams

load_dotenv()

# 1. Define your 6 Diagnostic Models as Functions
async def run_diagnostic_model_1(symptoms: str):
    print(f"Running Model 1 for: {symptoms}")
    return {"diagnosis": "TB Negative, clearing patient."}

# Add all 6 models to the toolset so Gemini can call them
diagnostic_tools = [{
    "function_declarations": [
        {
            "name": "run_diagnostic_model_1",
            "description": "Call this model when you see lung scans or symptoms on the screen.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "symptoms": {"type": "STRING"}
                },
                "required": ["symptoms"]
            }
        }
        # Add the other 5 models here...
    ]
}]

async def main(room_url: str, token: str):
    # 2. Setup WebRTC Transport (Receives screen/audio from frontend)
    transport = DailyTransport(
        room_url,
        token,
        "Medical_Brain",
        DailyParams(audio_in_enabled=True, audio_out_enabled=True, camera_out_enabled=False)
    )

    # 3. Initialize Gemini Live API
    llm = GeminiLiveLLMService(
        api_key=os.getenv("GOOGLE_API_KEY"),
        model="gemini-2.5-flash", # Best model for fast, multimodal live inference
        voice_id="Aoede",         # Built-in voice
        tools=diagnostic_tools,
        system_instruction="You are a medical diagnostic orchestrator. Watch the live screen feed. If you see patient data or scans, analyze them and call the appropriate diagnostic tool. Speak to the user naturally."
    )

    # Register the function back to the LLM
    llm.register_function("run_diagnostic_model_1", run_diagnostic_model_1)

    # 4. Build and Run the Pipeline
    pipeline = Pipeline([
        transport.input(), # Ingest WebRTC screen + mic
        llm,               # Process via Gemini Live
        transport.output() # Output voice response
    ])

    task = PipelineTask(pipeline)
    runner = PipelineRunner()
    
    await runner.run(task)

if __name__ == "__main__":
    # In production, you dynamically generate these via the Daily REST API.
    # For testing, grab a room URL from your Daily.co dashboard.
    ROOM_URL = "https://your-domain.daily.co/your-room-id"
    TOKEN = "your_room_token" 
    asyncio.run(main(ROOM_URL, TOKEN))
Step 3: The Frontend (The "Eyes & Ears")
In your Next.js app, edit client/app/page.tsx. This connects the user's browser to the backend, captures the screen, and sends it over the WebRTC pipe.

TypeScript

'use client';

import { useEffect, useRef, useState } from 'react';
import { PipecatClient } from '@pipecat-ai/client-js';
import { DailyTransport } from '@pipecat-ai/client-js/transports/daily';

export default function Home() {
  const [isConnected, setIsConnected] = useState(false);
  const pipecatRef = useRef<PipecatClient | null>(null);

  useEffect(() => {
    // Initialize the Pipecat client
    const transport = new DailyTransport();
    pipecatRef.current = new PipecatClient({ transport });

    return () => {
      pipecatRef.current?.disconnect();
    };
  }, []);

  const startSession = async () => {
    if (!pipecatRef.current) return;

    try {
      // 1. Get Room URL (In a real app, fetch this from your backend)
      const roomUrl = "https://your-domain.daily.co/your-room-id"; 
      
      // 2. Connect to the Pipecat Server
      await pipecatRef.current.connect({ url: roomUrl });
      
      // 3. Request Microphone Access
      await pipecatRef.current.startAudio();

      // 4. Request Screen Share (The "Eyes" of the Brain)
      const screenStream = await navigator.mediaDevices.getDisplayMedia({
        video: { frameRate: 5 } // Keep framerate low to save bandwidth
      });
      
      // Send the screen video track over the WebRTC transport
      const videoTrack = screenStream.getVideoTracks()[0];
      await pipecatRef.current.transport.sendVideo(videoTrack);

      setIsConnected(true);
      console.log("Brain is now watching and listening.");

    } catch (error) {
      console.error("Failed to start session:", error);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen gap-4">
      <h1 className="text-2xl font-bold">Hackathon Brain Console</h1>
      {!isConnected ? (
        <button 
          onClick={startSession}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Wake Up Brain & Share Screen
        </button>
      ) : (
        <div className="text-green-500 font-semibold animate-pulse">
          Brain is Live: Watching Screen & Listening
        </div>
      )}
    </div>
  );
}
Step 4: How to Run It
Start the Backend: Navigate to your server/ folder and run python bot.py. The Pipecat agent will join the Daily WebRTC room and wait.

Start the Frontend: Navigate to your client/ folder and run npm run dev.

Connect: Open http://localhost:3000, click "Wake Up Brain", and select the window/screen you want Gemini to watch.

The moment you start sharing, the Gemini Live API will receive the video frames and your microphone audio. You can talk to it normally ("Hey, look at this chart, what do you think?"), and if the conditions match your tool descriptions, it will trigger your Python diagnostic functions automatically.

Would you like me to show you how to set up the FastAPI endpoint so your frontend can securely generate the room_url dynamically instead of hardcoding it?

Milliseconds to Magic: Real-Time Workflows using the Gemini Live API and Pipecat
This presentation dives into the specific mechanics of connecting Gemini's multimodal capabilities with Pipecat for low-latency voice and vision workflows.