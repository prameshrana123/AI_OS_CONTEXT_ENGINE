from context_engine import collect_basic_context,collect_heavy_context,client

import json
import time

LOG_FILE="agent_log.jsonl"

def log_event(event:dict):
    event["timestamp"]=time.time()
    with open(LOG_FILE,"a",encoding="utf-8") as f:
        f.write(json.dumps(event)+"\n")


def identify_tasks(basic_ctx):
    basic_ctx=basic_ctx
    proc=basic_ctx.get("process_name")
    title=basic_ctx.get("window_title")
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

def is_task_important(basic,task):
    title=(basic.get("window_title")or "").lower()
    proc=(basic.get("process_name")or "").lower()
    if task == "coding":
        return True
    if "chrome" in proc or task =="browsing":
        if any(x in title for x in[
            "github",
            "stack overflow",
            "documentation",
            "docs",
            "tutorial",
            "how to",
            "error",
            "exception",
            "api",
            "refernce"
        ]):
            return True
        if any(x in title for x in[
            "youtube",
            "netflix",
            "spotify",
            "instagram",
            "twitter"
        ]):
            return False
        return False
    return False

def reasoning():
    basic=collect_basic_context()
    task=identify_tasks(basic)
    importance=is_task_important(basic,task)
    if not importance:
        return None
    heavy=collect_heavy_context()
    insight=generate_insight_with_llm(
        task=task,
        basic_ctx=basic,
        heavy_ctx=heavy
    )
    return insight

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



def generate_proposal(insight=None):
    if insight is None:
        insight=reasoning()
    if insight is None:
        return None
    response=client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"""
You are an assistant that proposes actions
but NEVER executes them.

CRITICAL RULES:
- You may ONLY propose actions from the ALLOWED ACTION LIST below.
- You MUST respond in valid JSON only.
- Do NOT invent new actions.
- If no action is appropriate, choose "action": "none".
- Keep the response under 50 words.

ALLOWED ACTIONS:
- notify_user
- open_browser
- copy_to_clipboard
- none

Given the following insight, propose:
- One safe, reversible action
- Explain why
- Mark urgency (low / medium / high)

INSIGHT:
\"\"\"{insight}\"\"\"

Respond in JSON with EXACTLY this format:
{{
  "action": "notify_user | open_browser | copy_to_clipboard | none",
  "reason": "...",
  "urgency": "low | medium | high"
}}
"""

    )
    return response.text

def ask_for_approval(basic,task,important,insight,proposal):
    if proposal is None:
        return None
    
    # We print the proposal so the user knows what they are approving
    print(proposal)
    choice = input("\n Approve action? (y/n)").strip().lower()

    try:
        if isinstance(proposal, str):
            proposal_dict=json.loads(proposal)
        else:
            proposal_dict=proposal
    except json.JSONDecodeError:
        proposal_dict={"raw":proposal}
    
    log_event({
        "process":basic.get("process_name"),
        "window":basic.get("window_title"),
        "proposal":proposal_dict,
        "approved":choice,
        "insight":insight,
        "task":task,
        "important":important,
        "user_decison":choice
    })
    
    if choice == "y":
        try:
            # Try importing as a package first (standard from root)
            from context_engine.executor import ActionExecutor
        except (ImportError, ModuleNotFoundError):
            # Fallback for when running code from inside the directory (script mode)
            from executor import ActionExecutor
        
        ActionExecutor.execute(proposal_dict)
    
    return choice

LAST_WINDOW_SIGN=None
WINDOW_ENTER_TIME=None
LAST_LLM_CALL_TIME=0
MIN_DWELL_TIME=5
SAME_WINDOW_INTERVAL=25

def should_call_llm(basic,task,important):
    global LAST_WINDOW_SIGN,WINDOW_ENTER_TIME,LAST_WINDOW_SIGN,LAST_LLM_CALL_TIME
    basic=collect_basic_context()
    important=is_task_important(basic,task)
    now =time.time()
    sig=(
        basic.get("process_name"),
        basic.get("window_title")
    )

    if not important:
        LAST_WINDOW_SIGN=sig
        WINDOW_ENTER_TIME=now
        return False
    
    if sig != LAST_WINDOW_SIGN:
        LAST_WINDOW_SIGN=sig
        WINDOW_ENTER_TIME=now
        return False
    
    dwell=now-(WINDOW_ENTER_TIME or now)
    since_last_llm=now-LAST_LLM_CALL_TIME

    if dwell >=MIN_DWELL_TIME and since_last_llm>=MIN_DWELL_TIME:
        LAST_LLM_CALL_TIME=now
        return True
    
    if since_last_llm >=SAME_WINDOW_INTERVAL:
        LAST_LLM_CALL_TIME=now
        return True
    print("DWELL:", dwell, "SINCE_LLM:", since_last_llm)

    return False

def background_loop():
    print("✅ Agent runing!")
    while True:
        basic=collect_basic_context()
        task=identify_tasks(basic)
        important=is_task_important(basic,task)

        if should_call_llm(basic,task,important):
            heavy=collect_heavy_context()
            insight=generate_insight_with_llm(task,basic,heavy)
            print("\n INSIGHT",insight)
            proposal=generate_proposal(insight)
            print("\n PROPOSAL",proposal)
            if proposal:
                approval=ask_for_approval(basic=basic,task=task,important=important,insight=insight,proposal=proposal)
            print("\n APPROVAL",approval)
        time.sleep(1)


if __name__ == "__main__":
    background_loop()


    