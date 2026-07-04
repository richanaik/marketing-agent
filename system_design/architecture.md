# system_design/architecture.md
# Full-Funnel Marketing Agent — System Architecture
# Google-Kaggle 5-Day Agentic AI Capstone | ADK 2.0 + Vibe Coding
# Author: [Your Name] | Date: June 2026
# Status: PRODUCTION-GRADE v1.0

---

## 0. Document Purpose & Execution Environments

This file is the single source of truth for the system architecture of the
Full-Funnel Marketing Agent. It must be read by every contributor, every agent
persona file (.md), and must be referenced explicitly in the Kaggle notebook
writeup under the "System Design" section.

### Execution Environments (ADK 2.0 Lifecycle)

This project operates across three distinct environments. Each has a specific role:

| Environment | Role | When to Use |
|---|---|---|
| **Google AI Studio** | Rapid prompt prototyping, safety filter testing, system instruction hardening, one-shot output validation | Validating each agent's system instruction before committing to .md file |
| **Antigravity 2.0 App** | Headless, conversation-driven orchestration; reads `.code-workspace`; runs the Workflow Runtime; manages HITL checkpoints | Primary runtime for executing the full multi-agent pipeline end-to-end |
| **Antigravity IDE** | Code-visible file tracking, MCP server config editing, agent .md editing, trace log inspection | Editing agent personas, debugging MCP connections, reading Artifacts |
| **Agents CLI** | Execution runtime, structured logging, multi-agent handoff tracking, evaluation trace capture | Running agents from terminal, CI/CD integration, generating trace exports |

### CLI Entry Point (after setup)
```bash
# From project root:
agents run --agent supervisor --config mcp/mcp_config.json --trace-output outputs/traces/
```

---

## 1. Problem Statement

**The problem:** A digital marketing practitioner (photographer + marketer based in Goa, India)
currently spends 12–15 hours across 4 separate tools to produce a complete marketing
campaign package for a new client: keyword research, schema markup, Google Ads structure,
Meta Ads funnel, ad copywriting, visual creative briefs, and final delivery.

**The solution:** A 6-agent orchestrated system that completes this entire workflow
autonomously in under 10 minutes, pausing at 3 human-approval checkpoints, and
delivering all outputs to Google Drive with a Gmail confirmation link.

**What makes it agentic (not just a wrapper):**
1. Agents reason, plan, and act across multiple steps (ReAct loop)
2. Agents use real external tools via MCP (Drive, Gmail, Search, Sheets)
3. Agents communicate via A2A protocol with published Agent Cards
4. The system modifies its behaviour based on human feedback at HITL checkpoints
5. The system evaluates its own outputs using LLM-as-Judge (self-evaluation loop)
6. All execution is traced and logged for probabilistic quality assessment

---

## 2. Graph Topology — ADK 2.0 Workflow Runtime

ADK 2.0 uses a **graph-based execution engine** (not a sequential script).
Each agent is a node. Edges represent data handoffs. The graph supports
parallel execution of independent nodes and conditional branching.

```
GRAPH TOPOLOGY:

 ┌─────────────────────────────────────────────────────────────────┐
 │                     WORKFLOW RUNTIME (ADK 2.0)                  │
 │                                                                  │
 │  [USER INPUT]                                                    │
 │       │                                                          │
 │       ▼                                                          │
 │  ┌────────────┐                                                  │
 │  │   INTAKE   │  ← Conversational brief collection              │
 │  │   AGENT    │    Outputs: IntakeBrief JSON                     │
 │  └─────┬──────┘                                                  │
 │        │ IntakeBrief                                             │
 │        ▼                                                         │
 │  ┌────────────┐                                                  │
 │  │ SUPERVISOR │  ← Validates, decomposes, dispatches            │
 │  │   AGENT    │    A2A delegation to 3 parallel nodes            │
 │  └──┬──┬──┬───┘                                                  │
 │     │  │  │  A2A Parallel Dispatch                               │
 │     │  │  │                                                      │
 │  ┌──▼─┐┌─▼──┐┌──▼──┐                                            │
 │  │SEO ││GADS││META │  ← Run simultaneously (parallel nodes)     │
 │  │AGNT││AGNT││AGNT │    Each writes to shared Context Store      │
 │  └──┬─┘└─┬──┘└──┬──┘                                            │
 │     │    │      │  Merge: StrategyBundle                         │
 │     └────┴──────┘                                                │
 │              │                                                   │
 │              ▼                                                   │
 │     ┌─────────────────┐                                          │
 │     │  HITL CHECKPOINT│  ◄── Human reviews StrategyBundle       │
 │     │       #1        │       Approves OR requests revision      │
 │     └────────┬────────┘                                          │
 │              │ [APPROVED]                                        │
 │              ▼                                                   │
 │     ┌────────┴────────┐                                          │
 │     │                 │  A2A Parallel Dispatch                   │
 │  ┌──▼────┐    ┌───────▼──┐                                       │
 │  │ COPY  │    │  VISUAL  │  ← Run simultaneously                │
 │  │ AGENT │    │  AGENT   │    Both read StrategyBundle           │
 │  └──┬────┘    └────┬─────┘                                       │
 │     │              │  Merge: CreativeBundle                      │
 │     └──────────────┘                                             │
 │              │                                                   │
 │              ▼                                                   │
 │     ┌─────────────────┐                                          │
 │     │  HITL CHECKPOINT│  ◄── Human reviews CreativeBundle       │
 │     │       #2        │       Selects variants, leaves notes     │
 │     └────────┬────────┘                                          │
 │              │ [APPROVED]                                        │
 │              ▼                                                   │
 │     ┌─────────────────┐                                          │
 │     │  LLM-AS-JUDGE   │  ← Evaluates all outputs                │
 │     │  EVALUATION     │    Produces EvalReport JSON              │
 │     └────────┬────────┘                                          │
 │              │                                                   │
 │              ▼                                                   │
 │     ┌─────────────────┐                                          │
 │     │  HITL CHECKPOINT│  ◄── Human final sign-off               │
 │     │       #3        │       Triggers delivery pipeline         │
 │     └────────┬────────┘                                          │
 │              │ [APPROVED]                                        │
 │              ▼                                                   │
 │     ┌─────────────────┐                                          │
 │     │  DELIVERY PHASE │  ← Drive folder creation + upload       │
 │     │  (MCP tools)    │    Gmail delivery email                  │
 │     └────────┬────────┘                                          │
 │              │                                                   │
 │              ▼                                                   │
 │         [COMPLETE]                                               │
 │                                                                  │
 └─────────────────────────────────────────────────────────────────┘
```

### Node Execution Types

| Node | Type | Execution Model |
|---|---|---|
| intake_agent | Sequential | Conversational loop until IntakeBrief complete |
| supervisor | Sequential | Validates + dispatches; waits for all children |
| seo_agent | Parallel | Fires simultaneously with gads + meta |
| google_ads_agent | Parallel | Fires simultaneously with seo + meta |
| meta_ads_agent | Parallel | Fires simultaneously with seo + gads |
| copywriter_agent | Parallel | Fires simultaneously with visual |
| visual_agent | Parallel | Fires simultaneously with copywriter |
| llm_judge | Sequential | Runs after all creative outputs merged |

---

## 3. Sequential Handoff Protocol

### 3.1 Handoff 1: User → Intake Agent
- **Trigger:** User types first message in Antigravity conversation
- **Input:** Free-form natural language (no schema required)
- **Process:** Intake agent conducts structured 10-step conversational interview
- **Output:** `IntakeBrief` JSON object (see Schema 3.4)
- **Handoff method:** Intake agent writes IntakeBrief to Context Store
  ```
  CONTEXT_KEY: "intake.brief.v1"
  ```

### 3.2 Handoff 2: Intake → Supervisor (Validation Gate)
- **Trigger:** IntakeBrief written to Context Store
- **Input:** `intake.brief.v1` from Context Store
- **Process:** Supervisor validates all 12 required fields, checks for empty arrays,
  validates URL format, confirms email format, confirms budget is numeric
- **On validation failure:** Supervisor sends targeted follow-up question to user
  (not a full restart — only the specific failing fields)
- **On validation success:** Supervisor builds TaskManifest and dispatches via A2A
- **Output:** `TaskManifest` written to Context Store
  ```
  CONTEXT_KEY: "supervisor.task_manifest.v1"
  ```

### 3.3 Handoff 3: Supervisor → Strategy Agents (Parallel A2A)
- **Trigger:** TaskManifest written to Context Store
- **Input:** Each agent receives a filtered view of IntakeBrief (only the fields it needs)
- **Process:** Three agents execute simultaneously:
  - `seo_agent` receives: business_name, services, service_areas, page_urls, competitors
  - `google_ads_agent` receives: business_name, services, service_areas, target_customer,
    budget, campaign_goal, competitors
  - `meta_ads_agent` receives: target_customer, service_areas, budget, unique_value_props,
    campaign_goal
- **Output:** Each agent writes to its own Context Store key:
  ```
  CONTEXT_KEY: "seo.strategy.v1"
  CONTEXT_KEY: "gads.strategy.v1"
  CONTEXT_KEY: "meta.strategy.v1"
  ```
- **Merge:** Supervisor collects all three on completion, produces `StrategyBundle`
  ```
  CONTEXT_KEY: "strategy.bundle.v1"
  ```

### 3.4 Handoff 4: HITL Checkpoint #1 → Creative Phase
- **Trigger:** `strategy.bundle.v1` complete
- **ADK Mechanism:** `interrupt_before` gate on creative phase nodes
- **Human Action:** Review 3 strategy docs in Drive (01_Strategy folder)
- **User responses accepted:**
  - `"approve"` → system resumes, dispatches creative agents
  - `"revise seo: [feedback]"` → only seo_agent re-runs with feedback in context
  - `"revise all: [feedback]"` → all three strategy agents re-run with feedback
- **Timeout:** 24 hours (system holds state via ADK session persistence)

### 3.5 Handoff 5: Strategy Bundle → Creative Agents (Parallel A2A)
- **Trigger:** HITL #1 approved
- **Input:** `strategy.bundle.v1` + `intake.brief.v1` (both in Context Store)
- **Process:** Two agents execute simultaneously:
  - `copywriter_agent` reads: google ads plan, meta funnel plan, UVPs, target customer
  - `visual_agent` reads: intake portfolio images, target customer, style preferences
- **Output:**
  ```
  CONTEXT_KEY: "copy.variants.v1"
  CONTEXT_KEY: "visual.concepts.v1"
  ```
- **Merge:** `CreativeBundle`
  ```
  CONTEXT_KEY: "creative.bundle.v1"
  ```

### 3.6 Handoff 6: HITL Checkpoint #2 → Evaluation
- **Trigger:** `creative.bundle.v1` complete
- **Human Action:** Review ad copy sheet and visual concepts in Drive (02_Creative)
- **User responses accepted:**
  - `"approve"` → trigger LLM judge
  - `"regenerate copy tofu"` → only Meta TOFU copy regenerates
  - `"regenerate all headlines"` → RSA writer re-runs for all ad groups

### 3.7 Handoff 7: LLM-as-Judge Evaluation
- **Trigger:** HITL #2 approved
- **Input:** All Context Store keys (full bundle)
- **Process:** Judge reads `evaluation/judge_rubric.md`, scores every output category
- **Output:**
  ```
  CONTEXT_KEY: "eval.report.v1"
  FILE: outputs/eval/last_run_eval.json
  FILE: outputs/eval/last_run_summary.md
  ```

### 3.8 Handoff 8: HITL Checkpoint #3 → Delivery
- **Trigger:** `eval.report.v1` complete
- **Human sees:** Eval scores, overall rating, top issues flagged
- **User responses accepted:**
  - `"deliver"` → triggers MCP delivery pipeline
  - `"revise: [specific issue]"` → targeted re-run of flagged agent

### 3.9 Handoff 9: Delivery Phase (MCP Pipeline)
- **Trigger:** HITL #3 approved
- **Process (sequential within delivery):**
  1. `gdrive_mcp`: Create project folder `{project_name}/`
  2. `gdrive_mcp`: Create subfolders `01_Strategy/`, `02_Creative/`, `02_Creative/Images/`, `03_Final_Deliverable/`
  3. `gdrive_mcp`: Upload all strategy docs to `01_Strategy/`
  4. `gdrive_mcp`: Upload copy sheet (.gsheet) and visual concepts to `02_Creative/`
  5. `gdrive_mcp`: Upload 30-day calendar and KPI tracker to `03_Final_Deliverable/`
  6. `gmail_mcp`: Send delivery email with Drive folder link to `user_email`
- **Output:**
  ```
  CONTEXT_KEY: "delivery.complete.v1"
  FILE: outputs/delivery_manifest.json
  ```

---

## 4. Context Engineering & Compaction Rules

### 4.1 Context Window Budget
Each agent operates within a **128k token context window** (Gemini 2.0 Flash).
However, passing all data to all agents wastes tokens and risks context overflow.
The following compaction rules apply:

### 4.2 Field-Level Context Filtering (Principle of Minimum Context)
Each agent receives ONLY the fields it needs. The supervisor enforces this.

```
intake_agent:      receives nothing from context (starts fresh)
supervisor:        receives full IntakeBrief (12 fields)
seo_agent:         receives 6 fields (business_name, services, service_areas,
                   page_urls, competitors, target_customer)
google_ads_agent:  receives 7 fields (business_name, services, service_areas,
                   target_customer, budget, campaign_goal, competitors)
meta_ads_agent:    receives 6 fields (target_customer, service_areas, budget,
                   unique_value_props, campaign_goal, services)
copywriter_agent:  receives StrategyBundle + 4 intake fields
                   (services, unique_value_props, target_customer, business_name)
visual_agent:      receives 4 intake fields + meta funnel stage formats
llm_judge:         receives ALL Context Store keys (full evaluation pass)
```

### 4.3 Context Compaction Rules (Large Outputs)
When an agent produces output exceeding 8,000 tokens:
1. The full output is written to `outputs/raw/` as a JSON file
2. A **compressed summary** (max 2,000 tokens) is written to Context Store
3. The summary contains: key findings, top metrics, and file path reference
4. Downstream agents receive the summary; humans receive the full file

### 4.4 Output Schema Enforcement
All agent outputs MUST conform to their schema (defined in agent_cards.json).
Schema validation runs automatically before any output enters Context Store.
On schema mismatch: agent retries once with the validation error appended.
On second failure: supervisor flags the error, continues with partial bundle.

### 4.5 Session Persistence
ADK 2.0 session state is persisted between HITL pauses using the built-in
`InMemorySessionService` during single sessions, and `PersistentSessionService`
(writes to `outputs/sessions/`) for multi-day continuations.

```python
# ADK 2.0 session config (referenced by Antigravity runtime)
session_config = {
    "service": "persistent",
    "storage_path": "./outputs/sessions/",
    "session_ttl_hours": 72
}
```

---

## 5. MCP Tool Registry

All external tool access is mediated via MCP. No agent calls external APIs directly.

| Tool Name | MCP Server | Scope | Used By |
|---|---|---|---|
| `google_search` | Native Gemini grounding | Read-only web search | seo_agent, gads_agent, meta_agent |
| `gdrive_create_folder` | @mcp/server-gdrive | Write: create folders | delivery phase |
| `gdrive_upload_doc` | @mcp/server-gdrive | Write: upload as GDoc | delivery phase |
| `gdrive_upload_sheet` | @mcp/server-gdrive | Write: upload as GSheet | delivery phase |
| `gdrive_set_permission` | @mcp/server-gdrive | Write: set viewer link | delivery phase |
| `gmail_send` | @mcp/server-gmail | Write: send email only | delivery phase |
| `gsheets_create` | @mcp/server-gsheets | Write: create sheet | copywriter_agent |
| `imagen_generate` | @mcp/genmedia-mcp | Write: generate images | visual_agent |

### MCP Security Model
- All MCP servers operate with **minimum scope**
- `gdrive` scope: `drive.file` only (cannot access pre-existing files)
- `gmail` scope: `gmail.send` only (cannot read inbox)
- Tool calls are logged to `outputs/traces/tool_calls.jsonl`
- HITL checkpoint required before any write tool executes (enforced by Antigravity)

---

## 6. A2A Protocol — Agent Cards & Discovery

Each agent publishes its capabilities via an Agent Card at a well-known path.
The supervisor reads all Agent Cards at startup to build its dispatch manifest.

### Agent Card Location
```
marketing_agent/.well-known/
├── agent-card.json              ← Supervisor's own card
├── seo_agent-card.json
├── google_ads_agent-card.json
├── meta_ads_agent-card.json
├── copywriter_agent-card.json
└── visual_agent-card.json
```

### A2A Message Format (between supervisor and subagents)
```json
{
  "a2a_version": "1.0",
  "from": "supervisor",
  "to": "seo_agent",
  "task_id": "task_seo_001",
  "message_type": "task_dispatch",
  "payload": {
    "context_keys": ["intake.brief.v1"],
    "filtered_fields": ["business_name", "services", "service_areas", "page_urls", "competitors"],
    "output_key": "seo.strategy.v1",
    "deadline_seconds": 120,
    "retry_policy": { "max_retries": 1, "on_failure": "partial_continue" }
  }
}
```

---

## 7. HITL Checkpoint Specification

### Checkpoint Architecture
All three checkpoints use ADK 2.0's `interrupt_before` mechanism.
In Antigravity 2.0, HITL checkpoints surface as review panels in the Agent Manager UI.

```
CHECKPOINT SCHEMA:
{
  "checkpoint_id":   "hitl_1" | "hitl_2" | "hitl_3",
  "triggered_after": "strategy_merge" | "creative_merge" | "eval_complete",
  "blocks":          ["copywriter_agent", "visual_agent"] | ["delivery_phase"] | ["delivery_phase"],
  "expires_hours":   24,
  "user_commands":   ["approve", "revise {agent}: {feedback}", "revise all: {feedback}"],
  "on_timeout":      "notify_user_and_hold"
}
```

### What the Human Reviews at Each Checkpoint

**Checkpoint 1 (Strategy Review):**
- SEO Strategy Report (keywords, AEO gaps, schema plan)
- Google Ads Campaign Structure (ad groups, keywords, bids)
- Meta Ads Funnel Strategy (TOFU/MOFU/BOFU audiences)
- Cross-channel consistency warning (if detected by supervisor)

**Checkpoint 2 (Creative Review):**
- Ad copy Google Sheet (all RSA headlines with scores, Meta copy per stage)
- Visual concepts doc (Imagen prompts, Reel scripts)
- LLM judge pre-scores on copy compliance

**Checkpoint 3 (Final Sign-off):**
- Complete LLM-as-Judge evaluation report
- Overall score + per-category breakdown
- List of Drive files to be delivered
- Preview of delivery email

---

## 8. Evaluation Architecture (LLM-as-Judge + Trace Metrics)

### 8.1 Two-Layer Evaluation Model

**Layer 1 — Probabilistic Quality (LLM-as-Judge):**
- A dedicated Gemini 2.0 Pro call evaluates all agent outputs
- Uses rubric defined in `evaluation/judge_rubric.md`
- Outputs structured scores per category (1–10 scale)
- Required for capstone submission

**Layer 2 — Deterministic Trace Metrics:**
- Captured from execution logs by ADK's trace exporter
- Hard numbers: latency, token usage, tool call success rate, retry count
- Defined in `evaluation/trace_metrics.json`
- Combined with Layer 1 scores in final EvalReport

### 8.2 EvalReport Schema
```json
{
  "run_id": "string (timestamp-based)",
  "timestamp": "ISO-8601",
  "duration_seconds": "number",
  "llm_judge_scores": {
    "seo_output": { "schema_validity": 0, "keyword_relevance": 0, "aeo_coverage": 0 },
    "gads_output": { "keyword_intent": 0, "ad_group_structure": 0, "negative_quality": 0 },
    "meta_output": { "funnel_distinction": 0, "audience_specificity": 0 },
    "copy_output": { "char_compliance": 0, "copy_distinctiveness": 0, "funnel_alignment": 0 },
    "system_output": { "cross_channel_consistency": 0, "completeness": 0 },
    "overall_score": 0
  },
  "trace_metrics": {
    "total_wall_time_seconds": 0,
    "tool_call_success_rate": 0,
    "hitl_checkpoint_count": 3,
    "parallel_strategy_time_seconds": 0,
    "json_parse_success_rate": 0,
    "schema_validation_pass_rate": 0,
    "character_limit_compliance_rate": 0,
    "drive_upload_success": true
  },
  "agent_traces": [
    {
      "agent": "string",
      "start_time": "ISO-8601",
      "end_time": "ISO-8601",
      "tool_calls": [],
      "retries": 0,
      "output_tokens": 0,
      "status": "success | partial | failed"
    }
  ]
}
```

---

## 9. IntakeBrief JSON Schema (Master Reference)

All agents depend on this schema. Any change here requires updating agent_cards.json.

```json
{
  "schema_version": "1.0",
  "business_name": "string (required)",
  "business_address": "string (required)",
  "project_name": "string (required, used as Drive folder name)",
  "user_email": "string (required, email format)",
  "services": ["string"] ,
  "service_areas": ["string"],
  "target_customer": "string (required, min 20 chars)",
  "unique_value_props": ["string"],
  "page_urls": [
    {
      "url": "string (required, valid URL)",
      "type": "homepage|service|portfolio|about|contact|blog|pricing|testimonials"
    }
  ],
  "competitors": ["string"],
  "monthly_budget": "string (required, e.g. ₹30,000)",
  "campaign_goal": "lead_generation|brand_awareness|sales",
  "portfolio_images": ["string (file path, optional)"]
}
```

---

## 10. Vibe Coding Paradigm — How This Architecture Uses It

This system is built spec-first, not code-first. The natural language files (.md)
ARE the primary engineering artefacts. Antigravity reads them and generates execution
code. This means:

1. **Changing agent behaviour = editing a .md file**, not Python code
2. **Adding a new tool = updating mcp_config.json**, not writing a wrapper
3. **Adding a new agent = writing a new .md file** + entry in agent_cards.json
4. **Debugging = reading Artifacts in Antigravity IDE**, not print statements
5. **Testing = running test prompts via Agents CLI**, not pytest

The spec files are the source of truth. The generated code is the output.
This inversion is the core paradigm shift of ADK 2.0 + Vibe Coding.

---

## 11. Test States — Architecture Validation

Use these three inputs to validate the full graph topology before the capstone demo.

### Test State 1 — Happy Path (Complete brief, Goa photography studio)
```
Business: Goa Lens Studio
Address: Shop 4, MG Road, Panaji, Goa 403001
Services: wedding photography, portrait sessions, commercial photography
Service areas: Goa, Mumbai, Bangalore
Target customer: Couples 24-35 planning destination weddings, budget ₹80k-2L
UVPs: 10 years experience, candid style, drone shots, 72hr gallery preview
URLs: homepage, /services, /portfolio, /about, /contact
Budget: ₹30,000/month
Goal: lead_generation
Email: test@goalensstudio.com
Expected: Full pipeline completes, 3 HITL pauses, Drive folder with 8 files, email delivered
```

### Test State 2 — Partial Failure Path (Missing fields, triggers validation)
```
Business: Test Studio
Services: (empty)
Budget: (missing)
Email: not-an-email
Expected: Supervisor validation fails, returns targeted clarification request
for exactly the 3 missing/invalid fields, does NOT restart intake from scratch
```

### Test State 3 — Revision Path (HITL #1 revision request)
```
After Test State 1 reaches HITL #1:
User types: "revise seo: Focus keywords more on Goa-specific destination wedding
terms. Add more question-based keywords for AEO."
Expected: Only seo_agent re-runs with this feedback appended to context.
gads_agent and meta_agent outputs are preserved.
StrategyBundle is rebuilt with new seo output + existing gads + meta outputs.
HITL #1 presented again.
```

---

## 12. Capstone Submission Checklist (Self-Audit)

Before submitting on Kaggle, verify:

- [ ] `architecture.md` — this file — complete and referenced in Kaggle writeup
- [ ] `agent_cards.json` — all 6 agents defined with input/output schemas
- [ ] All 6 agent `.md` files in `agents/` — complete, production-grade
- [ ] `mcp/mcp_config.json` — all 4 MCP servers configured
- [ ] `evaluation/judge_rubric.md` — rubric complete with scoring criteria
- [ ] `evaluation/trace_metrics.json` — 8 metrics defined
- [ ] At least one complete `outputs/eval/last_run_eval.json` with real scores
- [ ] `outputs/delivery_manifest.json` — from a real end-to-end run
- [ ] `README.md` — CLI execution instructions, setup guide, project index
- [ ] Kaggle notebook — writeup with architecture diagram, eval scores, demo screenshots
- [ ] Video explanation — 2-3 minutes, shows live run from intake to email delivery
- [ ] GitHub repo — public, `.env` and `credentials.json` NOT committed
- [ ] Kaggle submission — writeup + video link + code link submitted before July 6, 11:59 PM PT

---
*End of architecture.md — v1.0 | Next: agent_cards.json*
