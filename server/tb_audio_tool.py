"""TB Audio Tool - Record and analyze cough sounds for TB detection."""

import os
import time
import wave
import numpy as np
import aiohttp
from typing import Dict, Any


TB_API_URL = os.getenv(
    "TB_API_URL",
    "https://hear-tb-1039179580375.us-central1.run.app/predict",
)


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

    with wave.open(file_path, "wb") as wav_file:
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
            with open(file_path, "rb") as audio_file:
                data = aiohttp.FormData()
                data.add_field(
                    "file", audio_file, filename="cough.wav", content_type="audio/wav"
                )

                async with session.post(TB_API_URL, data=data) as response:
                    if response.status == 200:
                        api_result = await response.json()
                        tb_prob = api_result.get("tb_probability", 0)

                        if tb_prob >= 0.7:
                            interpretation = "High probability of TB - recommend immediate professional consultation"
                        elif tb_prob >= 0.4:
                            interpretation = (
                                "Moderate probability - recommend getting tested"
                            )
                        else:
                            interpretation = "Low probability - monitor symptoms"

                        return {
                            "result": {
                                "tb_probability": tb_prob,
                                "interpretation": interpretation,
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
