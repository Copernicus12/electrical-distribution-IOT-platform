<?php

namespace Tests\Feature;

use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\Gate;
use Tests\TestCase;

class AdminAuthorizationTest extends TestCase
{
    use RefreshDatabase;

    public function test_admin_has_access_even_when_a_gate_would_deny_it(): void
    {
        $admin = User::factory()->create();
        $admin->forceFill(['is_admin' => true])->save();

        Gate::define('manage-test-resource', fn (User $user): bool => false);

        $this->assertTrue(Gate::forUser($admin)->allows('access-admin'));
        $this->assertTrue(Gate::forUser($admin)->allows('manage-test-resource'));

        $this->actingAs($admin)->get(route('dashboard'))->assertOk();
    }

    public function test_regular_users_keep_their_normal_permissions(): void
    {
        $user = User::factory()->create();

        Gate::define('manage-test-resource', fn (User $user): bool => false);
        Gate::define('view-test-resource', fn (User $user): bool => true);

        $this->assertFalse($user->fresh()->is_admin);
        $this->assertFalse(Gate::forUser($user)->allows('access-admin'));
        $this->assertFalse(Gate::forUser($user)->allows('manage-test-resource'));
        $this->assertTrue(Gate::forUser($user)->allows('view-test-resource'));
    }

    public function test_registration_cannot_grant_admin_privileges(): void
    {
        $this->post(route('register.store'), [
            'name' => 'Regular User',
            'email' => 'regular@example.com',
            'password' => 'test-password',
            'password_confirmation' => 'test-password',
            'is_admin' => true,
        ])->assertSessionHasNoErrors();

        $user = User::where('email', 'regular@example.com')->firstOrFail();

        $this->assertFalse($user->is_admin);
        $this->assertFalse($user->isFillable('is_admin'));
    }
}
