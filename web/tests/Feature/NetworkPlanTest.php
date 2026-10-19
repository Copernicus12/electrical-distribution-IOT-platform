<?php

namespace Tests\Feature;

use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Inertia\Testing\AssertableInertia as Assert;
use Tests\TestCase;

class NetworkPlanTest extends TestCase
{
    use RefreshDatabase;

    public function test_guests_cannot_access_the_network_plan(): void
    {
        $this->get(route('network-plan'))->assertRedirect(route('login'));
    }

    public function test_unverified_users_must_verify_their_email(): void
    {
        $this->actingAs(User::factory()->unverified()->create())
            ->get(route('network-plan'))
            ->assertRedirect(route('verification.notice'));
    }

    public function test_verified_users_can_access_the_network_plan(): void
    {
        $this->withoutVite();

        $this->actingAs(User::factory()->create())
            ->get(route('network-plan'))
            ->assertOk()
            ->assertInertia(fn (Assert $page) => $page->component('NetworkPlan'));
    }
}
