

import time
import pytest
from playwright.sync_api import Page, expect

BASE_URL = "http://127.0.0.1:5000"

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"
TEST_PASSWORD = "TestPass123!"


def unique_username(prefix: str) -> str:
    """Avoid username collisions across test runs / CI re-runs."""
    return f"{prefix}_{int(time.time() * 1000)}"


def login(page: Page, username: str, password: str):
    page.goto(f"{BASE_URL}/login")
    page.fill("input[name='username']", username)
    page.fill("input[name='password']", password)
    page.click("button:has-text('Login')")


def register(page: Page, username: str, password: str, role: str):
    page.goto(f"{BASE_URL}/register")
    page.fill("input[name='username']", username)
    page.fill("input[name='password']", password)
    page.select_option("select[name='role']", role)
    page.click("button:has-text('Create Account')")


def register_and_login(page: Page, role: str) -> str:
    """Registers a fresh user with the given role, then logs in as them."""
    username = unique_username(role)
    register(page, username, TEST_PASSWORD, role)
    login(page, username, TEST_PASSWORD)
    return username


# ---------------------------------------------------------------------------
# Basic smoke tests
# ---------------------------------------------------------------------------

def test_home_page_loads(page: Page):
    page.goto(BASE_URL)
    assert page.title() != ""


def test_login_page_renders(page: Page):
    page.goto(f"{BASE_URL}/login")
    expect(page.locator("input[name='username']")).to_be_visible()
    expect(page.locator("input[name='password']")).to_be_visible()
    expect(page.locator("button:has-text('Login')")).to_be_visible()


def test_register_link_present(page: Page):
    page.goto(f"{BASE_URL}/login")
    expect(page.locator("a:has-text('Register')")).to_be_visible()


# ---------------------------------------------------------------------------
# Auth flow
# ---------------------------------------------------------------------------

def test_login_with_valid_admin_credentials(page: Page):
    login(page, ADMIN_USERNAME, ADMIN_PASSWORD)
    expect(page).not_to_have_url(f"{BASE_URL}/login")
    expect(page.get_by_text(
        f"Welcome, {ADMIN_USERNAME}! Role: admin")).to_be_visible()


def test_login_with_invalid_credentials_stays_on_login(page: Page):
    login(page, "wrong_user", "wrong_password")
    expect(page).to_have_url(f"{BASE_URL}/login")
    expect(page.get_by_text("Invalid username or password.")).to_be_visible()


def test_register_new_viewer_and_login(page: Page):
    username = unique_username("viewer")
    register(page, username, TEST_PASSWORD, "viewer")
    # Successful registration redirects to /login with a confirmation flash
    expect(page).to_have_url(f"{BASE_URL}/login")
    expect(page.get_by_text("Account created. Please login.")).to_be_visible()

    login(page, username, TEST_PASSWORD)
    expect(page.get_by_text(
        f"Welcome, {username}! Role: viewer")).to_be_visible()


def test_logout_redirects_to_login(page: Page):
    login(page, ADMIN_USERNAME, ADMIN_PASSWORD)
    page.goto(f"{BASE_URL}/logout")
    expect(page).to_have_url(f"{BASE_URL}/login")


# ---------------------------------------------------------------------------
# RBAC: /users is admin-only
# ---------------------------------------------------------------------------

def test_admin_can_access_users_page(page: Page):
    login(page, ADMIN_USERNAME, ADMIN_PASSWORD)
    page.goto(f"{BASE_URL}/users")
    expect(page).to_have_url(f"{BASE_URL}/users")
    expect(page.get_by_text("Access denied.")).not_to_be_visible()


@pytest.mark.parametrize("role", ["viewer", "analyst"])
def test_non_admin_cannot_access_users_page(page: Page, role):
    register_and_login(page, role)
    page.goto(f"{BASE_URL}/users")
    # Non-admins get bounced back with an "Access denied." flash
    expect(page).not_to_have_url(f"{BASE_URL}/users")
    expect(page.get_by_text("Access denied.")).to_be_visible()
