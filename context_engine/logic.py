import json
import time
from context_engine import client, collect_basic_context, collect_heavy_context

# --- Logic from ai.py ---

def identify_tasks(basic_ctx):
    # basic_ctx is the dict
    proc = basic_ctx.get("process_name", "").lower()
    title = basic_ctx.get("window_title", "").lower()
    
    if any(x in proc for x in ["code", "pycharm", "idea", "sublime", "atom"]):
        return "coding"

    if any(x in title for x in [".py", ".js", ".cpp", ".java", "visual studio", "github", "stack overflow"]):
        return "coding"
 
    if any(x in proc for x in ["discord", "slack", "teams", "whatsapp"]):
        return "communication"

    if any(x in title for x in ["youtube", "netflix", "spotify"]):
        return "media"

    if any(x in proc for x in ["spotify", "vlc"]):
        return "media"
    if any(x in proc for x in ["chrome", "firefox", "msedge", "brave"]):
        return "browsing"
    if "explorer" in proc:
        return "system"

    return "unknown"

def is_task_important(basic, task):
    title = (basic.get("window_title") or "").lower()
    proc = (basic.get("process_name") or "").lower()
    
    if task == "coding":
        return True
    if "chrome" in proc or task == "browsing":
        if any(x in title for x in [
            "github", "stack overflow", "documentation", "docs", 
            "tutorial", "how to", "error", "exception", "api", "refernce"
        ]):
            return True
        if any(x in title for x in ["youtube", "netflix", "spotify", "instagram", "twitter"]):
            return False
        return False
    return False

def generate_insight_with_llm(task, basic_ctx, heavy_ctx):
    prompt = {
        "task": task,
        "active_window": {
            "title": basic_ctx["window_title"],
            "process": basic_ctx["process_name"]
        },
        "recent_file_events": heavy_ctx.get("fsm_events", []),
        "clipboard_changed": heavy_ctx.get("clipboard_state", {}).get("changed"),
        "system_activity": {
            "network": heavy_ctx.get("network_state")
        }
    }

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"""
You are an OS-level assistant.
Generate the response under 50 words dont make lengthy responses.

Analyze the following context and generate a short insight:
- What the user is likely doing
- Whether they are progressing or distracted
- One helpful suggestion (no actions yet)

Context:
{json.dumps(prompt, indent=2)}
"""
    )
    return response.text

def reasoning(basic=None):
    if basic is None:
        basic = collect_basic_context()
    
    task = identify_tasks(basic)
    importance = is_task_important(basic, task)
    
    if not importance:
        return None
        
    heavy = collect_heavy_context()
    insight = generate_insight_with_llm(
        task=task,
        basic_ctx=basic,
        heavy_ctx=heavy
    )
    return insight

def generate_proposal(insight):
    if insight is None: 
        return None
        
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"""
You are an assistant that proposes actions
but NEVER executes them.
Generate the response under 50 words dont make lengthy responses.

Given the following insight, propose:
- One safe, reversible action
- Explain why
- Mark urgency (low / medium / high)

Insight:
\"\"\"{insight}\"\"\"

Respond in JSON with:
{{
  "action": "...",
  "reason": "...",
  "urgency": "low|medium|high"
}}
"""
    )
    return response.text
