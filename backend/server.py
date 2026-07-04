import os
import re
import uuid
import json
import threading
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Configure Gemini API
gemini_api_key = os.getenv("GEMINI_API_KEY")
if gemini_api_key:
    genai.configure(api_key=gemini_api_key)
else:
    print("Warning: GEMINI_API_KEY is not set. Gemini API calls will fail.")

app = Flask(__name__)
# Enable CORS for http://localhost:3000
CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})

# Find project root relative to this file (backend/server.py)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Thread lock for thread-safe memory session storage
state_lock = threading.Lock()

# In-memory session store
# Schema:
# {
#   session_id: {
#       "id": str,
#       "status": "running" | "waiting_for_checkpoint" | "complete" | "failed",
#       "checkpoint": int,
#       "intake_brief": dict,
#       "agents": [{"id": str, "status": str}],
#       "outputs": { agent_id: output_text },
#       "file_paths": { agent_id: absolute_path },
#       "feedback": { 1: [], 2: [], 3: [] }
#   }
# }
sessions = {}

def init_session_agents():
    """Returns the default agent sequence and status list."""
    return [
        {"id": "seo_agent", "status": "pending"},
        {"id": "google_ads_agent", "status": "pending"},
        {"id": "meta_ads_agent", "status": "pending"},
        {"id": "copywriter_agent", "status": "pending"},
        {"id": "visual_agent", "status": "pending"},
        {"id": "llm_judge", "status": "pending"}
    ]

def read_agent_file(relative_path):
    """Safely reads template files relative to project root."""
    path = os.path.join(PROJECT_ROOT, relative_path)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"Error reading file {path}: {e}")
    # Fallback default instructions if local files do not exist
    return f"Default prompt for {relative_path}. Execute the core responsibility."

def write_output_file(session_id, filename, content):
    """Writes agent output to a local folder inside outputs/session_{id}."""
    dir_path = os.path.join(PROJECT_ROOT, "outputs", f"session_{session_id}")
    os.makedirs(dir_path, exist_ok=True)
    path = os.path.join(dir_path, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path

def update_agent_status(session_id, agent_id, status):
    """Updates status for a specific agent in thread-safe manner."""
    with state_lock:
        if session_id in sessions:
            for ag in sessions[session_id]["agents"]:
                if ag["id"] == agent_id:
                    ag["status"] = status
                    break

def generate_with_fallback(system_prompt, final_user_prompt):
    """
    Tries each model in order. If one hits a quota/429 error,
    automatically moves to the next model in the list.
    """
    fallback_models = [
        "gemini-2.5-flash-lite",
        "gemini-2.0-flash-lite",
        "gemini-2.0-flash",
        "gemini-2.5-flash",
        "gemini-flash-lite-latest"
    ]

    last_error = None

    for model_name in fallback_models:
        try:
            model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=system_prompt
            )
            response = model.generate_content(final_user_prompt)
            print(f"✓ Success using model: {model_name}")
            return response

        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "quota" in error_str.lower():
                print(f"✗ Quota exceeded on {model_name}, trying next model...")
                last_error = e
                continue
            else:
                raise e

    raise Exception(f"All fallback models exhausted. Last error: {last_error}")


def run_agent(session_id, agent_id, prompt_path, user_content, feedback_str=None, is_json=False):
    """Executes a single Gemini generation cycle with automatic model fallback."""
    update_agent_status(session_id, agent_id, "running")
    
    try:
        system_prompt = read_agent_file(prompt_path)
        print(f"DEBUG [{agent_id}]: system_prompt length = {len(system_prompt)}, prompt_path = {prompt_path}")
        # Build user prompt, appending feedback if revision is requested
        final_user_prompt = user_content
        if feedback_str:
            final_user_prompt += f"\n\n--- SUPERVISOR REVISION FEEDBACK ---\n{feedback_str}"
        
        response = generate_with_fallback(system_prompt, final_user_prompt)
        output_text = response.text if response and response.text else ""
        
        # Save output
        filename = f"{agent_id}.json" if is_json else f"{agent_id}.txt"
        file_path = write_output_file(session_id, filename, output_text)
        
        with state_lock:
            if session_id in sessions:
                sessions[session_id]["outputs"][agent_id] = output_text
                sessions[session_id]["file_paths"][agent_id] = file_path
                
        update_agent_status(session_id, agent_id, "completed")
        return output_text
    except Exception as e:
        print(f"Error executing agent {agent_id}: {e}")
        update_agent_status(session_id, agent_id, "failed")
        raise e

def process_stage(session_id, stage_num):
    """Background pipeline state driver."""
    with state_lock:
        session = sessions.get(session_id)
        if not session:
            return
        session["status"] = "running"
    
    try:
        intake_brief = session["intake_brief"]
        # Join any revision comments collected for this stage
        feedback_list = session["feedback"].get(stage_num, [])
        feedback_str = "\n".join(feedback_list) if feedback_list else None
        
        if stage_num == 1:
            # Run SEO, Google Ads, and Meta Ads sequentially
            brief_str = f"Intake Brief Data:\n{json.dumps(intake_brief, indent=2)}"
            
            run_agent(session_id, "seo_agent", "agents/seo_agent.md", brief_str, feedback_str)
            run_agent(session_id, "google_ads_agent", "agents/google_ads_agent.md", brief_str, feedback_str)
            run_agent(session_id, "meta_ads_agent", "agents/meta_ads_agent.md", brief_str, feedback_str)
            
            with state_lock:
                if sessions.get(session_id):
                    sessions[session_id]["status"] = "waiting_for_checkpoint"
                    sessions[session_id]["checkpoint"] = 1
                    
        elif stage_num == 2:
            # Inputs for copywriter: brief + stage 1 outputs
            seo_out = session["outputs"].get("seo_agent", "")
            gads_out = session["outputs"].get("google_ads_agent", "")
            mads_out = session["outputs"].get("meta_ads_agent", "")
            
            s1_combined = f"SEO Recommendations:\n{seo_out}\n\nGoogle Ads Strategy:\n{gads_out}\n\nMeta Ads Strategy:\n{mads_out}"
            copywriter_prompt = f"Intake Brief:\n{json.dumps(intake_brief, indent=2)}\n\nMarketing Strategies:\n{s1_combined}"
            
            copy_out = run_agent(session_id, "copywriter_agent", "agents/copywriter_agent.md", copywriter_prompt, feedback_str)
            
            # Inputs for visual agent: brief + meta strategy + copywriter output
            visual_prompt = (
                f"Intake Brief:\n{json.dumps(intake_brief, indent=2)}\n\n"
                f"Meta Strategy:\n{mads_out}\n\n"
                f"Ad Copywriting Output:\n{copy_out}"
            )
            run_agent(session_id, "visual_agent", "agents/visual_agent.md", visual_prompt, feedback_str)
            
            with state_lock:
                if sessions.get(session_id):
                    sessions[session_id]["status"] = "waiting_for_checkpoint"
                    sessions[session_id]["checkpoint"] = 2
                    
        elif stage_num == 3:
            # Re-fetch fresh outputs directly from the global sessions dict
            # (bypasses any stale local 'session' reference)
            with state_lock:
                current_outputs = dict(sessions.get(session_id, {}).get("outputs", {}))

            all_outputs = []
            for k, v in current_outputs.items():
                if k != "llm_judge" and v:
                    all_outputs.append(f"=== Agent Output: {k} ===\n{v}")

            if not all_outputs:
                raise Exception(
                    f"No agent outputs found for session {session_id} — "
                    f"cannot run llm_judge. Outputs dict was: {current_outputs}"
                )

            judge_prompt = (
                "Review the following marketing deliverables and output a detailed appraisal report "
                "with an overall numerical score out of 38.\n\n" + "\n\n".join(all_outputs)
            )
            
            run_agent(session_id, "llm_judge", "evaluation/judge_rubric.md", judge_prompt, feedback_str, is_json=True)
            
            with state_lock:
                if sessions.get(session_id):
                    sessions[session_id]["status"] = "waiting_for_checkpoint"
                    sessions[session_id]["checkpoint"] = 3

    except Exception as e:
        print(f"Pipeline error in stage {stage_num} for session {session_id}: {e}")
        with state_lock:
            if sessions.get(session_id):
                sessions[session_id]["status"] = "failed"

def extract_score(judge_text):
    """Attempts to search and parse score from evaluation output."""
    if not judge_text:
        return None
    try:
        # Search for fractional score "X/38"
        match_fraction = re.search(r'(\d+)\s*/\s*38', judge_text)
        if match_fraction:
            return int(match_fraction.group(1))
        # Search for score patterns like '"score": X' or 'score of X'
        match_json = re.search(r'"score"\s*:\s*(\d+)', judge_text, re.IGNORECASE)
        if match_json:
            return int(match_json.group(1))
        match_phrase = re.search(r'(\d+)\s+out\s+of\s+38', judge_text, re.IGNORECASE)
        if match_phrase:
            return int(match_phrase.group(1))
    except Exception:
        pass
    return None

# --- ENDPOINTS ---

@app.route("/api/run", methods=["POST"])
def run_pipeline():
    data = request.get_json() or {}
    intake_brief = data.get("intake_brief", {})
    
    session_id = str(uuid.uuid4())
    
    with state_lock:
        sessions[session_id] = {
            "id": session_id,
            "status": "running",
            "checkpoint": 0,
            "intake_brief": intake_brief,
            "agents": init_session_agents(),
            "outputs": {},
            "file_paths": {},
            "feedback": {1: [], 2: [], 3: []}
        }
        
    # Kick off Stage 1
    t = threading.Thread(target=process_stage, args=(session_id, 1))
    t.start()
    
    return jsonify({"session_id": session_id}), 200

@app.route("/api/session/<session_id>/status", methods=["GET"])
def get_session_status(session_id):
    with state_lock:
        session = sessions.get(session_id)
        
    if not session:
        return jsonify({"error": "Session not found"}), 404
        
    return jsonify({
        "overall_status": session["status"],
        "current_checkpoint": session["checkpoint"],
        "agents": session["agents"]
    }), 200

@app.route("/api/session/<session_id>/checkpoint", methods=["POST"])
def submit_checkpoint(session_id):
    data = request.get_json() or {}
    checkpoint = data.get("checkpoint")
    decision = data.get("decision")
    feedback = data.get("feedback", "")
    
    with state_lock:
        session = sessions.get(session_id)
        
    if not session:
        return jsonify({"error": "Session not found"}), 404
        
    if session["checkpoint"] != checkpoint:
        return jsonify({"error": f"Invalid transition. Current checkpoint is {session['checkpoint']}"}), 400

    if decision == "approve":
        if checkpoint == 1:
            # Advance to Stage 2
            t = threading.Thread(target=process_stage, args=(session_id, 2))
            t.start()
        elif checkpoint == 2:
            # Advance to Stage 3
            t = threading.Thread(target=process_stage, args=(session_id, 3))
            t.start()
        elif checkpoint == 3:
            # Finalize Stage 4 execution
            with state_lock:
                session["status"] = "complete"
                
    elif decision == "revise":
        with state_lock:
            # Add supervisor revision comment
            if checkpoint in session["feedback"]:
                session["feedback"][checkpoint].append(feedback)
            session["status"] = "running"
            
        # Rerun corresponding stage
        t = threading.Thread(target=process_stage, args=(session_id, checkpoint))
        t.start()
        
    else:
        return jsonify({"error": "Decision must be 'approve' or 'revise'"}), 400

    return jsonify({"ok": True}), 200

@app.route("/api/session/<session_id>/outputs", methods=["GET"])
def get_session_outputs(session_id):
    with state_lock:
        session = sessions.get(session_id)
        
    if not session:
        return jsonify({"error": "Session not found"}), 404
        
    judge_text = session["outputs"].get("llm_judge", "")
    score = extract_score(judge_text)
    
    # Generate snippets of agent results for summary view
    summary = {}
    for agent_id, text in session["outputs"].items():
        if len(text) > 300:
            summary[agent_id] = text[:300] + "..."
        else:
            summary[agent_id] = text
            
    drive_files = list(session["file_paths"].values())
    
    return jsonify({
        "eval_score": score,
        "drive_files": drive_files,
        "summary": summary
    }), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)