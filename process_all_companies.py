#!/usr/bin/env python3
"""
Process all companies from companies.txt:
1. Download CSV files for each company
2. Extract the first NPRI ID from each CSV
3. Save results to a summary file
"""

import csv
import os
import sys
import time
import urllib.parse
from pathlib import Path


def download_npri_csv_for_company(company_name, download_dir="downloads"):
    """
    Download CSV file for a specific company using Selenium

    Args:
        company_name (str): Name of the company
        download_dir (str): Directory to save files

    Returns:
        tuple: (success: bool, csv_file_path: str, message: str)
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

        # Create URL for the company
        base_url = "https://pollution-waste.canada.ca/national-release-inventory/"
        encoded_name = urllib.parse.quote(company_name)
        url = f"{base_url}?fromYear=2024&toYear=2024&name={encoded_name}&direction=ascending&order=NPRI_Id&length=10&page=1"

        print(f"🌐 Downloading CSV for: {company_name}")
        print(f"   URL: {url}")

        # Setup download directory
        download_path = Path(download_dir).absolute()
        download_path.mkdir(exist_ok=True)

        # Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in background
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_experimental_option(
            "prefs",
            {
                "download.default_directory": str(download_path),
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
            },
        )

        # Initialize driver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

        try:
            # Navigate to page
            driver.get(url)
            wait = WebDriverWait(driver, 20)
            time.sleep(3)

            # Get initial file count
            initial_files = set(download_path.glob("*.csv"))

            # Look for download button
            download_button = None
            button_selectors = [
                "//span[contains(text(), 'Download as CSV')]",
                "//button[contains(text(), 'Download as CSV')]",
                "//a[contains(text(), 'Download as CSV')]",
                "//*[contains(text(), 'Download as CSV')]",
            ]

            for selector in button_selectors:
                try:
                    download_button = driver.find_element(By.XPATH, selector)
                    break
                except NoSuchElementException:
                    continue

            if not download_button:
                return False, "", f"No download button found for {company_name}"

            # Click download button
            try:
                driver.execute_script(
                    "arguments[0].scrollIntoView(true);", download_button
                )
                time.sleep(1)
                driver.execute_script("arguments[0].click();", download_button)
                print(f"   ✅ Clicked download button")

                # Wait for download
                download_timeout = 15
                start_time = time.time()

                while time.time() - start_time < download_timeout:
                    current_files = set(download_path.glob("*.csv"))
                    new_files = current_files - initial_files

                    if new_files:
                        downloaded_file = list(new_files)[0]
                        print(f"   📄 Downloaded: {downloaded_file.name}")
                        return True, str(downloaded_file), "CSV downloaded successfully"

                    time.sleep(1)

                return False, "", f"Download timeout for {company_name}"

            except Exception as e:
                return False, "", f"Failed to click download button: {e}"

        finally:
            driver.quit()

    except ImportError:
        return (
            False,
            "",
            "Selenium not available. Install with: pip install selenium webdriver-manager",
        )
    except Exception as e:
        return False, "", f"Error downloading CSV: {e}"


def extract_first_npri_id(csv_file_path):
    """
    Extract the first NPRI ID from a CSV file

    Args:
        csv_file_path (str): Path to the CSV file

    Returns:
        str: First NPRI ID or None if not found
    """
    try:
        with open(csv_file_path, "r", encoding="utf-8") as file:
            csv_reader = csv.reader(file)

            # Skip header
            next(csv_reader)

            # Read first data row
            first_row = next(csv_reader)

            # Get first value (NPRI ID)
            first_npri_id = first_row[0]

            # Clean up the ID (remove BOM if present)
            if first_npri_id.startswith("\ufeff"):
                first_npri_id = first_npri_id[1:]

            # Remove quotes if present
            first_npri_id = first_npri_id.strip('"')

            return first_npri_id

    except Exception as e:
        print(f"   ❌ Error reading CSV: {e}")
        return None


def read_companies_from_file(filename="companies.txt"):
    """
    Read company names from text file

    Args:
        filename (str): Path to companies file

    Returns:
        list: List of company names
    """
    try:
        with open(filename, "r", encoding="utf-8") as file:
            companies = [line.strip() for line in file if line.strip()]
        return companies
    except FileNotFoundError:
        print(f"❌ Error: File '{filename}' not found")
        return []
    except Exception as e:
        print(f"❌ Error reading file '{filename}': {e}")
        return []


def save_results_to_file(results, output_file="company_npri_ids.txt"):
    """
    Save company name and NPRI ID results to a text file

    Args:
        results (list): List of tuples (company_name, npri_id, status)
        output_file (str): Output file path
    """
    try:
        with open(output_file, "w", encoding="utf-8") as file:
            file.write("Company Name and First NPRI ID Results\n")
            file.write("=" * 50 + "\n\n")

            for company_name, npri_id, status in results:
                if npri_id:
                    file.write(f"{company_name}: {npri_id}\n")
                else:
                    file.write(f"{company_name}: NOT FOUND ({status})\n")

            file.write(f"\n\nProcessed {len(results)} companies\n")
            successful = sum(1 for _, npri_id, _ in results if npri_id)
            file.write(
                f"Successfully found NPRI IDs for {successful}/{len(results)} companies\n"
            )

        print(f"📄 Results saved to: {output_file}")

    except Exception as e:
        print(f"❌ Error saving results: {e}")


def main():
    """Main function to process all companies"""
    print("NPRI Company Processor")
    print("=" * 50)

    # Read companies
    companies = read_companies_from_file("companies.txt")

    if not companies:
        print("No companies found in companies.txt file")
        return

    print(f"📋 Found {len(companies)} companies to process:")
    for i, company in enumerate(companies, 1):
        print(f"  {i}. {company}")

    print("\n🚀 Starting processing...")

    # Process each company
    results = []

    for i, company in enumerate(companies, 1):
        print(f"\n{'='*60}")
        print(f"Processing {i}/{len(companies)}: {company}")
        print(f"{'='*60}")

        # Download CSV
        success, csv_file, message = download_npri_csv_for_company(company)

        if success:
            print(f"   ✅ CSV downloaded successfully")

            # Extract first NPRI ID
            npri_id = extract_first_npri_id(csv_file)

            if npri_id:
                print(f"   🎯 First NPRI ID: {npri_id}")
                results.append((company, npri_id, "SUCCESS"))
            else:
                print(f"   ❌ Could not extract NPRI ID from CSV")
                results.append((company, None, "CSV_READ_ERROR"))
        else:
            print(f"   ❌ Failed to download CSV: {message}")
            results.append((company, None, message))

        # Small delay between requests
        if i < len(companies):
            print(f"   ⏳ Waiting 3 seconds before next company...")
            time.sleep(3)

    # Display summary
    print(f"\n{'='*80}")
    print("FINAL SUMMARY")
    print(f"{'='*80}")

    for company, npri_id, status in results:
        if npri_id:
            print(f"✅ {company:<30} → {npri_id}")
        else:
            print(f"❌ {company:<30} → FAILED ({status})")

    # Save results to file
    save_results_to_file(results)

    # Count successes
    successful = sum(1 for _, npri_id, _ in results if npri_id)
    print(f"\n🎯 Successfully processed {successful}/{len(results)} companies")

    if successful < len(results):
        print("\n💡 For failed companies, you can:")
        print("1. Check if they have NPRI data for 2024 manually")
        print("2. Run with visible browser mode for debugging")
        print("3. Check the downloads folder for partial files")


if __name__ == "__main__":
    main()
