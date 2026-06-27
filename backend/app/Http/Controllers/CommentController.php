<?php

namespace App\Http\Controllers;

use App\Models\Comment;
use App\Models\Ticket;
use Illuminate\Http\Request;

class CommentController extends Controller
{
    public function store(Request $request, Ticket $ticket)
    {
        $user = $request->user();

        if ($user->isCustomer() && $ticket->requester_id !== $user->id) {
            abort(403, 'Unauthorized access to this ticket.');
        }

        $validated = $request->validate([
            'body' => 'required|string',
            'is_internal' => 'boolean',
        ]);

        if (isset($validated['is_internal']) && $validated['is_internal'] && $user->isCustomer()) {
            abort(403, 'Customers cannot create internal notes.');
        }

        $comment = Comment::create([
            'ticket_id' => $ticket->id,
            'author_id' => $user->id,
            'body' => $validated['body'],
            'is_internal' => $validated['is_internal'] ?? false,
        ]);

        return response()->json($comment->load('author'), 201);
    }
}
