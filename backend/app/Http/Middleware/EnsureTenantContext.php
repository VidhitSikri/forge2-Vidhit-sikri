<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Symfony\Component\HttpFoundation\Response;

class EnsureTenantContext
{
    public function handle(Request $request, Closure $next): Response
    {
        if (auth()->check() && !auth()->user()->organization_id) {
            return response()->json([
                'message' => 'User does not belong to an organization.'
            ], 403);
        }

        return $next($request);
    }
}
