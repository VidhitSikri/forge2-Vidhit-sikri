<?php

namespace App\Http\Controllers;

use App\Models\Category;
use Illuminate\Http\Request;

class CategoryController extends Controller
{
    public function index(Request $request)
    {
        $categories = Category::query()
            ->where('organization_id', $request->user()->organization_id)
            ->get();

        return response()->json($categories);
    }

    public function store(Request $request)
    {
        if (!$request->user()->isAdmin()) {
            abort(403, 'Only admins can create categories.');
        }

        $validated = $request->validate([
            'name' => 'required|string|max:255',
            'color' => 'required|string|max:7',
        ]);

        $category = Category::create($validated);

        return response()->json($category, 201);
    }
}
