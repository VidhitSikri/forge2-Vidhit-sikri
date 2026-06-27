<?php

namespace App\Http\Controllers;

use App\Models\Ticket;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;

class DashboardController extends Controller
{
    public function stats(Request $request)
    {
        $user = $request->user();
        
        $query = Ticket::query()->forUser($user);

        $stats = [
            'total' => (clone $query)->count(),
            'open' => (clone $query)->where('status', 'open')->count(),
            'pending' => (clone $query)->where('status', 'pending')->count(),
            'resolved' => (clone $query)->where('status', 'resolved')->count(),
            'closed' => (clone $query)->where('status', 'closed')->count(),
        ];

        if ($user->canManageTickets()) {
            $stats['my_assigned'] = (clone $query)->where('assignee_id', $user->id)->count();
            $stats['unassigned'] = (clone $query)->whereNull('assignee_id')->count();
        }

        $recentTickets = (clone $query)
            ->with(['requester', 'assignee'])
            ->latest()
            ->limit(5)
            ->get();

        return response()->json([
            'stats' => $stats,
            'recent_tickets' => $recentTickets,
        ]);
    }
}
