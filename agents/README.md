# Agents - Hermes & OpenClaw

This directory contains the agent configurations used to build PulseDesk through orchestration.

## Agent Roles

### Hermes (Product Owner / Orchestrator)
**Role:** Planning and coordination  
**Model:** `anthropic/claude-sonnet-4.5`  
**Responsibilities:**
- Receives sprint goals from human in #sprint-main
- Breaks down goals into executable tasks
- Assigns tasks to OpenClaw in #agent-coder
- Monitors PR status and triggers next tasks
- Tracks overall sprint progress

**Files:**
- `hermes/hermes.py` - Main orchestrator script
- `hermes/hermes-config.yaml` - Configuration (secrets redacted)

### OpenClaw (Software Engineer / Implementer)
**Role:** Feature implementation  
**Model:** `anthropic/claude-sonnet-4.5`  
**Responsibilities:**
- Receives task assignments from Hermes
- Implements complete features with working code
- Creates git branches and commits
- Runs CI/CD validation
- Creates GitHub Pull Requests
- Reports progress in #agent-log

**Files:**
- `openclaw/openclaw.py` - Main developer agent script
- `openclaw/openclaw.json` - Configuration (secrets redacted)

## Workflow

1. **Human** posts sprint goal mentioning @Hermes in #sprint-main
2. **Hermes** analyzes goal, breaks into tasks, posts plan
3. **Hermes** assigns first task to @OpenClaw in #agent-coder
4. **OpenClaw** implements feature, creates branch, runs tests
5. **OpenClaw** creates PR, posts in #human-review
6. **Human** reviews and merges PR
7. **Hermes** detects merge, triggers next task
8. **Repeat** steps 3-7 until sprint complete

## Communication Channels

- `#sprint-main` - Human posts goals, Hermes responds with plans
- `#agent-coder` - Hermes assigns tasks to OpenClaw
- `#agent-log` - OpenClaw posts implementation progress
- `#human-review` - OpenClaw posts PR links for review
- `#ci-cd` - CI/CD pipeline status updates

## Environment Variables (Example)

The agents require these environment variables (actual values redacted):

```bash
# Slack
SLACK_BOT_TOKEN=xoxb-***
SLACK_APP_TOKEN=xapp-***

# EastRouter (LLM Provider)
EASTROUTER_API_KEY=sk-er-***
EASTROUTER_BASE_URL=https://api.eastrouter.com/v1

# GitHub
GITHUB_TOKEN=ghp_***
GITHUB_REPO=username/repo-name
```

## State Management

Agents maintain state in `sprint_state.json` which tracks:
- Current sprint number
- Sprint goal
- List of tasks with status
- Current task index
- Last processed message timestamps
- Branch names and PR numbers

## PulseDesk Build Summary

**Sprint 01 (Backend):**
- Task 1: Database schema and migrations
- Task 2: Multi-tenancy infrastructure (traits, scopes, middleware)
- Task 3: Authentication API with Sanctum
- Task 4: Ticket CRUD API with authorization
- Task 5: Database seeder with demo data

**Sprint 02 (Frontend):**
- Task 6: React foundation with auth context
- Task 7: Login and register pages
- Task 8: Dashboard with statistics
- Task 9: Ticket list with filters
- Task 10: Ticket detail with comments
- Task 11: Create ticket modal

All tasks implemented by OpenClaw under Hermes coordination, reviewed and merged by human.
