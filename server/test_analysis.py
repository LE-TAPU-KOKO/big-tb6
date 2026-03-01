#!/usr/bin/env python3
"""Test script to verify TB analysis API works."""

import asyncio
import sys

sys.path.insert(0, "/home/sach/GEMINI_LIVE/server")

from tb_audio_tool import analyze_cough_file


async def test_analysis():
    print("🔍 Testing TB analysis API...")

    # Use a test file - you'll need to record one first
    file_path = "/tmp/test_cough.wav"

    print(f"Analyzing file: {file_path}")
    result = await analyze_cough_file(file_path)

    print(f"\n📋 Result: {result}")
    return result


if __name__ == "__main__":
    result = asyncio.run(test_analysis())
