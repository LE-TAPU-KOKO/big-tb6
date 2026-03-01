#!/usr/bin/env python3
"""Test script to verify audio recording works."""

import asyncio
import pyaudio
import wave
import sys

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 24000
RECORD_SECONDS = 4


async def test_recording():
    print("🎤 Testing audio recording...")
    print(f"Recording for {RECORD_SECONDS} seconds...")

    audio = pyaudio.PyAudio()

    stream = audio.open(
        format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK
    )

    frames = []

    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)
        print(
            f"Recorded chunk {i + 1}/{int(RATE / CHUNK * RECORD_SECONDS)} - {len(data)} bytes"
        )

    print("Recording complete!")

    stream.stop_stream()
    stream.close()
    audio.terminate()

    # Save to file
    output_file = "/tmp/test_cough.wav"
    wf = wave.open(output_file, "wb")
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(audio.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b"".join(frames))
    wf.close()

    print(f"✅ Audio saved to: {output_file}")
    return output_file


if __name__ == "__main__":
    result = asyncio.run(test_recording())
    print(f"\nResult: {result}")
