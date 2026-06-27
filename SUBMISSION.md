# PulseDesk - Submission Documentation

## Project Overview
PulseDesk is a fully functional multi-tenant customer support ticketing SaaS platform built through agent orchestration (Hermes + OpenClaw). Multiple companies can independently manage support tickets with complete data isolation.

## Core Features Implemented

### Multi-Tenancy (Complete Data Isolation)
- Every record scoped to organization_id
- Tenant derived from authenticated user (never client-supplied)
- Global scope automatically filters all queries
- Middleware validates tenant context on every request
- Tested thoroughly - zero cross-tenant data leakage

### Authentication & Authorization
- Laravel Sanctum token-based authentication
- Registration creates organization + admin user atomically
- Role-based access control (admin, agent, customer)
- Customers can only view their own tickets
- Agents/admins can manage all tickets in their org
- Internal notes hidden from customers

### Ticket Management
- Full CRUD operations with proper authorization
- Status workflow (open → pending → resolved → closed)
- Priority levels (low, medium, high, urgent)
- Assignment to agents
- Categories for organization
- Soft deletes with admin-only restore capability

### Comments System
- Public comments visible to all
- Internal notes for agent collaboration (hidden from customers)
- Real-time-feeling updates via React Query
- Author tracking with timestamps

### Dashboard
- Organization-wide statistics
- Role-based metrics (agents see their assignments)
- Recent tickets overview
- Quick actions

### Frontend
- Modern React 19 SPA
- Responsive design (mobile-friendly)
- Protected routes
- Role-based UI rendering
- Clean, professional interface
- Optimistic updates for better UX

## Tech Stack
- **Backend:** Laravel 11, PHP 8.2, MySQL 8, Laravel Sanctum
- **Frontend:** React 19, Vite, Tailwind CSS, React Router, TanStack Query
- **Auth:** Token-based (Sanctum)
- **Styling:** Tailwind CSS with custom color system

## Demo Accounts
All passwords: `password`

**Acme Corp:**
- admin@acme.test (Admin)
- agent@acme.test (Agent)
- customer@acme.test (Customer)

**TechCo Inc:**
- admin@techco.test (Admin)
- support@techco.test (Agent)

## Setup Instructions

### Backend
```bash
cd backend
cp .env.example .env
# Configure DB_* settings for MySQL
composer install
php artisan key:generate
php artisan migrate --seed
php artisan serve  # http://127.0.0.1:8000
```

### Frontend
```bash
cd frontend
cp .env.example .env
# VITE_API_URL should be http://127.0.0.1:8000
npm install
npm run dev  # http://127.0.0.1:5173
```

## Agent Orchestration Evidence

### Process
1. Human defines sprint goals in Slack (#sprint-main)
2. Hermes plans and breaks down into issues
3. Hermes assigns issues to OpenClaw (#agent-coder)
4. OpenClaw implements features, reports progress
5. Human reviews, tests, and merges
6. Repeat for next sprint

### Documentation
- `agent-log.md` - Complete human→Hermes→OpenClaw interaction log
- `sprints/sprint-01.md` - Backend sprint details
- `sprints/sprint-02.md` - Frontend sprint details
- `ARCHITECTURE.md` - Technical decisions and data model
- `agents/hermes/` - Hermes agent configuration
- `agents/openclaw/` - OpenClaw agent configuration

### Sprint Breakdown
**Sprint 01 (Backend):** Database schema, multi-tenancy, auth API, ticket CRUD, seeder  
**Sprint 02 (Frontend):** React setup, auth UI, dashboard, ticket management, detail view

## Key Technical Decisions

### Multi-Tenancy Approach
Chose global scope + middleware pattern over separate databases because:
- Simpler deployment and maintenance
- Better resource utilization
- Easier to implement and test
- Adequate isolation with proper scoping

### Authentication
Laravel Sanctum for SPA auth because:
- Native Laravel integration
- Simple token-based approach
- Perfect for SPA architecture
- No OAuth complexity needed

### Frontend State Management
React Query instead of Redux because:
- Built-in caching and refetching
- Less boilerplate
- Server state management specialized
- Optimistic updates out of the box

### Database Design
Soft deletes on tickets allow:
- Accidental deletion recovery
- Audit trail preservation
- Admin-only restore capability

## Testing Performed
- Created multiple orgs, verified complete data isolation
- Tested all user roles (admin, agent, customer)
- Verified role-based permissions and UI
- Tested cross-tenant access attempts (properly blocked)
- Confirmed internal notes visibility rules
- Tested ticket lifecycle workflows
- Verified comment system with internal/public notes

## Production Readiness
- ✅ Complete data isolation verified
- ✅ Authentication and authorization working
- ✅ Error handling implemented
- ✅ Responsive design tested
- ✅ Role-based access control enforced
- ✅ Demo data seeded successfully

## Future Enhancements (Not Implemented)
- Real-time updates via WebSockets/Pusher
- Email notifications
- SLA policies and tracking
- Activity logs
- File attachments
- Ticket templates
- Custom fields
- Reporting and analytics
- API rate limiting
- Two-factor authentication

## Evidence Location
All evidence is in this repository:
- `/agents/` - Agent configurations (Hermes + OpenClaw)
- `/agent-log.md` - Complete interaction log
- `/sprints/` - Sprint documentation
- `/ARCHITECTURE.md` - Technical architecture
- `/README.md` - Setup instructions
- Frontend/Backend code demonstrates implementation

## Live Demo
Runs locally per setup instructions above. No external deployment required.

---

**Built by orchestrating Hermes (planning) + OpenClaw (coding) via Slack**  
**June 20-27, 2026**
