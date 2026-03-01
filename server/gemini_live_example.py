#
# Copyright (c) 2024-2026, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

import os
import asyncio

from dotenv import load_dotenv
from loguru import logger

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.frames.frames import LLMMessagesAppendFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.audio.vad_processor import VADProcessor
from pipecat.runner.types import RunnerArguments
from pipecat.runner.utils import (
    create_transport,
    maybe_capture_participant_camera,
    maybe_capture_participant_screen,
)
from pipecat.services.google.gemini_live.llm import GeminiLiveLLMService
from pipecat.transports.base_transport import BaseTransport, TransportParams
from pipecat.transports.daily.transport import DailyParams
from pipecat.transports.websocket.fastapi import FastAPIWebsocketParams

# Load environment variables
load_dotenv(override=True)


# We use lambdas to defer transport parameter creation until the transport
# type is selected at runtime.
transport_params = {
    "daily": lambda: DailyParams(
        audio_in_enabled=True,
        audio_out_enabled=True,
        # set stop_secs to something roughly similar to the internal setting
        # of the Multimodal Live api, just to align events.
    ),
    "twilio": lambda: FastAPIWebsocketParams(
        audio_in_enabled=True,
        audio_out_enabled=True,
        # set stop_secs to something roughly similar to the internal setting
        # of the Multimodal Live api, just to align events.
    ),
    "webrtc": lambda: TransportParams(
        audio_in_enabled=True,
        audio_out_enabled=True,
        video_in_enabled=True,
        camera_out_enabled=True,
    ),
}


async def run_bot(transport: BaseTransport, runner_args: RunnerArguments):
    logger.info(f"Starting bot")

    # Detailed system prompt for TB diagnosis health companion
    system_instruction = """
    You are Dr. AI, a personal health companion specializing in Tuberculosis (TB) diagnosis.
    
    Your primary role is to help users determine if they might have TB symptoms and guide them through a diagnostic conversation.
    
    CONVERSATION FLOW:
    1. GREETING: As soon as the user connects, warmly greet them and introduce yourself.
       Example: "Hello! I'm Dr. AI, your personal health companion. I'm here to help you assess your health today. How are you feeling?"
    
    2. SYMPTOM INQUIRY: Ask one question at a time about TB-related symptoms:
       - Cough duration (cough lasting more than 3 weeks)
       - Cough severity (dry vs productive)
       - Fever patterns
       - Night sweats
       - Weight loss
       - Fatigue levels
       - Chest pain
       - Loss of appetite
       - Previous TB exposure or contact
    
    3. RISK FACTORS: Ask about:
       - Recent travel to TB-prone areas
       - Contact with TB patients
       - HIV status (if comfortable sharing)
       - Diabetes
       - Smoking history
       - Malnutrition
    
    4. VISUAL OBSERVATION: If the user shares their camera, observe and comment on their appearance (visible weight loss, pallor, fatigue).
    
    5. SCREEN ANALYSIS: If the user shares their screen showing medical reports, X-rays, or test results, analyze and discuss them.
    
    6. RECOMMENDATION: Based on symptoms and risk factors, provide a preliminary assessment and recommend next steps (see a doctor, get tested, etc.)
    
    COMMUNICATION STYLE:
    - Be conversational, warm, and empathetic
    - Ask ONE question at a time - never overwhelm the user
    - Listen actively to their responses
    - Validate their concerns
    - Use simple language, avoid medical jargon
    - Your output will be spoken aloud, so avoid special characters, emojis, or bullet points
    - Keep responses concise and natural-sounding
    
    IMPORTANT:
    - You are NOT a doctor - always recommend professional medical consultation
    - Never prescribe medication
    - Handle sensitive health information with care
    - If user shows severe symptoms, urge them to seek immediate medical attention
    """

    llm = GeminiLiveLLMService(
        api_key=os.getenv("GOOGLE_API_KEY"),
        system_instruction=system_instruction,
        voice_id="Puck",  # Aoede, Charon, Fenrir, Kore, Puck
    )

    vad_processor = VADProcessor(
        vad_analyzer=SileroVADAnalyzer(params=VADParams(stop_secs=0.5))
    )

    # Build the pipeline
    pipeline = Pipeline(
        [
            transport.input(),
            vad_processor,
            llm,
            transport.output(),
        ]
    )

    # Configure the pipeline task
    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            enable_metrics=True,
            enable_usage_metrics=True,
        ),
        idle_timeout_secs=runner_args.pipeline_idle_timeout_secs,
    )

    # Handle client connection event
    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        logger.info(f"Client connected: {client}")

        # Start capturing camera and screen
        await maybe_capture_participant_camera(transport, client, framerate=1)
        await maybe_capture_participant_screen(transport, client, framerate=1)

        # Unpause video input
        llm.set_video_input_paused(False)

        # Kick off the conversation - ask Gemini to greet and start diagnosis
        await task.queue_frames(
            [
                LLMMessagesAppendFrame(
                    messages=[
                        {
                            "role": "user",
                            "content": "Please greet the user warmly, introduce yourself as Dr. AI their personal health companion, and ask how they're feeling today to start the TB symptom assessment conversation.",
                        }
                    ]
                )
            ]
        )

    # Handle client disconnection events
    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info(f"Client disconnected")
        await task.cancel()

    # Run the pipeline
    runner = PipelineRunner(handle_sigint=runner_args.handle_sigint)
    await runner.run(task)


async def bot(runner_args: RunnerArguments):
    """Main bot entry point compatible with Pipecat Cloud."""
    transport = await create_transport(runner_args, transport_params)
    await run_bot(transport, runner_args)


if __name__ == "__main__":
    from pipecat.runner.run import main

    main()
