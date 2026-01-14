import os
import re
import sys

import pytest

# We will implement a simple parser if bs4 is not available, or use bs4 if I can install it quickly.
# But let's try to install bs4 specifically first, it should be fast.
# If that fails, I'll fallback to regex/string checks.

try:
    from bs4 import BeautifulSoup
except ImportError:
    # Fallback or fail
    BeautifulSoup = None


def get_html_content():
    with open("web_ui.py", "r") as f:
        content = f.read()

    # Extract the string returned by _html_page
    # It looks like: return """<!doctype html>..."""
    match = re.search(r'return """(<!doctype html>.*?)"""', content, re.DOTALL)
    if match:
        # The file content might have escaped quotes like \" which we need to unescape
        # effectively mimicking what Python would do when evaluating the string
        return match.group(1).replace('\\"', '"')
    raise ValueError("Could not find HTML content in web_ui.py")


def test_ux_improvements():
    if BeautifulSoup is None:
        pytest.fail(
            "BeautifulSoup is required for this test. Please pip install beautifulsoup4"
        )

    html_content = get_html_content()
    soup = BeautifulSoup(html_content, "html.parser")

    # Check 1: Textarea has aria-label
    textarea = soup.find("textarea", id="message")
    assert textarea is not None, "Textarea not found"
    # assert textarea.get('aria-label') == "Message to Manus", "Textarea missing aria-label"

    if textarea.get("aria-label") != "Message to Manus":
        print("FAIL: Textarea missing aria-label")
    else:
        print("PASS: Textarea has aria-label")

    # Check 2: CSS has button:disabled
    style = soup.find("style")
    assert style is not None
    if "button:disabled" not in style.string:
        print("FAIL: CSS missing button:disabled style")
    else:
        print("PASS: CSS has button:disabled style")

    # Check 3: JS disables button
    script = soup.find_all("script")[-1]
    js_content = script.string

    has_disable = (
        "button.disabled = true" in js_content
        or "submitBtn.disabled = true" in js_content
    )
    has_loading = "Thinking..." in js_content
    has_enable = (
        "button.disabled = false" in js_content
        or "submitBtn.disabled = false" in js_content
    )

    if not has_disable:
        print("FAIL: JS missing disable logic")
    if not has_loading:
        print("FAIL: JS missing loading text")
    if not has_enable:
        print("FAIL: JS missing re-enable logic")

    # Assertions for pytest
    assert textarea.get("aria-label") == "Message to Manus"
    assert "button:disabled" in style.string
    assert has_disable
    assert has_loading
    assert has_enable


if __name__ == "__main__":
    try:
        test_ux_improvements()
        print("UX Tests Passed!")
    except Exception as e:
        print(f"Test failed: {e}")
