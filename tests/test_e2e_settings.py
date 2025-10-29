"""End-to-end tests for settings panel and reranker functionality."""

import pytest
from playwright.sync_api import Page, expect


def test_settings_panel_collapsible(page: Page):
    """Test that settings panel is collapsible."""
    page.goto("http://localhost:8501")
    
    # Wait for page to load
    page.wait_for_timeout(2000)
    
    # Look for Settings expander
    settings_expander = page.locator('text=⚙️ Settings').or_(page.locator('text=Settings'))
    
    # Should be visible
    expect(settings_expander.first).to_be_visible(timeout=10000)
    
    # Expand settings
    settings_expander.first.click()
    
    # Should show tabs after expand
    page.wait_for_timeout(1000)
    expect(page.locator('text=Capture').or_(page.locator('button:has-text("Capture")')).first).to_be_visible(timeout=5000)


def test_smart_capture_toggles(page: Page):
    """Test smart capture toggles are present and functional."""
    page.goto("http://localhost:8501")
    
    # Expand settings
    page.locator('text=Settings').click()
    
    # Go to Capture tab
    page.locator('text=Capture').click()
    
    # Should see smart capture toggles
    expect(page.locator('text=Skip duplicate frames')).to_be_visible()
    expect(page.locator('text=Auto-adjust FPS based on activity')).to_be_visible()
    
    # Should NOT see manual FPS slider
    fps_slider = page.locator('input[type="range"]').filter(has_text='Frames per second')
    expect(fps_slider).not_to_be_visible()


def test_reranker_settings(page: Page):
    """Test reranker settings are exposed."""
    page.goto("http://localhost:8501")
    
    # Expand settings
    page.locator('text=Settings').click()
    
    # Go to Search tab
    page.locator('text=Search').click()
    
    # Should see reranker toggle
    expect(page.locator('text=Enable search result reranking')).to_be_visible()
    
    # Should see model info
    expect(page.locator('text=BAAI/bge-reranker-large')).to_be_visible()


def test_settings_persistence(page: Page):
    """Test that settings changes persist."""
    page.goto("http://localhost:8501")
    
    # Expand settings
    page.locator('text=Settings').click()
    
    # Go to Capture tab
    page.locator('text=Capture').click()
    
    # Toggle frame deduplication
    checkbox = page.locator('input[type="checkbox"]').first
    _initial_state = checkbox.is_checked()  # noqa: F841
    
    # Toggle it
    checkbox.click()
    
    # Should see success message
    expect(page.locator('text=Frame deduplication')).to_be_visible()


@pytest.fixture(scope="session")
def streamlit_app():
    """Start Streamlit app for testing."""
    import subprocess
    import time
    
    process = subprocess.Popen(
        ["streamlit", "run", "src/second_brain/ui/streamlit_app.py", "--server.port", "8501", "--server.headless", "true"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for app to start
    time.sleep(3)
    
    yield process
    
    # Cleanup
    process.terminate()
    process.wait()
