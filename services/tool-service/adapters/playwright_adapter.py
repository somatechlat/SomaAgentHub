"""
⚠️ WE DO NOT MOCK - Real Playwright UI automation adapter.

Automates web UIs for tools without APIs:
- Browser automation (Chrome, Firefox, WebKit)
- Form filling and submission
- Navigation and clicking
- Screenshot capture
- Data extraction
- Headless and headed modes
"""

from playwright.sync_api import sync_playwright, Browser, Page, BrowserContext
from typing import Dict, List, Any, Optional, Callable
import logging
import time

logger = logging.getLogger(__name__)


class PlaywrightAdapter:
    """
    Adapter for Playwright browser automation.
    
    Playwright Documentation: https://playwright.dev/python
    """
    
    def __init__(
        self,
        browser_type: str = "chromium",  # chromium, firefox, webkit
        headless: bool = True,
        slow_mo: int = 0  # Slow down operations (ms)
    ):
        """
        Initialize Playwright adapter.
        
        Args:
            browser_type: Browser to use
            headless: Run in headless mode
            slow_mo: Slow down operations (useful for debugging)
        """
        self.browser_type = browser_type
        self.headless = headless
        self.slow_mo = slow_mo
        
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
    
    def start(self) -> None:
        """Start browser."""
        logger.info(f"Starting {self.browser_type} browser (headless={self.headless})")
        
        self.playwright = sync_playwright().start()
        
        # Select browser
        if self.browser_type == "chromium":
            browser_launcher = self.playwright.chromium
        elif self.browser_type == "firefox":
            browser_launcher = self.playwright.firefox
        elif self.browser_type == "webkit":
            browser_launcher = self.playwright.webkit
        else:
            raise ValueError(f"Invalid browser type: {self.browser_type}")
        
        # Launch browser
        self.browser = browser_launcher.launch(
            headless=self.headless,
            slow_mo=self.slow_mo
        )
        
        # Create context and page
        self.context = self.browser.new_context()
        self.page = self.context.new_page()
    
    def stop(self) -> None:
        """Stop browser."""
        logger.info("Stopping browser")
        
        if self.page:
            self.page.close()
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
    
    # Navigation
    
    def goto(self, url: str, wait_until: str = "load") -> None:
        """
        Navigate to URL.
        
        Args:
            url: Target URL
            wait_until: When to consider navigation complete
                       (load, domcontentloaded, networkidle)
        """
        logger.info(f"Navigating to: {url}")
        self.page.goto(url, wait_until=wait_until)
    
    def go_back(self) -> None:
        """Go back in history."""
        self.page.go_back()
    
    def reload(self) -> None:
        """Reload current page."""
        self.page.reload()
    
    # Interaction
    
    def click(self, selector: str, timeout: int = 30000) -> None:
        """
        Click element.
        
        Args:
            selector: CSS/XPath selector
            timeout: Timeout in milliseconds
        """
        logger.info(f"Clicking: {selector}")
        self.page.click(selector, timeout=timeout)
    
    def fill(self, selector: str, value: str, timeout: int = 30000) -> None:
        """
        Fill input field.
        
        Args:
            selector: CSS/XPath selector
            value: Value to fill
            timeout: Timeout in milliseconds
        """
        logger.info(f"Filling {selector} with: {value}")
        self.page.fill(selector, value, timeout=timeout)
    
    def type(self, selector: str, text: str, delay: int = 0) -> None:
        """
        Type text (simulates keyboard).
        
        Args:
            selector: CSS/XPath selector
            text: Text to type
            delay: Delay between keystrokes (ms)
        """
        logger.info(f"Typing into {selector}")
        self.page.type(selector, text, delay=delay)
    
    def select_option(
        self,
        selector: str,
        value: Optional[str] = None,
        label: Optional[str] = None
    ) -> None:
        """
        Select dropdown option.
        
        Args:
            selector: Select element selector
            value: Option value
            label: Option label
        """
        if value:
            self.page.select_option(selector, value=value)
        elif label:
            self.page.select_option(selector, label=label)
    
    def check(self, selector: str) -> None:
        """Check checkbox/radio."""
        self.page.check(selector)
    
    def uncheck(self, selector: str) -> None:
        """Uncheck checkbox."""
        self.page.uncheck(selector)
    
    def press(self, selector: str, key: str) -> None:
        """
        Press keyboard key.
        
        Args:
            selector: Element selector
            key: Key to press (Enter, Tab, etc.)
        """
        self.page.press(selector, key)
    
    # Waiting
    
    def wait_for_selector(
        self,
        selector: str,
        state: str = "visible",
        timeout: int = 30000
    ) -> None:
        """
        Wait for element.
        
        Args:
            selector: CSS/XPath selector
            state: Element state (visible, hidden, attached, detached)
            timeout: Timeout in milliseconds
        """
        logger.info(f"Waiting for: {selector}")
        self.page.wait_for_selector(selector, state=state, timeout=timeout)
    
    def wait_for_url(self, url: str, timeout: int = 30000) -> None:
        """Wait for URL."""
        self.page.wait_for_url(url, timeout=timeout)
    
    def wait_for_timeout(self, timeout: int) -> None:
        """Wait for fixed timeout (ms)."""
        self.page.wait_for_timeout(timeout)
    
    # Data Extraction
    
    def get_text(self, selector: str) -> str:
        """Get element text content."""
        return self.page.text_content(selector) or ""
    
    def get_value(self, selector: str) -> str:
        """Get input value."""
        return self.page.input_value(selector)
    
    def get_attribute(self, selector: str, attribute: str) -> Optional[str]:
        """Get element attribute."""
        return self.page.get_attribute(selector, attribute)
    
    def get_all_text(self, selector: str) -> List[str]:
        """Get text from all matching elements."""
        elements = self.page.query_selector_all(selector)
        return [el.text_content() or "" for el in elements]
    
    def evaluate(self, expression: str) -> Any:
        """Execute JavaScript and return result."""
        return self.page.evaluate(expression)
    
    # Screenshots
    
    def screenshot(
        self,
        path: Optional[str] = None,
        full_page: bool = False
    ) -> bytes:
        """
        Take screenshot.
        
        Args:
            path: Save to file path
            full_page: Capture full scrollable page
            
        Returns:
            Screenshot bytes
        """
        logger.info(f"Taking screenshot: {path or 'in-memory'}")
        
        kwargs = {"full_page": full_page}
        if path:
            kwargs["path"] = path
        
        return self.page.screenshot(**kwargs)
    
    def screenshot_element(self, selector: str, path: Optional[str] = None) -> bytes:
        """Screenshot specific element."""
        element = self.page.query_selector(selector)
        
        kwargs = {}
        if path:
            kwargs["path"] = path
        
        return element.screenshot(**kwargs)
    
    # Authentication
    
    def login(
        self,
        url: str,
        username_selector: str,
        password_selector: str,
        submit_selector: str,
        username: str,
        password: str,
        post_login_selector: Optional[str] = None
    ) -> None:
        """
        Perform login.
        
        Args:
            url: Login page URL
            username_selector: Username input selector
            password_selector: Password input selector
            submit_selector: Submit button selector
            username: Username value
            password: Password value
            post_login_selector: Element to wait for after login
        """
        logger.info(f"Logging in to: {url}")
        
        # Navigate to login page
        self.goto(url)
        
        # Fill credentials
        self.fill(username_selector, username)
        self.fill(password_selector, password)
        
        # Submit
        self.click(submit_selector)
        
        # Wait for redirect/element
        if post_login_selector:
            self.wait_for_selector(post_login_selector)
        else:
            self.wait_for_timeout(2000)  # Default wait
    
    # Utility Methods
    
    def fill_form(self, form_data: Dict[str, str]) -> None:
        """
        Fill multiple form fields.
        
        Args:
            form_data: Dict of {selector: value}
        """
        logger.info("Filling form")
        
        for selector, value in form_data.items():
            self.fill(selector, value)
    
    def extract_table(self, table_selector: str) -> List[List[str]]:
        """
        Extract data from HTML table.
        
        Args:
            table_selector: Table element selector
            
        Returns:
            2D array of cell values
        """
        logger.info(f"Extracting table: {table_selector}")
        
        # JavaScript to extract table data
        script = f"""
        const table = document.querySelector('{table_selector}');
        const rows = Array.from(table.querySelectorAll('tr'));
        return rows.map(row => {{
            const cells = Array.from(row.querySelectorAll('td, th'));
            return cells.map(cell => cell.textContent.trim());
        }});
        """
        
        return self.evaluate(script)
    
    def automate_workflow(
        self,
        url: str,
        steps: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Execute automated workflow.
        
        Args:
            url: Starting URL
            steps: List of step configurations
            
        Returns:
            Workflow results
        """
        logger.info(f"Executing workflow: {len(steps)} steps")
        
        self.goto(url)
        results = {"steps": [], "screenshots": []}
        
        for i, step in enumerate(steps):
            logger.info(f"Step {i + 1}/{len(steps)}: {step.get('action')}")
            
            action = step.get("action")
            
            if action == "click":
                self.click(step["selector"])
            elif action == "fill":
                self.fill(step["selector"], step["value"])
            elif action == "wait":
                self.wait_for_selector(step["selector"])
            elif action == "extract":
                text = self.get_text(step["selector"])
                results["steps"].append({
                    "step": i + 1,
                    "action": "extract",
                    "data": text
                })
            elif action == "screenshot":
                screenshot = self.screenshot()
                results["screenshots"].append({
                    "step": i + 1,
                    "data": screenshot
                })
            
            # Optional wait between steps
            if step.get("wait_ms"):
                self.wait_for_timeout(step["wait_ms"])
        
        return results


# Example usage
if __name__ == "__main__":
    # Example: Automate form submission
    with PlaywrightAdapter(headless=False) as browser:
        browser.goto("https://example.com/form")
        
        browser.fill_form({
            "#name": "John Doe",
            "#email": "john@example.com",
            "#message": "Hello from SomaGent!"
        })
        
        browser.click("button[type='submit']")
        browser.wait_for_selector(".success-message")
        
        success_msg = browser.get_text(".success-message")
        print(f"✅ {success_msg}")
