<?php

namespace Database\Seeders;

use App\Models\Category;
use App\Models\Comment;
use App\Models\Organization;
use App\Models\Ticket;
use App\Models\User;
use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\Hash;

class DatabaseSeeder extends Seeder
{
    public function run(): void
    {
        // Create Acme Corp
        $acme = Organization::create([
            'name' => 'Acme Corp',
            'slug' => 'acme-corp',
            'domain' => 'acme.test',
        ]);

        $acmeAdmin = User::create([
            'organization_id' => $acme->id,
            'name' => 'Admin User',
            'email' => 'admin@acme.test',
            'password' => Hash::make('password'),
            'role' => 'admin',
        ]);

        $acmeAgent = User::create([
            'organization_id' => $acme->id,
            'name' => 'Support Agent',
            'email' => 'agent@acme.test',
            'password' => Hash::make('password'),
            'role' => 'agent',
        ]);

        $acmeCustomer = User::create([
            'organization_id' => $acme->id,
            'name' => 'John Customer',
            'email' => 'customer@acme.test',
            'password' => Hash::make('password'),
            'role' => 'customer',
        ]);

        // Acme Categories
        $acmeBug = Category::create([
            'organization_id' => $acme->id,
            'name' => 'Bug',
            'color' => '#ef4444',
        ]);

        $acmeFeature = Category::create([
            'organization_id' => $acme->id,
            'name' => 'Feature Request',
            'color' => '#3b82f6',
        ]);

        $acmeSupport = Category::create([
            'organization_id' => $acme->id,
            'name' => 'Support',
            'color' => '#10b981',
        ]);

        // Acme Tickets
        $ticket1 = Ticket::create([
            'organization_id' => $acme->id,
            'subject' => 'Login page not loading',
            'description' => 'When I try to access the login page, it shows a blank screen.',
            'status' => 'open',
            'priority' => 'urgent',
            'requester_id' => $acmeCustomer->id,
            'assignee_id' => $acmeAgent->id,
        ]);
        $ticket1->categories()->attach($acmeBug);

        Comment::create([
            'ticket_id' => $ticket1->id,
            'author_id' => $acmeAgent->id,
            'body' => 'Thanks for reporting. I\'m looking into this now.',
            'is_internal' => false,
        ]);

        Comment::create([
            'ticket_id' => $ticket1->id,
            'author_id' => $acmeAgent->id,
            'body' => 'Found the issue - it\'s a caching problem on the frontend.',
            'is_internal' => true,
        ]);

        $ticket2 = Ticket::create([
            'organization_id' => $acme->id,
            'subject' => 'Add dark mode support',
            'description' => 'Would be great to have a dark mode option for the dashboard.',
            'status' => 'pending',
            'priority' => 'medium',
            'requester_id' => $acmeCustomer->id,
            'assignee_id' => $acmeAdmin->id,
        ]);
        $ticket2->categories()->attach($acmeFeature);

        $ticket3 = Ticket::create([
            'organization_id' => $acme->id,
            'subject' => 'How to export reports?',
            'description' => 'I need to know how to export monthly reports to CSV.',
            'status' => 'resolved',
            'priority' => 'low',
            'requester_id' => $acmeCustomer->id,
            'assignee_id' => $acmeAgent->id,
        ]);
        $ticket3->categories()->attach($acmeSupport);

        Comment::create([
            'ticket_id' => $ticket3->id,
            'author_id' => $acmeAgent->id,
            'body' => 'Go to Reports > Click the Export button in the top right. You can choose CSV or PDF format.',
            'is_internal' => false,
        ]);

        Comment::create([
            'ticket_id' => $ticket3->id,
            'author_id' => $acmeCustomer->id,
            'body' => 'Perfect! Thank you so much.',
            'is_internal' => false,
        ]);

        // Create TechCo Inc
        $techco = Organization::create([
            'name' => 'TechCo Inc',
            'slug' => 'techco-inc',
            'domain' => 'techco.test',
        ]);

        $techcoAdmin = User::create([
            'organization_id' => $techco->id,
            'name' => 'Sarah Admin',
            'email' => 'admin@techco.test',
            'password' => Hash::make('password'),
            'role' => 'admin',
        ]);

        $techcoAgent = User::create([
            'organization_id' => $techco->id,
            'name' => 'Mike Support',
            'email' => 'support@techco.test',
            'password' => Hash::make('password'),
            'role' => 'agent',
        ]);

        $techcoCustomer = User::create([
            'organization_id' => $techco->id,
            'name' => 'Jane Client',
            'email' => 'jane@client.test',
            'password' => Hash::make('password'),
            'role' => 'customer',
        ]);

        // TechCo Categories
        $techcoBilling = Category::create([
            'organization_id' => $techco->id,
            'name' => 'Billing',
            'color' => '#f59e0b',
        ]);

        $techcoTechnical = Category::create([
            'organization_id' => $techco->id,
            'name' => 'Technical',
            'color' => '#8b5cf6',
        ]);

        // TechCo Tickets
        $ticket4 = Ticket::create([
            'organization_id' => $techco->id,
            'subject' => 'API rate limit reached',
            'description' => 'Our application is hitting the API rate limit. Can we increase it?',
            'status' => 'open',
            'priority' => 'high',
            'requester_id' => $techcoCustomer->id,
            'assignee_id' => $techcoAgent->id,
        ]);
        $ticket4->categories()->attach($techcoTechnical);

        $ticket5 = Ticket::create([
            'organization_id' => $techco->id,
            'subject' => 'Invoice inquiry',
            'description' => 'I didn\'t receive the invoice for last month.',
            'status' => 'closed',
            'priority' => 'medium',
            'requester_id' => $techcoCustomer->id,
            'assignee_id' => $techcoAdmin->id,
        ]);
        $ticket5->categories()->attach($techcoBilling);

        Comment::create([
            'ticket_id' => $ticket5->id,
            'author_id' => $techcoAdmin->id,
            'body' => 'I\'ve resent the invoice to your email. Please check your spam folder as well.',
            'is_internal' => false,
        ]);
    }
}
