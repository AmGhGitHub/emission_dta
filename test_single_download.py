#!/usr/bin/env python3
"""
Simple test script to debug the CSV download process for a single company
"""

import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


def test_download():
    url = "https://pollution-waste.canada.ca/national-release-inventory/?fromYear=2024&toYear=2024&name=Spur%20Petroleum%20Ltd&direction=ascending&order=NPRI_Id&length=10&page=1"

    download_path = Path("downloads").absolute()
    download_path.mkdir(exist_ok=True)

    chrome_options = Options()
    # Run in visible mode for debugging
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_experimental_option(
        "prefs",
        {
            "download.default_directory": str(download_path),
            "download.prompt_for_download": False,
        },
    )

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        print(f"🌐 Navigating to: {url}")
        driver.get(url)

        # Wait for page to load
        wait = WebDriverWait(driver, 20)
        time.sleep(5)  # Give extra time for content to load

        print("📊 Page loaded, looking for download options...")

        # Take a screenshot for debugging
        driver.save_screenshot(str(download_path / "page_screenshot.png"))
        print("📸 Screenshot saved")

        # Look for all possible download elements
        possible_download_elements = driver.find_elements(
            By.XPATH,
            "//*[contains(text(), 'Download') or contains(text(), 'CSV') or contains(text(), 'Export')]",
        )

        print(f"Found {len(possible_download_elements)} potential download elements:")
        for i, element in enumerate(possible_download_elements):
            try:
                text = element.text.strip()
                tag = element.tag_name
                classes = element.get_attribute("class")
                href = element.get_attribute("href")
                print(
                    f"  {i+1}. Tag: {tag}, Text: '{text}', Classes: '{classes}', Href: '{href}'"
                )
            except Exception as e:
                print(f"  {i+1}. Error getting element info: {e}")

        # Try to click the first viable download element
        for element in possible_download_elements:
            try:
                text = element.text.strip().lower()
                if "download" in text or "csv" in text:
                    print(f"🖱️ Attempting to click element with text: '{element.text}'")

                    # Scroll to element
                    driver.execute_script("arguments[0].scrollIntoView(true);", element)
                    time.sleep(2)

                    # Try to click
                    element.click()
                    print("✅ Clicked successfully!")

                    # Wait for download
                    print("⏳ Waiting for download...")
                    time.sleep(10)

                    # Check if any files were downloaded
                    files = list(download_path.glob("*"))
                    csv_files = [f for f in files if f.suffix.lower() == ".csv"]

                    if csv_files:
                        print(f"✅ Downloaded file: {csv_files[0]}")
                        return True
                    else:
                        print("❌ No CSV files found after click")
                        continue

            except Exception as e:
                print(f"❌ Failed to click element: {e}")
                continue

        print("❌ No successful downloads")
        return False

    finally:
        input("Press Enter to close browser...")  # Keep browser open for inspection
        driver.quit()


if __name__ == "__main__":
    test_download()
