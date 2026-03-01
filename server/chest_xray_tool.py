"""Chest X-ray Tool - Analyze chest X-ray images for TB indicators."""

import os
from typing import Any, Dict

import aiohttp


XRAY_API_URL = os.getenv(
    "XRAY_API_URL",
    "https://chest-xray-1039179580375.us-central1.run.app/analyze-tb",
)


async def analyze_xray_file(file_path: str) -> Dict[str, Any]:
    """Analyze a chest X-ray image file for TB indicators.

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
        timeout = aiohttp.ClientTimeout(total=180)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            with open(file_path, "rb") as image_file:
                data = aiohttp.FormData()
                data.add_field(
                    "file",
                    image_file,
                    filename=os.path.basename(file_path),
                    content_type="image/png",
                )

                async with session.post(XRAY_API_URL, data=data) as response:
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
