# Architecture -- PulseDesk

## Multi-tenancy approach
Every database record is scoped to an `organization_id`. The tenant context is derived from the authenticated user's organization (via `auth()->user()->organization_id`), never from client-supplied parameters.

**Implementation:**
- **Global Scope:** `TenantScope` automatically filters all queries to the current user's organization
- **Middleware:** `EnsureTenantContext` validates tenant access on every request
- **Policies:** Authorization checks verify organization ownership before any action
- **Model Trait:** `BelongsToTenant` trait applied to all tenant-scoped models

## Data model
- **Organization** (tenant): `id`, `name`, `slug`, `domain`, `settings`, `timestamps`
- **User** (belongs_to Organization): `id`, `organization_id`, `name`, `email`, `password`, `role` (admin|agent|customer), `avatar`, `timestamps`
- **Ticket**: `id`, `organization_id`, `subject`, `description`, `status` (open|pending|resolved|closed), `priority` (low|medium|high|urgent), `requester_id`, `assignee_id`, `timestamps`
- **Comment**: `id`, `ticket_id`, `author_id`, `body`, `is_internal` (boolean), `timestamps`
- **Category**: `id`, `organization_id`, `name`, `color`, `timestamps`
- **TicketCategory**: `ticket_id`, `category_id` (pivot)

## API routes (routes/api.php)
| Method | Path | Auth | Notes |
| --- | --- | --- | --- |
| POST | /api/register | - | Creates org + admin user |
| POST | /api/login | - | Returns Sanctum token |
| POST | /api/logout | ✓ | Revokes token |
| GET | /api/user | ✓ | Current user + org |
| GET | /api/tickets | ✓ | Tenant-scoped, filterable by status/priority/assignee |
| POST | /api/tickets | ✓ | Create ticket (customer/agent/admin) |
| GET | /api/tickets/{id} | ✓ | Show ticket with comments |
| PUT | /api/tickets/{id} | ✓ | Update ticket (agent/admin only) |
| DELETE | /api/tickets/{id} | ✓ | Delete ticket (admin only) |
| POST | /api/tickets/{id}/comments | ✓ | Add comment (public or internal) |
| GET | /api/users | ✓ | Org users (for assignment) |
| GET | /api/categories | ✓ | Org categories |
| POST | /api/categories | ✓ | Create category (admin only) |
| GET | /api/dashboard/stats | ✓ | Dashboard metrics |

## Key decisions
- **Multi-tenancy:** Global scope + middleware approach ensures complete data isolation
- **Authentication:** Laravel Sanctum for SPA token-based auth
- **Authorization:** Policies check both authentication AND tenant ownership
- **Roles:** Simple ENUM approach (admin/agent/customer) - admin can manage everything, agents handle tickets, customers can only see their own
- **Ticket visibility:** Customers see only their tickets, agents/admins see all org tickets
- **Internal notes:** Comments with `is_internal=true` hidden from customers
- **Frontend state:** React Context API for auth state, React Query for data fetching/caching
- **Styling:** Tailwind CSS with custom design system for consistent UI
- **Real-time:** Future enhancement - could add WebSockets/Pusher for live updates
