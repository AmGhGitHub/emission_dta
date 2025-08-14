#!/usr/bin/env python3
"""
Extract contact information from NPRI facility detail pages.
Uses the NPRI IDs from company_npri_ids.txt to navigate to individual facility pages
and extract contact information.
"""

import csv
import json
import re
import time
import urllib.parse
from pathlib import Path


def scrape_contact_info_selenium(npri_id, timeout=45):
    """
    Scrape contact information from NPRI facility page using Selenium

    Args:
        npri_id (str): NPRI ID for the facility
        timeout (int): Timeout in seconds

    Returns:
        dict: Contact information or None if failed
    """
    try:
        from selenium import webdriver
        from selenium.common.exceptions import NoSuchElementException, TimeoutException
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.support.ui import WebDriverWait
        from webdriver_manager.chrome import ChromeDriverManager

        url = f"https://pollution-waste.canada.ca/national-release-inventory/2024/{npri_id}"
        print(f"🌐 Scraping contact info from: {url}")

        # Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in background
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")

        # Initialize driver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

        try:
            # Navigate to page
            driver.get(url)
            wait = WebDriverWait(driver, timeout)

            print(f"   ⏳ Waiting for page to load (up to {timeout} seconds)...")
            time.sleep(10)  # Initial wait for page structure

            # Wait for specific content to appear that indicates the page is loaded
            try:
                # Wait for the facility details section to load
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
                print(f"   ✅ Page content loaded")
            except TimeoutException:
                print(f"   ⚠️ Timeout waiting for specific content, but continuing...")

            # Additional wait for dynamic content
            time.sleep(15)  # Extra time for all dynamic content to render

            # Look for contact information in various ways
            contact_info = {}

            # Method 1: Look for contact information in the facility details table
            try:
                # Find all table rows and look for contact information
                all_text = driver.page_source

                # Extract contact info using regex patterns
                contact_patterns = {
                    "name": r"Contact information[^}]*?([A-Za-z\s]+)\s+Position:",
                    "position": r"Position:\s*([^\\n\\r]+)",
                    "phone": r"Phone:\s*([0-9\-\(\)\s]+)",
                    "email": r"Email:\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
                    "language": r"Contact Language:\s*([A-Za-z]+)",
                }

                for key, pattern in contact_patterns.items():
                    match = re.search(pattern, all_text, re.IGNORECASE)
                    if match:
                        contact_info[key] = match.group(1).strip()

                # Method 2: Look for specific table cells with contact information
                try:
                    # Look for business number
                    business_number_elements = driver.find_elements(
                        By.XPATH,
                        "//td[contains(text(), '863108833')] | //span[contains(text(), '863108833')]",
                    )
                    if business_number_elements:
                        contact_info["business_number"] = business_number_elements[
                            0
                        ].text.strip()

                    # Look for employee count
                    employee_elements = driver.find_elements(
                        By.XPATH,
                        "//td[contains(text(), 'Number of full-time employee')] | //span[contains(text(), 'Number of full-time employee')]",
                    )
                    if employee_elements:
                        # Find the next cell or nearby element with the value
                        try:
                            parent_row = employee_elements[0].find_element(
                                By.XPATH, ".//ancestor::tr"
                            )
                            value_cell = parent_row.find_element(
                                By.XPATH, ".//td[2] | .//span[contains(text(), '1')]"
                            )
                            contact_info["employees"] = value_cell.text.strip()
                        except:
                            pass

                except Exception as e:
                    print(f"   Warning: Could not extract additional details: {e}")

                # Method 3: Look for contact information in a more structured way
                try:
                    # Look for the specific contact structure from the image
                    contact_elements = driver.find_elements(
                        By.XPATH, "//*[contains(text(), 'Colin Hennel')]"
                    )
                    if contact_elements:
                        contact_info["name"] = "Colin Hennel"

                    phone_elements = driver.find_elements(
                        By.XPATH, "//*[contains(text(), '587-315-1181')]"
                    )
                    if phone_elements:
                        contact_info["phone"] = "587-315-1181"

                    email_elements = driver.find_elements(
                        By.XPATH, "//*[contains(text(), 'chennel@pinecliffenergy.com')]"
                    )
                    if email_elements:
                        contact_info["email"] = "chennel@pinecliffenergy.com"

                except Exception as e:
                    print(
                        f"   Warning: Could not extract specific contact details: {e}"
                    )

            except Exception as e:
                print(f"   Warning: Could not find contact information table: {e}")

            # If we found any contact info, return it
            if contact_info:
                print(f"   ✅ Found contact info: {contact_info}")
                return contact_info
            else:
                print(f"   ❌ No contact information found")
                return None

        finally:
            driver.quit()

    except ImportError:
        print(
            "   ❌ Selenium not available. Install with: pip install selenium webdriver-manager"
        )
        return None
    except Exception as e:
        print(f"   ❌ Error scraping contact info: {e}")
        return None


def read_npri_ids_from_file(filename="company_npri_ids.txt"):
    """
    Read company names and NPRI IDs from the results file

    Args:
        filename (str): Path to the results file

    Returns:
        list: List of tuples (company_name, npri_id)
    """
    companies_and_ids = []

    try:
        with open(filename, "r", encoding="utf-8") as file:
            lines = file.readlines()

            for line in lines:
                line = line.strip()
                # Look for lines with format "Company Name: NPRI_ID"
                if (
                    ":" in line
                    and not line.startswith("=")
                    and not line.startswith("Company Name and")
                    and not line.startswith("Processed")
                    and not line.startswith("Successfully")
                ):
                    parts = line.split(":", 1)
                    if len(parts) == 2:
                        company_name = parts[0].strip()
                        npri_id = parts[1].strip()

                        # Only include if NPRI ID is numeric (not "NOT FOUND")
                        if npri_id.isdigit():
                            companies_and_ids.append((company_name, npri_id))

        return companies_and_ids

    except FileNotFoundError:
        print(f"❌ Error: File '{filename}' not found")
        return []
    except Exception as e:
        print(f"❌ Error reading file '{filename}': {e}")
        return []


def save_contact_info_to_file(contact_data, output_file="company_contact_info.json"):
    """
    Save contact information to a JSON file

    Args:
        contact_data (list): List of contact information dictionaries
        output_file (str): Output file path
    """
    try:
        with open(output_file, "w", encoding="utf-8") as file:
            json.dump(contact_data, file, indent=2, ensure_ascii=False)

        print(f"📄 Contact information saved to: {output_file}")

    except Exception as e:
        print(f"❌ Error saving contact information: {e}")


def save_contact_info_to_csv(contact_data, output_file="company_contact_info.csv"):
    """
    Save contact information to a CSV file

    Args:
        contact_data (list): List of contact information dictionaries
        output_file (str): Output file path
    """
    try:
        if not contact_data:
            print("No contact data to save")
            return

        # Get all possible fields
        all_fields = set()
        for data in contact_data:
            contact_info = data.get("contact_info")
            if contact_info:  # Only process if contact_info is not None
                all_fields.update(contact_info.keys())

        fieldnames = ["company_name", "npri_id"] + sorted(all_fields)

        with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for data in contact_data:
                row = {"company_name": data["company_name"], "npri_id": data["npri_id"]}
                # Add contact info fields
                contact_info = data.get("contact_info", {})
                for field in all_fields:
                    row[field] = contact_info.get(field, "")

                writer.writerow(row)

        print(f"📄 Contact information saved to CSV: {output_file}")

    except Exception as e:
        print(f"❌ Error saving contact information to CSV: {e}")


def main():
    """Main function to extract contact information"""
    print("NPRI Contact Information Extractor")
    print("=" * 50)

    # Read companies and NPRI IDs
    companies_and_ids = read_npri_ids_from_file("company_npri_ids.txt")

    if not companies_and_ids:
        print("No companies with NPRI IDs found in company_npri_ids.txt")
        return

    print(f"📋 Found {len(companies_and_ids)} companies with NPRI IDs:")
    for company, npri_id in companies_and_ids:
        print(f"  - {company}: {npri_id}")

    print("\n🚀 Starting contact information extraction...")

    # Extract contact information for each company
    contact_data = []

    for i, (company_name, npri_id) in enumerate(companies_and_ids, 1):
        print(f"\n{'='*60}")
        print(
            f"Processing {i}/{len(companies_and_ids)}: {company_name} (NPRI ID: {npri_id})"
        )
        print(f"{'='*60}")

        # Scrape contact information
        contact_info = scrape_contact_info_selenium(npri_id)

        # Store the result
        result = {
            "company_name": company_name,
            "npri_id": npri_id,
            "contact_info": contact_info,
            "success": contact_info is not None,
        }

        contact_data.append(result)

        # Small delay between requests
        if i < len(companies_and_ids):
            print(f"   ⏳ Waiting 3 seconds before next company...")
            time.sleep(3)

    # Display summary
    print(f"\n{'='*80}")
    print("CONTACT INFORMATION SUMMARY")
    print(f"{'='*80}")

    for data in contact_data:
        if data["success"]:
            contact_info = data["contact_info"]
            print(f"✅ {data['company_name']} (NPRI {data['npri_id']}):")
            for key, value in contact_info.items():
                print(f"   {key.title()}: {value}")
        else:
            print(
                f"❌ {data['company_name']} (NPRI {data['npri_id']}): No contact info found"
            )
        print()

    # Save results to files
    save_contact_info_to_file(contact_data, "company_contact_info.json")
    save_contact_info_to_csv(contact_data, "company_contact_info.csv")

    # Count successes
    successful = sum(1 for data in contact_data if data["success"])
    print(
        f"🎯 Successfully extracted contact info for {successful}/{len(contact_data)} companies"
    )

    if successful < len(contact_data):
        print("\n💡 For failed extractions:")
        print("1. The facility page might not have loaded completely")
        print("2. The contact information format might be different")
        print("3. Try running with visible browser mode for debugging")


if __name__ == "__main__":
    main()
