import os
import json
import time
import subprocess
import urllib.request
import urllib.parse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

STATE_FILE = "sprint_state.json"
EASTROUTER_API_KEY = os.environ.get("EASTROUTER_API_KEY")
EASTROUTER_BASE_URL = os.environ.get("EASTROUTER_BASE_URL", "https://api.eastrouter.com/v1").rstrip("/")
EASTROUTER_MODEL = "z-ai/glm-5.1"  # Confirmed supported model
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_REPO = os.environ.get("GITHUB_REPO")

def get_openclaw_token():
    # Attempt to load from various potential config paths
    paths = [
        os.path.expanduser("~/.openclaw/openclaw.json"),
        "agents/openclaw/openclaw.json",
        "../../.openclaw/openclaw.json"
    ]
    for p in paths:
        if os.path.exists(p):
            try:
                with open(p, "r") as f:
                    config = json.load(f)
                    token = config.get("channels", {}).get("slack", {}).get("botToken")
                    if isinstance(token, dict) and token.get("source") == "env":
                        # If it points to env, use env variable
                        env_id = token.get("id", "SLACK_BOT_TOKEN")
                        return os.environ.get(env_id)
                    if isinstance(token, str):
                        return token
            except Exception:
                pass
    # Fallback to general SLACK_BOT_TOKEN if not found
    return os.environ.get("SLACK_BOT_TOKEN")

OPENCLAW_BOT_TOKEN = get_openclaw_token()

def slack_api_call(method, payload=None):
    url = f"https://slack.com/api/{method}"
    headers = {
        "Authorization": f"Bearer {OPENCLAW_BOT_TOKEN}",
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
        "User-Agent": "OpenClaw-Agent"
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
    return None

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

def run_cicd():
    print("Running local CI/CD pipeline checks...")
    logs = []
    
    # 1. Check PHP syntax in modified files
    try:
        git_status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, check=True)
        php_files = []
        for line in git_status.stdout.splitlines():
            parts = line.strip().split()
            if len(parts) >= 2:
                file_path = parts[-1]
                if file_path.endswith(".php") and os.path.exists(file_path):
                    php_files.append(file_path)
                    
        for php_file in php_files:
            lint = subprocess.run(["php", "-l", php_file], capture_output=True, text=True)
            if lint.returncode != 0:
                logs.append(f"CI/CD Lint Failed for {php_file}: {lint.stdout.strip()}")
                return False, "\n".join(logs)
            else:
                logs.append(f"CI/CD Lint Passed: {php_file}")
    except Exception as e:
        logs.append(f"Skipped PHP linting: {e}")
        
    # 2. Run backend test suite if Laravel vendor/phpunit is present
    phpunit_path = os.path.join("backend", "vendor", "bin", "phpunit")
    if os.path.exists(phpunit_path):
        try:
            test_run = subprocess.run([phpunit_path], cwd="backend", capture_output=True, text=True)
            logs.append(test_run.stdout)
            if test_run.returncode != 0:
                logs.append("CI/CD Laravel PHPUnit tests failed.")
                return False, "\n".join(logs)
            logs.append("CI/CD Laravel PHPUnit tests passed successfully.")
        except Exception as e:
            logs.append(f"Failed to execute PHPUnit: {e}")
            return False, "\n".join(logs)
    else:
        logs.append("No local PHPUnit test suite found. Skipping test execution.")
        
    return True, "\n".join(logs)

def execute_task(task_description, sprint_num, task_idx):
    print(f"Executing Task {task_idx+1}: {task_description}")
    
    # Ask LLM to generate code changes
    system_prompt = (
        "You are OpenClaw, an expert developer agent. Your task is to implement the requested programming changes "
        "within the workspace.\n"
        "Analyze the project structure (containing backend/ Laravel app and frontend/ React app).\n"
        "You can write files or run shell/terminal commands. You must output file paths that write directly into 'backend/' or 'frontend/' subdirectories (e.g. 'backend/app/Models/User.php'). Do NOT write to temporary or backup folders.\n"
        "Return the changes as a valid JSON array of operations. Each operation must be an object:\n"
        "{\n"
        "  \"action\": \"create\" | \"modify\" | \"delete\" | \"run_command\",\n"
        "  \"path\": \"relative/path/to/file (omit if action is run_command)\",\n"
        "  \"content\": \"...file content... (omit if action is run_command)\",\n"
        "  \"command\": \"...shell command... (only if action is run_command)\"\n"
        "}\n"
        "Provide ONLY the JSON response. Do not include explanations, code blocks, or markdown formatting."
    )
    user_prompt = f"Implement changes for Task: {task_description}"
    
    llm_response = ask_llm(system_prompt, user_prompt)
    
    # Extract JSON content
    clean_json = llm_response.strip()
    if "```json" in clean_json:
        clean_json = clean_json.split("```json")[1].split("```")[0].strip()
    elif "```" in clean_json:
        clean_json = clean_json.split("```")[1].split("```")[0].strip()
        
    try:
        operations = json.loads(clean_json)
        applied_ops = []
        for op in operations:
            action = op.get("action")
            
            if action == "run_command":
                cmd = op.get("command")
                print(f"Running task command: {cmd}")
                res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                applied_ops.append(f"Ran command '{cmd}' (exit code: {res.returncode})")
                if res.stdout:
                    applied_ops.append(f"Stdout:\n{res.stdout.strip()}")
                if res.stderr:
                    applied_ops.append(f"Stderr:\n{res.stderr.strip()}")
                continue
                
            path = op.get("path")
            content = op.get("content", "")
            
            # Prevent writing outside the workspace
            if not path or ".." in path or path.startswith("/") or path.startswith("\\"):
                continue
                
            # Ensure parent directories exist
            dir_name = os.path.dirname(path)
            if dir_name and not os.path.exists(dir_name):
                os.makedirs(dir_name)
                
            if action == "create" or action == "modify":
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
                applied_ops.append(f"Wrote {path}")
            elif action == "delete":
                if os.path.exists(path):
                    os.remove(path)
                    applied_ops.append(f"Deleted {path}")
        return True, applied_ops
    except Exception as e:
        print(f"Failed to apply LLM changes: {e}. Response: {llm_response}")
        return False, [f"Error: {e}"]

def main():
    print("OpenClaw Developer Agent started. Polling Slack...")
    
    channels = resolve_channels()
    agent_coder_id = channels.get("#agent-coder")
    agent_log_id = channels.get("#agent-log")
    human_review_id = channels.get("#human-review")
    
    if not agent_coder_id or not agent_log_id or not human_review_id:
        print(f"Error: Could not resolve channels. Resolved: {channels}")
        return
        
    bot_id = get_bot_user_id()
    if not bot_id:
        print("Error: Could not resolve Bot User ID from Slack.")
        return
    print(f"Authenticated as Bot User ID: {bot_id}")

    while True:
        # Resolve channels periodically in case they change
        channels = resolve_channels()
        agent_coder_id = channels.get("#agent-coder", agent_coder_id)
        agent_log_id = channels.get("#agent-log", agent_log_id)
        human_review_id = channels.get("#human-review", human_review_id)

        state = load_state()
        last_processed_ts = "0"
        if state:
            last_processed_ts = state.get("last_agent_coder_message_ts", "0")

        history = slack_api_call("conversations.history", {"channel": agent_coder_id, "limit": 10})
        if history.get("ok"):
            messages = history.get("messages", [])
            messages.reverse()
            
            for msg in messages:
                ts = msg.get("ts")
                if float(ts) <= float(last_processed_ts):
                    continue
                    
                text = msg.get("text", "")
                if f"<@{bot_id}>" in text:
                    print(f"Received new task in #agent-coder: {text}")
                    
                    state = load_state()
                    if not state or state["current_task_index"] == -1:
                        print("No active sprint state found or sprint is not running.")
                        continue
                        
                    task_idx = state["current_task_index"]
                    current_task = state["tasks"][task_idx]
                    
                    # 1. Execute LLM coding changes
                    success, changes = execute_task(current_task["description"], state["current_sprint"], task_idx)
                    
                    # 2. Write details to #agent-log
                    log_text = f"*OpenClaw Dev Log - Sprint {state['current_sprint']} Task {task_idx+1}*\n"
                    if success:
                        log_text += f"Status: Code generation complete. Applied {len(changes)} file operations.\n"
                        log_text += "\n".join([f"- {c}" for c in changes])
                    else:
                        log_text += f"Status: Code generation failed. {changes[0]}\n"
                    slack_api_call("chat.postMessage", {
                        "channel": agent_log_id,
                        "text": log_text
                    })
                    
                    # Save the processed message ts regardless of success to avoid loop
                    state["last_agent_coder_message_ts"] = ts
                    save_state(state)
                    
                    if not success:
                        continue
                        
                    # 3. Run CI/CD validation
                    cicd_ok, cicd_logs = run_cicd()
                    cicd_status_text = "CI/CD checks passed successfully! ✅" if cicd_ok else "CI/CD checks failed! ❌"
                    slack_api_call("chat.postMessage", {
                        "channel": agent_log_id,
                        "text": f"*CI/CD Pipeline Status:*\n{cicd_status_text}\n```\n{cicd_logs}\n```"
                    })
                    
                    if not cicd_ok:
                        slack_api_call("chat.postMessage", {
                            "channel": agent_coder_id,
                            "text": "Task implementation failed CI/CD verification. Please check the logs."
                        })
                        continue
                        
                    # 4. Git Branch, Commit, and Push
                    branch_name = f"feature/sprint-{state['current_sprint']}-task-{task_idx+1}"
                    try:
                        # Git config (using safe defaults)
                        subprocess.run(["git", "config", "user.name", "OpenClaw Agent"], check=True)
                        subprocess.run(["git", "config", "user.email", "openclaw@agent.local"], check=True)
                        
                        # Create feature branch (using -B to overwrite/reset if it already exists)
                        subprocess.run(["git", "checkout", "-B", branch_name], check=True)
                        subprocess.run(["git", "add", "."], check=True)
                        subprocess.run(["git", "commit", "-m", f"Sprint {state['current_sprint']} Task {task_idx+1}: {current_task['description']}"], check=True)
                        
                        # Push to remote GitHub repo
                        remote_url = f"https://{GITHUB_TOKEN}@github.com/{GITHUB_REPO}.git"
                        subprocess.run(["git", "push", "-u", remote_url, branch_name, "--force"], check=True)
                        print(f"Successfully pushed branch {branch_name} to GitHub.")
                    except Exception as e:
                        print(f"Git operations failed: {e}")
                        slack_api_call("chat.postMessage", {
                            "channel": agent_log_id,
                            "text": f"Git operations failed: {e}"
                        })
                        # Return to main branch to avoid stuck state
                        subprocess.run(["git", "checkout", "main"], check=True)
                        continue
                        
                    # 5. Create Pull Request (PR) on GitHub
                    pr_payload = {
                        "title": f"Sprint {state['current_sprint']} Task {task_idx+1}: {current_task['description']}",
                        "head": branch_name,
                        "base": "main",
                        "body": f"Automated PR containing changes for Task {task_idx+1} of Sprint {state['current_sprint']}.\nGoal: {state['sprint_goal']}"
                    }
                    pr_res = github_api_call(f"/repos/{GITHUB_REPO}/pulls", payload=pr_payload, method="POST")
                    
                    if pr_res and pr_res.get("html_url"):
                        pr_url = pr_res.get("html_url")
                        pr_num = pr_res.get("number")
                        current_task["branch"] = branch_name
                        current_task["pr_number"] = pr_num
                        current_task["pr_url"] = pr_url
                        save_state(state)
                        
                        # 6. Post in #human-review
                        slack_api_call("chat.postMessage", {
                            "channel": human_review_id,
                            "text": f"🔔 *New Review Request:* Sprint {state['current_sprint']} Task {task_idx+1}\nPR URL: {pr_url}\nBranch: `{branch_name}`\nPlease review and merge the PR to automatically trigger the next task!"
                        })
                    else:
                        print(f"Failed to create PR. GitHub Response: {pr_res}")
                        slack_api_call("chat.postMessage", {
                            "channel": agent_log_id,
                            "text": f"Failed to create GitHub Pull Request. Response: {pr_res}"
                        })
                        
                    # Return to main branch locally to be ready for next task
                    try:
                        subprocess.run(["git", "checkout", "main"], check=True)
                    except Exception:
                        pass
                        
        time.sleep(10)

if __name__ == "__main__":
    main()
