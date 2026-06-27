<?php

namespace App\Http\Controllers;

use App\Models\User;
use Illuminate\Http\Request;

class UserController extends Controller
{
    public function index(Request $request)
    {
        $users = User::query()
            ->where('organization_id', $request->user()->organization_id)
            ->select('id', 'name', 'email', 'role', 'avatar')
            ->get();

        return response()->json($users);
    }

    public function agents(Request $request)
    {
        $agents = User::query()
            ->where('organization_id', $request->user()->organization_id)
            ->whereIn('role', ['admin', 'agent'])
            ->select('id', 'name', 'email', 'role', 'avatar')
            ->get();

        return response()->json($agents);
    }
}
