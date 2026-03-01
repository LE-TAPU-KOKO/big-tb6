import os
import tempfile
import asyncio
import sys
from pathlib import Path

# Ensure server/ is on sys.path so imports work when running from server/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def run(coro):
    return asyncio.run(coro)


class FakeResponse:
    def __init__(self, status, json_data=None, text_data=""):
        self.status = status
        self._json_data = json_data
        self._text_data = text_data

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def json(self):
        if self._json_data is None:
            raise ValueError("no json")
        return self._json_data

    async def text(self):
        return self._text_data


class FakeSession:
    def __init__(self, response):
        self._response = response

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    def post(self, url, data=None):
        return self._response


def test_analyze_palm_file_missing_file(monkeypatch):
    from palm_anemia_tool import analyze_palm_file

    result = run(analyze_palm_file("/no/such/file.png"))
    assert "error" in result


def test_analyze_palm_file_success_json(monkeypatch):
    from palm_anemia_tool import analyze_palm_file
    import palm_anemia_tool

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        path = f.name

    try:
        fake = FakeResponse(status=200, json_data={"ok": True})
        monkeypatch.setattr(
            palm_anemia_tool.aiohttp,
            "ClientSession",
            lambda: FakeSession(fake),
        )
        result = run(analyze_palm_file(path))
        assert result == {"result": {"ok": True}}
    finally:
        if os.path.exists(path):
            os.remove(path)


def test_analyze_palm_file_success_text(monkeypatch):
    from palm_anemia_tool import analyze_palm_file
    import palm_anemia_tool

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        path = f.name

    try:
        fake = FakeResponse(status=200, json_data=None, text_data="ok")
        monkeypatch.setattr(
            palm_anemia_tool.aiohttp,
            "ClientSession",
            lambda: FakeSession(fake),
        )
        result = run(analyze_palm_file(path))
        assert result == {"result_text": "ok"}
    finally:
        if os.path.exists(path):
            os.remove(path)


def test_analyze_palm_file_error_status(monkeypatch):
    from palm_anemia_tool import analyze_palm_file
    import palm_anemia_tool

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        path = f.name

    try:
        fake = FakeResponse(status=400, text_data="bad request")
        monkeypatch.setattr(
            palm_anemia_tool.aiohttp,
            "ClientSession",
            lambda: FakeSession(fake),
        )
        result = run(analyze_palm_file(path))
        assert "error" in result
        assert "400" in result["error"]
    finally:
        if os.path.exists(path):
            os.remove(path)


def test_analyze_palm_file_real_image():
    """Integration test: uses any image under palm_captures/ if present."""
    import pytest
    from palm_anemia_tool import analyze_palm_file

    capture_dir = Path(__file__).resolve().parent.parent / "palm_captures"
    if not capture_dir.is_dir():
        pytest.skip("palm_captures/ directory not found.")

    images = [
        str(p)
        for p in capture_dir.iterdir()
        if p.suffix.lower() in {".png", ".jpg", ".jpeg"}
    ]
    if not images:
        pytest.skip("No images found under palm_captures/.")

    result = run(analyze_palm_file(images[0]))
    print(result)
    assert "result" in result or "result_text" in result or "error" in result
