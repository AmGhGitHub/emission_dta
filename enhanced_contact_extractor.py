#!/usr/bin/env python3
"""
Enhanced contact information extractor with better regex patterns
"""

import re
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


def extract_contact_info_enhanced(npri_id="1368"):
    """
    Enhanced extraction with better patterns for the specific NPRI facility
    """

    url = f"https://pollution-waste.canada.ca/national-release-inventory/2024/{npri_id}"
    print(f"🌐 Enhanced extraction from: {url}")

    # Chrome options
    chrome_options = Options()
    # Run visible for debugging
    chrome_options.add_argument("--window-size=1920,1080")

    # Initialize driver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        print("   ⏳ Loading page (this may take 30+ seconds)...")
        driver.get(url)

        # Wait for page to load completely
        time.sleep(20)  # Initial wait

        # Wait for specific content that indicates page is ready
        try:
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.support.ui import WebDriverWait

            wait = WebDriverWait(driver, 30)
            wait.until(
                EC.any_of(
                    EC.presence_of_element_located(
                        (By.XPATH, "//*[contains(text(), 'Contact information')]")
                    ),
                    EC.presence_of_element_located(
                        (By.XPATH, "//*[contains(text(), 'Business number')]")
                    ),
                    EC.presence_of_element_located(
                        (By.XPATH, "//*[contains(text(), 'Facility details')]")
                    ),
                )
            )
            print("   ✅ Page content detected")
        except:
            print("   ⚠️ Continuing without specific content detection...")

        # Additional wait to ensure all dynamic content is loaded
        time.sleep(10)

        # Get the full page source
        page_source = driver.page_source

        # Save page source for analysis
        with open(f"page_source_{npri_id}.html", "w", encoding="utf-8") as f:
            f.write(page_source)

        print(f"📄 Page source saved to: page_source_{npri_id}.html")

        # Enhanced regex patterns based on the expected format
        patterns = {
            "business_number": r"Business number[^}]*?(\d{9})",
            "employees": r"Number of full-time employee equivalents[^}]*?(\d+)",
            "contact_name": r"Contact information[^}]*?([A-Z][a-z]+ [A-Z][a-z]+)",
            "position": r"Position:\s*([^\\n\\r\\}]+?)(?:\s+Phone:|$)",
            "phone": r"Phone:\s*([0-9\-\(\)\s]+?)(?:\s+|\\n|\\r|$)",
            "email": r"Email:\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
            "language": r"Contact Language:\s*([A-Za-z]+)",
        }

        contact_info = {}

        for key, pattern in patterns.items():
            matches = re.findall(pattern, page_source, re.IGNORECASE | re.DOTALL)
            if matches:
                # Take the first match and clean it up
                value = matches[0].strip()
                # Clean up any template syntax or extra whitespace
                value = re.sub(r"\{\{[^}]*\}\}", "", value).strip()
                contact_info[key] = value
                print(f"   {key}: {value}")

        return contact_info

    finally:
        input("Press Enter to close browser...")
        driver.quit()


if __name__ == "__main__":
    print("Enhanced Contact Information Extractor")
    print("=" * 50)

    # Test with Pine Cliff Energy (NPRI 1368)
    contact_info = extract_contact_info_enhanced("1368")

    print("\n" + "=" * 50)
    print("EXTRACTED CONTACT INFORMATION:")
    print("=" * 50)

    for key, value in contact_info.items():
        print(f"{key.replace('_', ' ').title()}: {value}")
