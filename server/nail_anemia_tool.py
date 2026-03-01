"""Nail Analysis Tool - Analyze fingernail images via external API."""

import os
from typing import Any, Dict

import aiohttp


NAIL_API_URL = os.getenv(
    "NAIL_API_URL",
    "https://nail-anemia-1039179580375.us-central1.run.app/predict",
)


async def analyze_nail_file(file_path: str) -> Dict[str, Any]:
    """Analyze a fingernail image file for indicators.

    Args:
        file_path: Path to the image file

    Returns:
        Dict containing either:
        - "result": API response
        - "error": Error message if the request failed
    """
    if not os.path.exists(file_path):
        return {"error": f"File not found: {file_path}"}

    try:
        timeout = aiohttp.ClientTimeout(total=90)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            with open(file_path, "rb") as image_file:
                image_bytes = image_file.read()
            if not image_bytes:
                return {"error": f"Empty image file: {file_path}"}

            data = aiohttp.FormData()
            data.add_field(
                "image",
                image_bytes,
                filename="nail.png",
                content_type="image/png",
            )

            async with session.post(NAIL_API_URL, data=data) as response:
                if response.status == 200:
                    try:
                        api_result = await response.json()
                        return {"result": api_result}
                    except Exception:
                        text = await response.text()
                        return {"result_text": text}
                else:
                    error_text = await response.text()
                    return {"error": f"API error {response.status}: {error_text}"}
    except Exception as e:
        return {"error": str(e)}
