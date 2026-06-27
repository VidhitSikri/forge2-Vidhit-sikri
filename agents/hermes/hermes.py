import os
import json
import time
import urllib.request
import urllib.parse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
EASTROUTER_API_KEY = os.environ.get("EASTROUTER_API_KEY")
EASTROUTER_BASE_URL = os.environ.get("EASTROUTER_BASE_URL", "https://api.eastrouter.com/v1").rstrip("/")
EASTROUTER_MODEL = "z-ai/glm-5.1"  # Confirmed supported model
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_REPO = os.environ.get("GITHUB_REPO")

STATE_FILE = "sprint_state.json"

def slack_api_call(method, payload=None):
    url = f"https://slack.com/api/{method}"
    headers = {
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
        "Content-Type": "application/json; charset=utf-8"
    }
    
    data = None
    if payload:
        data = json.dumps(payload).encode('utf-8')
        
    for attempt in range(3):
        req = urllib.request.Request(url, data=data, headers=headers, method="POST" if payload else "GET")
        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                res_data = json.loads(response.read().decode('utf-8'))
                if not res_data.get("ok"):
                    print(f"Slack API error for {method}: {res_data}")
                return res_data
        except Exception as e:
            print(f"Slack API attempt {attempt+1} failed: {e}")
            if attempt < 2:
                time.sleep(2)
    return {"ok": False}

def github_api_call(path, payload=None, method="GET"):
    url = f"https://api.github.com{path}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Hermes-Orchestrator"
    }
    
    data = None
    if payload:
        data = json.dumps(payload).encode('utf-8')
        headers["Content-Type"] = "application/json"
        
    for attempt in range(3):
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                return json.loads(response.read().decode('utf-8'))
        except Exception as e:
            print(f"GitHub API attempt {attempt+1} failed: {e}")
            if attempt < 2:
                time.sleep(2)
    return None

def ask_llm(system_prompt, user_prompt):
    url = f"{EASTROUTER_BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {EASTROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": EASTROUTER_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.2
    }
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode('utf-8'))
            return res["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"EastRouter LLM call failed: {e}")
        return ""

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "current_sprint": 1,
        "sprint_goal": "",
        "tasks": [],
        "current_task_index": -1,
        "last_sprint_main_message_ts": "0",
        "last_agent_coder_message_ts": "0"
    }

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def resolve_channels():
    # Fetch both public and private channels to support all setups
    res = slack_api_call("conversations.list", {
        "types": "public_channel,private_channel",
        "limit": 1000
    })
    channels = {}
    if res.get("ok"):
        for chan in res.get("channels", []):
            name = chan["name"]
            channels[f"#{name}"] = chan["id"]
    return channels

def get_bot_user_id():
    res = slack_api_call("auth.test")
    if res.get("ok"):
        return res.get("user_id")
    return None

def main():
    print("Hermes Orchestrator started. Polling Slack...")
    
    # Resolve channel IDs
    channels = resolve_channels()
    sprint_main_id = channels.get("#sprint-main")
    agent_coder_id = channels.get("#agent-coder")
    
    if not sprint_main_id or not agent_coder_id:
        print(f"Error: Could not resolve all channels. Resolved: {channels}")
        return

    bot_id = get_bot_user_id()
    if not bot_id:
        print("Error: Could not resolve Bot User ID from Slack.")
        return
    print(f"Authenticated as Bot User ID: {bot_id}")

    state = load_state()
    
    while True:
        # Resolve channels periodically in case they change
        channels = resolve_channels()
        sprint_main_id = channels.get("#sprint-main", sprint_main_id)
        agent_coder_id = channels.get("#agent-coder", agent_coder_id)

        # 1. Poll #sprint-main for new goal mentions
        history = slack_api_call("conversations.history", {"channel": sprint_main_id, "limit": 10})
        if history.get("ok"):
            messages = history.get("messages", [])
            # Sort messages old to new to process chronologically
            messages.reverse()
            
            for msg in messages:
                ts = msg.get("ts")
                # Only check newer messages
                if float(ts) <= float(state.get("last_sprint_main_message_ts", "0")):
                    continue
                    
                text = msg.get("text", "")
                # Check if bot is mentioned
                if f"<@{bot_id}>" in text:
                    print(f"Received new goal in #sprint-main: {text}")
                    # Extract the sprint goal
                    goal = text.replace(f"<@{bot_id}>", "").strip()
                    
                    # Ask LLM to plan tasks
                    system_prompt = (
                        "You are Hermes, the main orchestrator and product owner. Your job is to take a high-level sprint goal "
                        "and divide it into a JSON list of clear, executable, and sequential programming tasks for the developer agent (OpenClaw).\n"
                        "Each task description must be self-contained and specify exactly what files to write or modify, or what features to implement.\n"
                        "Respond ONLY with a valid JSON array of strings, representing the list of tasks. No markdown, no formatting outside JSON."
                    )
                    user_prompt = f"Sprint Goal: {goal}"
                    
                    llm_response = ask_llm(system_prompt, user_prompt)
                    # Clean up markdown code blocks if any
                    if "```json" in llm_response:
                        llm_response = llm_response.split("```json")[1].split("```")[0].strip()
                    elif "```" in llm_response:
                        llm_response = llm_response.split("```")[1].split("```")[0].strip()
                    
                    try:
                        tasks_list = json.loads(llm_response.strip())
                        if isinstance(tasks_list, list) and len(tasks_list) > 0:
                            state["sprint_goal"] = goal
                            state["tasks"] = [
                                {
                                    "index": idx,
                                    "description": task_desc,
                                    "status": "pending",
                                    "branch": "",
                                    "pr_number": None,
                                    "pr_url": ""
                                } for idx, task_desc in enumerate(tasks_list)
                            ]
                            state["current_task_index"] = 0
                            state["last_sprint_main_message_ts"] = ts
                            save_state(state)
                            
                            # Post tasks to #sprint-main
                            formatted_tasks = "\n".join([f"{i+1}. {t}" for i, t in enumerate(tasks_list)])
                            slack_api_call("chat.postMessage", {
                                "channel": sprint_main_id,
                                "text": f"Sprint planning complete! Divided goal into {len(tasks_list)} tasks:\n{formatted_tasks}\n\nStarting Task 1..."
                            })
                            
                            # Delegate Task 1 to OpenClaw in #agent-coder
                            slack_api_call("chat.postMessage", {
                                "channel": agent_coder_id,
                                "text": f"<@openclaw> Task 1: {state['tasks'][0]['description']}"
                            })
                            state["tasks"][0]["status"] = "in_progress"
                            save_state(state)
                        else:
                            print(f"LLM did not return a valid list: {llm_response}")
                    except Exception as e:
                        print(f"Failed to parse LLM response as JSON: {e}. Raw response: {llm_response}")
                        
        # 2. Check status of current task PR
        if state["current_task_index"] != -1 and state["current_task_index"] < len(state["tasks"]):
            current_task = state["tasks"][state["current_task_index"]]
            if current_task["status"] == "in_progress" and current_task["pr_number"]:
                pr_num = current_task["pr_number"]
                print(f"Checking status of PR #{pr_num} for Task {state['current_task_index']+1}...")
                pr_details = github_api_call(f"/repos/{GITHUB_REPO}/pulls/{pr_num}")
                if pr_details:
                    # Check if merged or closed
                    merged = pr_details.get("merged", False)
                    state_str = pr_details.get("state", "open")
                    
                    if merged or state_str == "closed":
                        if merged:
                            print(f"PR #{pr_num} has been merged!")
                            current_task["status"] = "completed"
                            slack_api_call("chat.postMessage", {
                                "channel": sprint_main_id,
                                "text": f"Task {state['current_task_index']+1} PR merged successfully! ✅"
                            })
                        else:
                            print(f"PR #{pr_num} was closed without merge.")
                            current_task["status"] = "closed_unmerged"
                            
                        # Advance to next task
                        next_idx = state["current_task_index"] + 1
                        if next_idx < len(state["tasks"]):
                            state["current_task_index"] = next_idx
                            next_task = state["tasks"][next_idx]
                            next_task["status"] = "in_progress"
                            save_state(state)
                            
                            slack_api_call("chat.postMessage", {
                                "channel": agent_coder_id,
                                "text": f"<@openclaw> Task {next_idx+1}: {next_task['description']}"
                            })
                        else:
                            # All tasks done!
                            slack_api_call("chat.postMessage", {
                                "channel": sprint_main_id,
                                "text": "All tasks for the sprint have been completed! 🚀🎉"
                            })
                            state["current_task_index"] = -1
                            save_state(state)
                            
        time.sleep(10)

if __name__ == "__main__":
    main()
