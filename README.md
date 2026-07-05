# Full-Funnel Marketing Agent

A 6-agent AI system that takes a marketing brief through SEO strategy, Google Ads, Meta Ads, ad copywriting, and visual creative generation — with 3 human-in-the-loop checkpoints and automatic delivery to Google Drive and Gmail.

Built for the **Google × Kaggle 5-Day AI Agents Intensive** — Agents for Business track.

What normally takes 12–15 hours of manual work across 4 separate tools now runs in under 10 minutes.

---

## Architecture

Six agents, each defined as a natural language Markdown file (Vibe Coding paradigm) — no Python agent logic, just structured prompts:

| Agent | File | Role |
|---|---|---|
| Intake | `agents/intake_agent.md` | Collects the client brief |
| SEO | `agents/seo_agent.md` | Keyword strategy, schema markup, AEO |
| Google Ads | `agents/google_ads_agent.md` | Campaign structure, RSA copy stubs |
| Meta Ads | `agents/meta_ads_agent.md` | Full-funnel Meta strategy |
| Copywriter | `agents/copywriter_agent.md` | Google + Meta ad copy |
| Visual | `agents/visual_agent.md` | Visual creative briefs |
| LLM Judge | `evaluation/judge_rubric.md` | Scores the full output, 38-point rubric |

A Python Flask backend orchestrates the pipeline. Three HITL checkpoints pause the pipeline for human approval between stages. A custom local MCP server (FastMCP) handles final delivery to Google Drive and Gmail.

```
Intake → [SEO + Google Ads + Meta Ads] → HITL 1
       → [Copywriter + Visual] → HITL 2
       → LLM Judge → HITL 3
       → Drive Upload + Email Delivery
```

Every agent call runs through an automatic model fallback chain — if one Gemini model hits a quota limit, it transparently retries the next model in the list (`gemini-2.5-flash-lite` → `gemini-2.0-flash-lite` → `gemini-2.0-flash` → `gemini-2.5-flash`) without failing the pipeline.

---

## Project Structure

```
marketing_agent/
├── agents/                  # 6 agent definitions (Markdown)
├── backend/
│   └── server.py            # Flask API — orchestrates the pipeline
├── delivery/
│   └── deliver_mcp.py       # Local MCP server — Drive + Gmail delivery
├── evaluation/
│   ├── judge_rubric.md      # LLM-as-Judge scoring criteria
│   └── trace_metrics.json   # Trace/logging schema
├── frontend/                # Web UI — intake form, live dashboard, HITL screens
├── mcp/
│   └── mcp_config.json      # MCP server config
├── system_design/           # Architecture docs, agent cards
├── .well-known/             # A2A agent cards (6 files)
├── outputs/                 # Generated session outputs (gitignored)
├── .env.example             # Environment variable template
├── .gitignore
└── requirements.txt
```

---

## Setup

**1. Clone the repository**
```bash
git clone https://github.com/YOURUSERNAME/marketing-agent.git
cd marketing-agent
```

**2. Create a virtual environment and install dependencies**
```bash
python -m venv venv2
venv2\Scripts\activate
pip install flask flask-cors google-generativeai python-dotenv mcp google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

**3. Set up environment variables**

Copy `.env.example` to `.env` and add your real Gemini API key:
```
GEMINI_API_KEY=your_gemini_api_key_here
DEFAULT_MODEL=gemini-2.5-flash-lite
PRO_MODEL=gemini-2.5-pro
```

**4. Set up Google OAuth (for Drive + Gmail delivery)**

- Go to Google Cloud Console → create a project
- Enable **Google Drive API** and **Gmail API**
- Create OAuth 2.0 credentials (Desktop app type) → download as `credentials.json` → place in project root
- Add your email as a **Test User** under OAuth consent screen
- Required scopes: `drive.file`, `gmail.send`

---

## Running the System

This project runs as **three separate processes**, each in its own terminal tab.

**Terminal 1 — Backend (agent pipeline)**
```bash
venv2\Scripts\activate
python backend/server.py
```
Runs on `http://localhost:8080`

**Terminal 2 — Frontend (UI)**
```bash
cd frontend
npx serve .
```
Runs on `http://localhost:3000`

**Terminal 3 — Delivery MCP server**
```bash
venv2\Scripts\activate
python delivery/deliver_mcp.py
```

Open `http://localhost:3000` in your browser, fill in the intake form, and submit. The pipeline runs through 3 HITL checkpoints — approve each to proceed. On completion you'll see the final evaluation score and deliverables summary.

**Delivering to Drive + Gmail** (after a session completes):
```bash
python -c "from delivery.deliver_mcp import upload_session_to_drive; print(upload_session_to_drive('YOUR_SESSION_ID'))"
python -c "from delivery.deliver_mcp import email_session_summary; print(email_session_summary('YOUR_SESSION_ID', 'client@email.com'))"
```
The session ID is shown in the browser (Network tab → `run` request → Response) or as the folder name under `outputs/`.

First run of either delivery command opens a browser for Google OAuth consent — subsequent runs use the cached `token.json` silently.

---

## Evaluation

Every completed session is scored by the LLM Judge against a 38-point rubric (`evaluation/judge_rubric.md`) — 15 quality criteria (business fidelity, strategic quality, creative quality) plus 8 hard constraint checks (character limits, schema validity, output completeness). Scores of 32+ auto-recommend delivery.

---

## License

Built as a capstone project for the Google × Kaggle 5-Day AI Agents Intensive. Not licensed for commercial redistribution.
