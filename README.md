# BigTB6

BigTB6 is a multimodal, voice-driven preliminary tuberculosis screening system. It integrates cough audio analysis, palm/eye/nail imagery, real-time respiratory rate monitoring, and chest X-ray analysis into a unified diagnostic interface.

## The Problem

**India** faces 2.7 million TB cases annually 25% of the global burden with 305,000 deaths per year. Traditional screening creates deadly delays: overcrowded hospitals, 48–72 hour lab results, and patients lost to follow-up before a diagnosis is ever reached.

## Our Solution

BigTB6 provides instant, non-contact preliminary screening at the point of care. By combining multiple passive biomarkers into a single voice-guided session, it enables hospitals to screen 3–5x more patients daily while reducing direct exposure risk for healthcare workers.

**Deployed Link:** https://big-tb6.vercel.app/
---
**Demo video:** https://youtu.be/ubBDRxCwaeE
---
## Architecture
![BigTB6 Architecture](./bigtb-archi.png)

BigTb6 is structured across four layers:

1. **Interaction Layer — Gemini Live & GetStream**: Handles all real-time voice and video communication with the user over WebRTC via GetStream's SFU. It uses the `vision-agents` framework to natively route audio/video frames into Gemini Live, dynamically invoking appropriate screening tools using function calling based on the conversation context.

2. **Orchestration Layer — MedGemma**: Acts as the clinical reasoning core. Once all modality-specific models return their results, MedGemma aggregates the outputs, interprets them in context, and generates a consolidated preliminary diagnostic report.

3. **Specialist Model Layer**: A set of independently fine-tuned models, each responsible for a single screening modality (see table below). They are invoked by the orchestrator as needed.

4. **Output Layer**: The final report is synthesized by MedGemma and delivered back to the user through Gemini Live as a voice response via the GetStream connection.

## Features

- **Voice Conversation** — Real-time microphone-based interaction via WebRTC streaming
- **Cough Analysis** — Record cough audio and receive TB probability scoring
- **Chest X-ray Analysis** — Upload X-ray images for TB screening
- **Palm Analysis** — Capture palm image for anemia screening
- **Eye Analysis** — Capture lower-eyelid image for anemia screening
- **Fingernail Analysis** — Capture fingernail image for anemia screening
- **Respiratory Rate Monitor** — Real-time respiratory rate estimation via webcam
- **Report Generation** — Consolidated diagnostic report synthesized from all modality results
- **Tool Integration** — Gemini Live function calling for multimodal tool orchestration

---

## Models

| Modality | Repository | Weights |
|---|---|---|
| Cough Analysis | [Hear-Cough-Finetuning](https://github.com/SACHokstack/Hear--Cough-Finetuning) | [sach3v/Domain_aware_dual_head_HEar](https://huggingface.co/sach3v/Domain_aware_dual_head_HEar) |
| Palm Anemia Detection | [palm-medsiglip](https://github.com/Sidharth1743/palm-medsiglip) | [Sidharth1743/palm-medsiglip-linear-probe](https://huggingface.co/Sidharth1743/palm-medsiglip-linear-probe) |
| Eye Anemia Detection | [medgemma-tb](https://github.com/Sidharth1743/medgemma-tb) | [Sidharth1743/eye-medsiglip-linear-probe](https://huggingface.co/Sidharth1743/eye-medsiglip-linear-probe) |
| Fingernail Anemia Detection | [nail-anemia-detection](https://github.com/LE-TAPU-KOKO/nail-anemia-detection) | [JetX-GT/nail-anemia-detector](https://huggingface.co/JetX-GT/nail-anemia-detector) |
| Chest X-ray Analysis | [CHRX-MLP-LINEAR_PROBE](https://github.com/LE-TAPU-KOKO/CHRX-MLP-LINEAR_PROBE) | [JetX-GT/hades-hellix-tb-linear-probe](https://huggingface.co/JetX-GT/hades-hellix-tb-linear-probe) |
| Respiratory Rate Monitor | [HR-RR-detector](https://github.com/Sidharth1743/HR-RR-detector) | — |

## Deployment

### Web Application

| Component | Platform | URL |
|---|---|---|
| Frontend (Next.js) | Vercel | https://big-tb6.vercel.app/ |
| Backend API (`medbrain-api`) | Google Cloud Run | https://medbrain-api-1039179580375.us-central1.run.app |
| Bot Service (`medbrain-bot`) | Google Cloud Run | https://medbrain-bot-1039179580375.us-central1.run.app |

### Specialist Model APIs (Google Cloud Run)

All specialist models are containerized and deployed on Google Cloud Run for scalable, unauthenticated access. Each service exposes a REST endpoint consumed by the MedGemma orchestrator.

| Service | Endpoint | Method | Route |
|---|---|---|---|
| Cough Analysis (HeAR TB) | `https://hear-tb-1039179580375.us-central1.run.app` | POST | `/predict` |
| Chest X-ray (Hades Hellix) | `https://chest-xray-1039179580375.us-central1.run.app` | POST | `/analyze-tb` |
| Palm Anemia | `https://palm-anemia-1039179580375.us-central1.run.app` | POST | `/predict` |
| Nail Anemia | `https://nail-anemia-1039179580375.us-central1.run.app` | POST | `/predict` |
| Respiratory Rate (Respira-Sense) | `https://respira-medsiglip-1039179580375.us-central1.run.app` | POST | `/predict` |


## Prerequisites

- Python 3.12+ (Requires **WSL/Ubuntu** if running on Windows for WebRTC DTLS compatibility)
- Node.js 18+
- Google API Key (for Gemini Live)
- GetStream API Key & Secret (for WebRTC Infrastructure)

## Setup

### 1. Clone and Install Dependencies

```bash
# Clone the repository
git clone <repository-url>
cd GEMINI_LIVE

# Setup backend virtual environment
cd server
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Setup frontend
cd ../client
npm install
```

### 2. Configure API Keys

Create a `.env` file in the `server` directory:

```bash
# server/.env
GOOGLE_API_KEY=your_google_api_key_here
STREAM_API_KEY=your_stream_api_key_here
STREAM_API_SECRET=your_stream_api_secret_here
```

**Getting API Keys:**
- **Google API Key**: Get from [Google AI Studio](https://aistudio.google.com/app/apikey)
- **GetStream API Keys**: Get from [Stream Dashboard](https://getstream.io/dashboard/)

## Running the Application

### For Windows Users (Automated)

We have provided a unified script that handles backend WSL spawning and frontend starting automatically:
```powershell
.\run_locally.ps1
```

### Manual Startup (Linux/WSL)

#### Terminal 1 - Backend API & Bot Orchestrator
```bash
cd server
source ~/med-venv/bin/activate # Use your venv path
python main.py
```
*(Note: The bot is dynamically spawned by the backend when a user connects from the frontend).*

#### Terminal 2 - Frontend
```bash
cd client
npm run dev
```

### Access the Application

1. Open http://localhost:3000 in your browser
2. Grant microphone and camera permissions
3. Click "Start Visit"
4. Wait for the Bot to spawn and natively join the Stream Video call! You can now talk to BigTBAI clearly and seamlessly. Use the provided tools and UI to begin diagnostic checks.

## How It Works

### Conversation Flow

1. **Greeting**: BigTB6 introduces itself and asks how you're feeling
2. **Symptom Inquiry**: Ask questions about TB-related symptoms
3. **Cough Analysis**: When you mention a cough, the bot records and analyzes the cough audio
4. **Palm/Eye/Nail Analysis**: When you mention these concerns, the bot captures an image and returns an analysis in the same tool call
5. **Chest X‑ray Analysis**: After uploading an X‑ray, ask the bot to analyze the chest X‑ray

### Tools

| Tool | Description |
|------|-------------|
| `record_cough_sound` | Records user's cough audio |
| `analyze_cough_for_tb` | Analyzes recorded cough for TB probability |
| `capture_palm_photo` | Captures palm image and returns analysis |
| `capture_eye_photo` | Captures eye image and returns analysis |
| `capture_fingernail_photo` | Captures fingernail image and returns analysis |
| `analyze_chest_xray` | Analyzes most recently uploaded chest X‑ray |

### Backend Architecture

```
┌─────────────┐     WebRTC      ┌─────────────┐
│   Client    │ ◄──────────────► │   Backend   │
│  (Browser)  │                 │ (Python)    │
└─────────────┘                 └─────────────┘
                                        │
                                        ▼
                               ┌─────────────┐
                               │ Gemini Live │
                               │    API      │
                               └─────────────┘
                                        │
                                        ▼
                               ┌─────────────┐
                               │  TB Audio   │
                               │  Analysis   │
                               │    API      │
                               └─────────────┘
```

## Project Structure

```
GEMINI_LIVE/
├── client/                 # Next.js frontend with Stream Video SDK
│   ├── app/              # Next.js app directory
│   ├── components/        # React components
│   └── package.json      # Frontend dependencies
├── server/                # Python backend
│   ├── bot.py            # Main bot built with Vision-Agents
│   ├── tb_audio_tool.py  # TB cough analysis API
│   ├── palm_anemia_tool.py  # Palm anemia API
│   ├── eye_anemia_tool.py   # Eye anemia API
│   ├── nail_anemia_tool.py  # Nail anemia API
│   ├── chest_xray_tool.py   # Chest X‑ray TB API
│   ├── xray_store.py     # Latest X‑ray path store
│   ├── main.py           # FastAPI server (upload + bot spawner)
│   ├── requirements.txt  # Python dependencies
│   └── venv/             # Virtual environment
```

### Customizing the Bot

Edit `server/bot.py` to:
- Change the `BigTBAI` system prompt/behavior
- Add new clinical tools to the Gemini Live configuration
- Modify Stream video connection logic

## License

MIT License

## Credits

- [Vision-Agents](https://github.com/landing-ai/vision-agents) - Framework for building vision-capable agents
- [Google Gemini Live API](https://ai.google.dev/gemini-api/docs/live) - Multimodal live AI
- [GetStream Video](https://getstream.io/video/) - Global scalable WebRTC infrastructure
