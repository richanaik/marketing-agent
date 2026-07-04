Full-Funnel Marketing Agent
Google × Kaggle 5-Day Agentic AI Intensive — Capstone Project
ADK 2.0 + Vibe Coding | June 2026
What This Project Is
A 6-agent orchestrated system that takes a business goal end-to-end — from a
conversational intake interview through SEO/AEO/GEO strategy, Google Ads campaign
structure, Meta Ads funnel strategy, AI-generated ad copy with LLM-as-Judge scoring, and
visual creative concepts — with 3 human-in-the-loop approval checkpoints, automatic
Google Drive delivery, and Gmail confirmation.
Built for: A working digital marketer and photographer in Goa, India who currently spends
12–15 hours per client onboarding across 4 separate tools.
What it demonstrates (course concepts):
✅ Multi-agent orchestration via ADK 2.0 Workflow Runtime
✅ Vibe Coding — all agent behaviour defined in natural language (.md files)
✅ MCP (Model Context Protocol) — Drive, Gmail, Sheets, Search via config only
✅ A2A Protocol — agents publish Agent Cards, supervisor dispatches via A2A
✅ Human-in-the-Loop — 3 HITL checkpoints via ADK 
interrupt_before
✅ LLM-as-Judge — embedded evaluation in copywriter agent + standalone eval pass
✅ Trace-based metrics — 8 quantitative metrics captured from execution logs
✅ Context engineering — field-level filtering, compaction rules, session persistence
✅ Gemini Vision — portfolio photo style extraction in visual agent
✅ Gemini Imagen 3 — ad image concept generation
Project Structure
marketing_agent/
├
── agents/                          
(Vibe Coding)
│   
├
── intake_agent.md              
step interview)
│   
├
── seo_agent.md                 
internal links
│   
├
── google_ads_agent.md          
← Natural language agent persona files
← Conversational brief collection (10
← Keyword research + schema generation +
← Campaign structure + keywords + bid
strategy
│   
├
── meta_ads_agent.md            ← TOFU/MOFU/BOFU audience funnel
strategy
│   
├
── copywriter_agent.md          ← RSA + Meta copy with embedded LLM-as
Judge
│   └── visual_agent.md              ← Style extraction + Imagen prompts +
Reel scripts
│ ├
── mcp/
│   └── mcp_config.json              ← MCP server registry (Drive, Gmail,
Sheets, Search)
│ ├
── evaluation/
│   
├
── judge_rubric.md              ← LLM-as-Judge scoring criteria (15
metrics)
│   └── trace_metrics.json           ← 8 deterministic trace metrics
definitions
│ ├
── system_design/
│   
├
── architecture.md              ← Full graph topology, handoff protocol,
context rules
│   └── agent_cards.json             ← A2A capability registry for all 6
agents
│ ├
── .well-known/                     ← A2A agent card discovery endpoints
│   
├
── agent-card.json              ← Supervisor's own A2A card
│   
├
── seo_agent-card.json
│   
├
── google_ads_agent-card.json
│   
├
── meta_ads_agent-card.json
│   
├
── copywriter_agent-card.json
│   └── visual_agent-card.json
│ ├
── outputs/                         ← All generated artefacts (gitignored
except structure)
│   
├
── antigravity.json             ← Antigravity 2.0 project config
│   
├
── sessions/                    ← ADK session persistence files
│   
├
── traces/                      ← Execution trace logs (JSONL)
│   │   └── tool_calls.jsonl
│   
├
── eval/                        ← LLM Judge evaluation reports
│   │   
├
── last_run_eval.json
│   │   └── last_run_summary.md
│   └── delivery_manifest.json       ← Drive delivery confirmation
│ ├
── .env                             ← API keys (NEVER commit — in
.gitignore) ├
── .gitignore
└── README.md                        ← This file
Execution Environments — When to Use Each
This project uses three environments. Each has a specific job.
Environment
When to Use
How to Access
Google AI
Studio
Test a single agent's system instruction
before committing it to the .md file. Validate
JSON output structure. Test safety filtering.
aistudio.google.com
Antigravity
2.0 App
Run the full multi-agent pipeline end-to
end. Manage HITL checkpoints in the Agent
Manager UI. View Artifacts from each agent
run.
Desktop app
(antigravity.google/download)
Antigravity
IDE
Edit agent .md files, view and edit
mcp_config.json, inspect generated code,
read trace logs in the sidebar.
Integrated into the Antigravity
desktop app
Agents CLI
Run agents headlessly for testing, CI, or
trace capture. Log multi-agent handoffs.
Export evaluation data.
agents
 command (installed with
Antigravity)
Prerequisites & Setup
Step 1 — Required accounts and API keys
Create a 
.env
 file in the project root. Never commit this file.
bash
# .env
GEMINI_API_KEY=AIzaSy...          
GOOGLE_OAUTH_CLIENT_ID=...        
GOOGLE_OAUTH_CLIENT_SECRET=...    
# From aistudio.google.com/apikey (free)
# From console.cloud.google.com
# From console.cloud.google.com
Step 2 — Google Cloud OAuth (for Drive + Gmail MCP servers)
1. Go to console.cloud.google.com
2. Create project: "marketing-agent"
3. Enable APIs: Google Drive API, Gmail API, Google Sheets API
4. Create credentials: OAuth 2.0 Client ID → Desktop application
5. Download credentials.json → place in project root (gitignored)
6. First run opens browser for OAuth approval → token.json saved
automatically
Step 3 — Node.js (required for MCP servers)
MCP servers run via 
bash
npx 
. Install Node.js LTS from nodejs.org if not installed.
# Verify installation:
node --version    
npx --version     
# Should return v20.x or higher
# Should return 10.x or higher
Step 4 — Antigravity 2.0 Setup
1. Download from antigravity.google/download
2. Run installer (Windows: click "More info" → "Run anyway" if Defender
warns)
3. When prompted for Agent Mode → select "Review-Driven Development"
4. Sign in with your Google account
5. Install plugins when prompted: Google Drive, Gmail, Google Search
Grounding
6. Open Folder → select this marketing_agent/ directory
7. Antigravity reads antigravity.json and loads the project configuration
Step 5 — Verify MCP Connections
bash
# From Antigravity IDE terminal or any terminal in project root:
agents mcp verify --config mcp/mcp_config.json
# Expected output:
# ✅ gdrive      
# ✅ gmail       
# ✅ gsheets     
— Connected (scope: drive.file)
— Connected (scope: gmail.send)
— Connected (scope: spreadsheets)
# ✅ google-search — Connected (native grounding)
Running the Project — Agents CLI Reference
Full Pipeline Run (recommended for demo)
bash
Run Individual Agents (for testing)
Run Evaluation Pass
 
# Run the complete multi-agent pipeline from intake to delivery
agents run \
  --agent supervisor \
  --config mcp/mcp_config.json \
  --session-persist outputs/sessions/ \
  --trace-output outputs/traces/ \
  --hitl-mode interactive
# Flags explained:
# --agent supervisor       → entry point; supervisor dispatches all others
# --config                 → MCP server registry
# --session-persist        → saves state between HITL pauses (survives terminal 
# --trace-output           → writes execution trace to JSONL for eval
# --hitl-mode interactive  → HITL checkpoints pause in terminal, await your inp
 
bash
# Test intake agent only
agents run --agent intake_agent --no-persist
# Test SEO agent with pre-built IntakeBrief
agents run \
  --agent seo_agent \
  --context-inject '{"intake.brief.v1": { <your IntakeBrief JSON here> }}' \
  --trace-output outputs/traces/seo_test.jsonl
# Test copywriter agent with pre-built StrategyBundle
agents run \
  --agent copywriter_agent \
  --context-inject '{"strategy.bundle.v1": { <your StrategyBundle JSON here> }}
  --no-hitl
bash
# After a full pipeline run, evaluate all outputs
agents eval \--rubric evaluation/judge_rubric.md \--metrics evaluation/trace_metrics.json \--trace-input outputs/traces/ \--output outputs/eval/last_run_eval.json \--summary outputs/eval/last_run_summary.md
View Execution Trace (real-time)
bash
# Stream live trace during a run (separate terminal)
agents trace follow --file outputs/traces/tool_calls.jsonl
List All Registered Agents
bash
agents list --cards system_design/agent_cards.json
Antigravity 2.0 App — Conversation Entry Points
When running via the Antigravity Agent Manager UI (not CLI), use these opening
messages to trigger each phase:
# Start a full pipeline run:
"Run the intake agent using agents/intake_agent.md to collect the campaign
brief."
# Start from a specific phase (if intake already done):
"Using the intake brief in context, run the supervisor to dispatch
the strategy agents."
# Trigger evaluation after creative phase:
"Using evaluation/judge_rubric.md, evaluate all outputs from this run
and save the report to outputs/eval/"
# Trigger delivery after HITL #3 approval:
"All checkpoints are approved. Trigger the delivery pipeline to upload
all outputs to Google Drive and send the confirmation email to {user_email}."
HITL Checkpoint Reference
The pipeline pauses three times for human review. Here is what to do at each:
Checkpoint 1 — Strategy Review
Triggered after: SEO + Google Ads + Meta strategy agents complete What to review: 3
docs in Google Drive → 01_Strategy folder Your options:
bash
# In terminal (CLI mode):
approve                              
# Continue to creative phase
revise seo: focus more on Goa-specific destination wedding keywords
revise gads: add a separate ad group for commercial photography clients
revise all: the target customer framing feels too broad, tighten it
# In Antigravity UI:
# Click the Review panel → type your decision in the response box
Checkpoint 2 — Creative Review
Triggered after: Copywriter + Visual agents complete What to review: Ad copy Google
Sheet (02_Creative), Visual concepts doc Your options:
bash
approve
regenerate copy tofu               
regenerate all headlines           
regenerate visual reel_30s         
Checkpoint 3 — Final Sign-off
# Re-runs only Meta TOFU copy
# Re-runs RSA writer for all ad groups
# Re-runs only the 30s Reel script
Triggered after: LLM-as-Judge evaluation complete What to review: EvalReport in
outputs/eval/last_run_summary.md Your options:
bash
deliver                            
# Triggers MCP delivery pipeline
revise: headline char compliance is low, fix before delivery
MCP Tool Registry
All external API access goes through MCP. No agent calls APIs directly.
json
// mcp/mcp_config.json — summary
{
"gdrive":
"Create folders, upload docs, set viewer permissions",
"gmail":
"gsheets":
"Send delivery email only (gmail.send scope — cannot read i
"Create ad copy tracker and KPI sheet",
"google-search": "Web search via Gemini native grounding (keyword research, 
}

Security model:
gdrive
 scope: 
drive.file
 — can only access files this project created
gmail
 scope: 
gmail.send
 — cannot read, search, or delete emails
All tool calls logged to 
outputs/traces/tool_calls.jsonl
No write tool executes without HITL checkpoint approval (Review-Driven mode)

Agent Graph — Quick Reference
[User] → [Intake] → [Supervisor] ──parallel──→ [SEO Agent]
──parallel──→ [Google Ads Agent]  → HITL #1
──parallel──→ [Meta Ads Agent]
↓
[Supervisor] ──parallel──→ [Copywriter Agent]
──parallel──→ [Visual Agent]       
#2
#3
↓
[LLM Judge Evaluation]                           
↓
[MCP Delivery Pipeline]
(Drive upload + Gmail send)
→ HITL
→ HITL
Context Store Keys — Complete Reference
All inter-agent data flows through the ADK 2.0 Context Store. Never pass data directly
between agent functions — use these keys.
Context Key
Written by
Read by
Description
intake.brief.v1
intake_agent
supervisor, all
strategy agents
Complete
IntakeBrief
JSON
supervisor.task_manifest.v1 
supervisor
Workflow Runtime
Dispatch
instructions per
agent
seo.strategy.v1
seo_agent
supervisor,
copywriter_agent
Keyword report
+ schemas +
linking map
gads.strategy.v1
google_ads_agent supervisor,
copywriter_agent
Full campaign
structure
meta.strategy.v1
meta_ads_agent
supervisor,
copywriter_agent,
visual_agent
Audience funnel
strategy
strategy.bundle.v1
supervisor
copywriter_agent,
visual_agent
Merged strategy
outputs
copy.variants.v1
copywriter_agent supervisor, llm_judge All copy with
judge scores
visual.concepts.v1
visual_agent
supervisor, llm_judge
Style profile +
prompts +
scripts
creative.bundle.v1
supervisor
llm_judge
Merged creative
outputs
eval.report.v1
llm_judge
supervisor
Evaluation
scores + trace
metrics
delivery.complete.v1
delivery phase
—
Delivery
manifest with
Drive URLs
Evaluation Summary
Two-layer evaluation model. Both layers required for capstone submission.
Layer 1 — LLM-as-Judge (probabilistic quality):
Rubric: 
evaluation/judge_rubric.md
15 scored criteria across 5 output categories
Scored 1–10 per criterion by Gemini 2.0 Pro
Overall score = weighted average
Output: 
outputs/eval/last_run_eval.json
Layer 2 — Trace Metrics (deterministic):
8 hard metrics: latency, tool success rate, HITL count, parallel time, JSON parse rate,
schema validation rate, char limit compliance, Drive success
Captured from 
outputs/traces/
Output: appended to 
outputs/eval/last_run_eval.json
Capstone Submission Requirements
Deadline: July 6, 2026 — 11:59 PM Pacific Time
Deliverable
Where
Status
Kaggle notebook writeup
kaggle.com competition page
[ ]
Video explanation (2–3 min)
Linked in Kaggle writeup
[ ]
GitHub repo (public)
Linked in Kaggle writeup
[ ]
LLM Judge eval scores
outputs/eval/last_run_eval.json
[ ]
Live demo evidence (screenshots)
Kaggle notebook
[ ]
Video requirements:
Duration: 2–3 minutes
Must show: live run from intake conversation to Gmail delivery
Must explain: what makes the system agentic (not just a wrapper)
Tool: Loom (free, loom.com) or OBS Studio (free, obsproject.com)
Host: YouTube (unlisted) or Loom link — paste into Kaggle submission
.gitignore Reference
# Secrets
.env
credentials.json
token.json
gmail_token.json
# Runtime artefacts
outputs/sessions/
outputs/traces/
venv/
__pycache__/
*.pyc
node_modules/
# Temp files
temp/
.DS_Store
*.log
Architecture Reference
Full system design: 
system_design/architecture.md
 Agent capability registry:
system_design/agent_cards.json
 Evaluation rubric: 
metric definitions: 
evaluation/trace_metrics.json
evaluation/judge_rubric.md
 Trace
README.md — v1.0 | Full-Funnel Marketing Agent | Google-Kaggle AI Agents Intensive
2026