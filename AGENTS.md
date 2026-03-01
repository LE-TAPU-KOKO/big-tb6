# Repository Guidelines

## Project Structure & Module Organization
- `server/`: Python backend (Pipecat + Gemini Live). Key files: `server/bot.py` (bot logic), `server/tb_audio_tool.py` (TB cough analysis), `server/palm_anemia_tool.py` (palm anemia API), `server/tests/` (pytest).
- `client/`: Next.js frontend (`client/app/`, `client/components/`).
- `docs/`: Project docs and notes.
- Media outputs: `server/cough_samples/`, `server/palm_captures/`, `server/eye_images/`, `server/fingernail_images/`.
 - Palm analysis flow: `capture_palm_photo` is the only tool. It saves a PNG and immediately calls `analyze_palm_file()` internally, returning the analysis in the same tool response (no separate analysis tool call).
 - Eye analysis flow: `capture_eye_photo` saves a PNG and immediately calls `analyze_eye_file()` (single tool response).
 - Nail analysis flow: `capture_fingernail_photo` saves a PNG and immediately calls `analyze_nail_file()` (single tool response, API expects form field `image`).
 - Completion tracking: after a successful cough or palm/eye/nail analysis, the bot prompts the next uncompleted check only.

## Build, Test, and Development Commands
- Backend (run bot):
  - `cd server`
  - `./venv/bin/python bot.py -t webrtc --host localhost --port 7860`
- Frontend (dev server):
  - `cd client`
  - `npm run dev`
- Tests:
  - `cd server`
  - `./venv/bin/python -m pytest tests/`

## Coding Style & Naming Conventions
- Python: 4‑space indentation, PEP 8 style, keep async functions `async def` when interacting with Pipecat.
- Naming: `snake_case` for Python functions/vars; `PascalCase` for classes.
- Files: place new backend tools in `server/` (e.g., `*_tool.py`).

## Testing Guidelines
- Framework: `pytest` under `server/tests/`.
- Naming: `test_*.py` with test functions `test_*`.
- Prefer integration tests for API calls in tools; keep unit tests fast and isolated where possible.

## Commit & Pull Request Guidelines
- Commit history is minimal; use short, descriptive messages (e.g., “add palm analysis tool”).
- PRs should include:
  - A brief summary of behavior changes
  - Test commands run and results
  - Screenshots or logs for UI/voice flow changes when relevant

## Security & Configuration Tips
- Store API keys in `server/.env` (e.g., `GOOGLE_API_KEY`, `DAILY_API_KEY`).
- Do not commit secrets or generated media outputs.
