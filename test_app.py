

import time
import pytest
from playwright.sync_api import Page, expect

BASE_URL = "http://127.0.0.1:5000"

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"
TEST_PASSWORD = "TestPass123!"


def unique_username(prefix: str) -> str:

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
    page.get_by_role("button", name="submit").click()



def register_and_login(page: Page, role: str) -> str:
    username = unique_username(role)
    register(page, username, TEST_PASSWORD, role)
    login(page, username, TEST_PASSWORD)
    return username

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


