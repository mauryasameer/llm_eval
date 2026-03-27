import subprocess
import os
import sys

# Install playwright quietly
print("Installing playwright...")
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "playwright"])
subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"])

from playwright.sync_api import sync_playwright

def take_screenshot():
    import glob
    reports = glob.glob("reports/validation_report_*.html")
    if not reports:
        print("No report found to screenshot!")
        return

    latest_report = max(reports, key=os.path.getctime)
    html_path = f"file://{os.path.abspath(latest_report)}"
    
    with sync_playwright() as p:
        browser = p.chromium.launch()
        # Set a nice desktop viewport
        page = browser.new_page(viewport={"width": 1400, "height": 1200})
        page.goto(html_path)
        # Scroll down slightly to show some of the table and the cards
        page.evaluate("window.scrollBy(0, 300)")
        page.screenshot(path="assets/sample_report.png")
        browser.close()
        print("✅ Screenshot saved to assets/sample_report.png")

if __name__ == "__main__":
    os.makedirs("assets", exist_ok=True)
    take_screenshot()
