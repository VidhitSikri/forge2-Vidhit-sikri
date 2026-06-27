<?php

namespace App\Http\Controllers;

use App\Models\Ticket;
use App\Models\User;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Gate;

class TicketController extends Controller
{
    public function index(Request $request)
    {
        $query = Ticket::query()
            ->with(['requester', 'assignee', 'categories'])
            ->forUser($request->user());

        if ($request->has('status')) {
            $query->status($request->status);
        }

        if ($request->has('priority')) {
            $query->priority($request->priority);
        }

        if ($request->has('assignee_id')) {
            $query->assignedTo($request->assignee_id);
        }

        if ($request->has('search')) {
            $search = $request->search;
            $query->where(function ($q) use ($search) {
                $q->where('subject', 'like', "%{$search}%")
                  ->orWhere('description', 'like', "%{$search}%");
            });
        }

        $tickets = $query->latest()->paginate(20);

        return response()->json($tickets);
    }

    public function store(Request $request)
    {
        $validated = $request->validate([
            'subject' => 'required|string|max:255',
            'description' => 'required|string',
            'priority' => 'required|in:low,medium,high,urgent',
            'assignee_id' => 'nullable|exists:users,id',
            'category_ids' => 'nullable|array',
            'category_ids.*' => 'exists:categories,id',
        ]);

        $ticket = Ticket::create([
            'subject' => $validated['subject'],
            'description' => $validated['description'],
            'priority' => $validated['priority'],
            'requester_id' => $request->user()->id,
            'assignee_id' => $validated['assignee_id'] ?? null,
            'status' => 'open',
        ]);

        if (isset($validated['category_ids'])) {
            $ticket->categories()->sync($validated['category_ids']);
        }

        return response()->json($ticket->load(['requester', 'assignee', 'categories']), 201);
    }

    public function show(Request $request, Ticket $ticket)
    {
        $user = $request->user();
        
        if ($user->isCustomer() && $ticket->requester_id !== $user->id) {
            abort(403, 'Unauthorized access to this ticket.');
        }

        $ticket->load([
            'requester',
            'assignee',
            'categories',
            'comments' => function ($query) use ($user) {
                $query->visibleTo($user)->with('author')->latest();
            }
        ]);

        return response()->json($ticket);
    }

    public function update(Request $request, Ticket $ticket)
    {
        $user = $request->user();

        if (!$user->canManageTickets()) {
            abort(403, 'Only agents and admins can update tickets.');
        }

        $validated = $request->validate([
            'subject' => 'sometimes|string|max:255',
            'description' => 'sometimes|string',
            'status' => 'sometimes|in:open,pending,resolved,closed',
            'priority' => 'sometimes|in:low,medium,high,urgent',
            'assignee_id' => 'nullable|exists:users,id',
            'category_ids' => 'nullable|array',
            'category_ids.*' => 'exists:categories,id',
        ]);

        $ticket->update($validated);

        if (isset($validated['category_ids'])) {
            $ticket->categories()->sync($validated['category_ids']);
        }

        return response()->json($ticket->load(['requester', 'assignee', 'categories']));
    }

    public function destroy(Request $request, Ticket $ticket)
    {
        if (!$request->user()->isAdmin()) {
            abort(403, 'Only admins can delete tickets.');
        }

        $ticket->delete();

        return response()->json([
            'message' => 'Ticket deleted successfully'
        ]);
    }
}
