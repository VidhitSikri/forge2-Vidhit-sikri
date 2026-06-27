# PulseDesk -- Forge 2 / Edition 1

A multi-tenant customer support ticketing SaaS, BUILT BY ORCHESTRATING Hermes + OpenClaw over Slack.
Companies can create/manage support tickets, assign agents, reply to customers, and track ticket status—while each company can only access its own data.

## Stack (required)
Laravel 11 . PHP 8.2 . MySQL 8 . Laravel Sanctum . React 19 . Vite . Tailwind

## EastRouter models I used
- Hermes (planning / product owner): anthropic/claude-sonnet-4.5
- OpenClaw (coding): anthropic/claude-sonnet-4.5

## How to run  (EXACT -- a judge will run these from a fresh clone)
### Backend (Laravel + MySQL)
    cd backend
    cp .env.example .env          # set DB_* for your MySQL
    composer install
    php artisan key:generate
    php artisan migrate --seed
    php artisan serve             # http://127.0.0.1:8000
### Frontend (React + Vite)
    cd frontend
    cp .env.example .env          # set VITE_API_URL=http://127.0.0.1:8000
    npm install
    npm run dev                   # http://127.0.0.1:5173

## Demo logins (from the seeder)
- admin@acme.test / password (Admin - Acme Corp)
- agent@acme.test / password (Agent - Acme Corp)
- customer@acme.test / password (Customer - Acme Corp)
- admin@techco.test / password (Admin - TechCo Inc)
- support@techco.test / password (Agent - TechCo Inc)

## Live URL
<paste if deployed, else: "runs locally per the steps above">

## Where my evidence lives (everything is in THIS repo -- no Drive, no video)
- agents/        -- real Hermes + OpenClaw configs (secrets redacted)
- agent-log.md   -- the human->Hermes->OpenClaw loop
- sprints/       -- one doc per sprint
- slack-export/  -- Slack export, or per-channel screenshots
- evidence/screenshots/ -- app, agents-running, CI screenshots
