import os
import sys
import time
import urllib.parse
from pathlib import Path


def download_npri_csv_with_selenium(url, company_name, download_dir="downloads", headless=True):
    """
    Navigate to NPRI website and download CSV data for a company.

    Args:
        url (str): The URL to navigate to
        company_name (str): Name of the company for the filename
        download_dir (str): Directory to save the downloaded file

    Returns:
        tuple: (success: bool, file_path: str, message: str)
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

        print(f"🌐 Navigating to: {url}")

        # Create download directory if it doesn't exist
        download_path = Path(download_dir).absolute()
        download_path.mkdir(exist_ok=True)
        print(f"📁 Download directory: {download_path}")

        # Set up Chrome options for file download
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        chrome_options.add_argument("--window-size=1920,1080")

        # Configure download preferences
        prefs = {
            "download.default_directory": str(download_path),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
        }
        chrome_options.add_experimental_option("prefs", prefs)

        # Initialize the driver with automatic Chrome driver management
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

        try:
            # Remove automation indicators
            driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )

            # Navigate to the page
            driver.get(url)
            print("✅ Page loaded successfully")

            # Wait for the page to load completely
            wait = WebDriverWait(driver, 20)

            # Wait for results to load (look for the results table or download button)
            try:
                # Wait for either the table to appear or some content indicator
                wait.until(
                    EC.any_of(
                        EC.presence_of_element_located((By.TAG_NAME, "table")),
                        EC.presence_of_element_located((By.CLASS_NAME, "table")),
                        EC.presence_of_element_located(
                            (
                                By.XPATH,
                                "//button[contains(text(), 'CSV') or contains(text(), 'Download')]",
                            )
                        ),
                    )
                )
                print("📊 Page content loaded")
            except TimeoutException:
                print("⚠️ Timeout waiting for page content, proceeding anyway")

            # Look for download/CSV button with various possible selectors
            download_button = None
            button_selectors = [
                "//button[contains(text(), 'Download as CSV')]",
                "//a[contains(text(), 'Download as CSV')]",
                "//button[contains(text(), 'CSV')]",
                "//a[contains(text(), 'CSV')]",
                "//button[contains(text(), 'Download')]",
                "//a[contains(text(), 'Download')]",
                "//input[@value='Download as CSV']",
                "//*[@id='downloadCSV']",
                "//*[contains(@class, 'download') and contains(@class, 'csv')]",
                "//*[contains(@class, 'btn') and contains(text(), 'CSV')]",
            ]

            for selector in button_selectors:
                try:
                    download_button = driver.find_element(By.XPATH, selector)
                    print(f"🔍 Found download button with selector: {selector}")
                    break
                except NoSuchElementException:
                    continue

            if not download_button:
                # Try to find any clickable element that might trigger CSV download
                try:
                    download_button = driver.find_element(
                        By.XPATH,
                        "//*[contains(text(), 'CSV') or contains(text(), 'Download')]",
                    )
                    print("🔍 Found potential download element")
                except NoSuchElementException:
                    # Take a screenshot for debugging
                    screenshot_path = (
                        download_path
                        / f"debug_screenshot_{company_name.replace(' ', '_')}.png"
                    )
                    driver.save_screenshot(str(screenshot_path))
                    print(f"📸 Debug screenshot saved to: {screenshot_path}")

                    # Save page source for debugging
                    page_source_path = (
                        download_path
                        / f"debug_page_source_{company_name.replace(' ', '_')}.html"
                    )
                    with open(page_source_path, "w", encoding="utf-8") as f:
                        f.write(driver.page_source)
                    print(f"📄 Page source saved to: {page_source_path}")

                    return False, "", "No download button found on the page"

            # Get initial file count in download directory
            initial_files = set(download_path.glob("*"))

            # Make sure the download button is clickable
            try:
                # Wait for the button to be clickable
                clickable_button = wait.until(EC.element_to_be_clickable(download_button))
                
                # Scroll to the button and make it visible
                driver.execute_script("arguments[0].scrollIntoView(true);", clickable_button)
                time.sleep(2)
                
                # Try to enable the button if it's disabled
                driver.execute_script("arguments[0].removeAttribute('disabled');", clickable_button)
                
                # Try JavaScript click first
                try:
                    driver.execute_script("arguments[0].click();", clickable_button)
                    print("🖱️ Clicked download button using JavaScript")
                except Exception:
                    # Fallback to regular click
                    clickable_button.click()
                    print("🖱️ Clicked download button using regular click")
                    
            except TimeoutException:
                # If button not clickable, try alternative methods
                print("⚠️ Button not clickable, trying alternative approaches...")
                
                # Try to find and click any CSV-related links or buttons
                csv_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'CSV')]")
                for element in csv_elements:
                    try:
                        driver.execute_script("arguments[0].click();", element)
                        print(f"🖱️ Clicked CSV element: {element.text}")
                        break
                    except Exception:
                        continue
                else:
                    return False, "", "Could not click any download element"

            # Wait for file to be downloaded
            print("⏳ Waiting for file download...")
            download_timeout = 30
            start_time = time.time()

            while time.time() - start_time < download_timeout:
                current_files = set(download_path.glob("*"))
                new_files = current_files - initial_files

                # Check for completed downloads (not .crdownload files)
                completed_files = [
                    f for f in new_files if not f.name.endswith(".crdownload")
                ]

                if completed_files:
                    downloaded_file = completed_files[0]

                    # Rename file to include company name
                    company_safe_name = company_name.replace(" ", "_").replace(".", "")
                    new_filename = (
                        f"NPRI_data_{company_safe_name}_{int(time.time())}.csv"
                    )
                    final_path = download_path / new_filename

                    try:
                        downloaded_file.rename(final_path)
                        print(f"✅ File downloaded and renamed to: {final_path}")
                        return True, str(final_path), "CSV file downloaded successfully"
                    except Exception as e:
                        print(f"✅ File downloaded to: {downloaded_file}")
                        return (
                            True,
                            str(downloaded_file),
                            f"CSV file downloaded (rename failed: {e})",
                        )

                time.sleep(1)

            return False, "", f"Download timeout after {download_timeout} seconds"

        finally:
            driver.quit()

    except ImportError:
        return False, "", "Selenium not available. Install with: pip install selenium"
    except Exception as e:
        return False, "", f"Error during download: {e}"


def create_url_for_company(company_name):
    """
    Create the NPRI search URL for a specific company

    Args:
        company_name (str): The name of the company to search for

    Returns:
        str: The complete URL for searching this company's NPRI data
    """
    base_url = "https://pollution-waste.canada.ca/national-release-inventory/"

    # URL encode the company name to handle spaces and special characters
    encoded_name = urllib.parse.quote(company_name)

    # Build the complete URL with query parameters
    url = f"{base_url}?fromYear=2024&toYear=2024&name={encoded_name}&direction=ascending&order=NPRI_Id&length=10&page=1"

    return url


def process_single_company(company_name):
    """
    Process a single company and download its NPRI CSV data

    Args:
        company_name (str): The name of the company to process

    Returns:
        tuple: (company_name, success, file_path, message)
    """
    print(f"\n{'='*60}")
    print(f"Processing: {company_name}")
    print(f"{'='*60}")

    # Create URL for this company
    url = create_url_for_company(company_name)
    print(f"URL: {url}")

    # Download CSV using Selenium (run in visible mode for debugging)
    success, file_path, message = download_npri_csv_with_selenium(url, company_name, headless=False)

    if success:
        print(f"✅ SUCCESS: CSV downloaded for {company_name}")
        print(f"📄 File location: {file_path}")
    else:
        print(f"❌ FAILED: Could not download CSV for {company_name}")
        print(f"📝 Reason: {message}")

    return (company_name, success, file_path, message)


def read_companies_from_file(filename="companies.txt"):
    """
    Read company names from a text file

    Args:
        filename (str): Path to the file containing company names

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


def main():
    """Main function to run the NPRI CSV downloader for multiple companies"""
    print("NPRI CSV Downloader - Multiple Companies")
    print("=" * 50)

    # Read companies from file
    companies = read_companies_from_file("companies.txt")

    if not companies:
        print("No companies found in companies.txt file")
        return

    print(f"Found {len(companies)} companies to process:")
    for i, company in enumerate(companies, 1):
        print(f"  {i}. {company}")

    # Process each company
    results = []

    for company in companies:
        result = process_single_company(company)
        results.append(result)

        # Add a small delay between requests to be respectful to the server
        time.sleep(3)

    # Display summary results
    print(f"\n{'='*80}")
    print("SUMMARY RESULTS")
    print(f"{'='*80}")
    print(f"{'Company':<30} {'Status':<10} {'File Path':<40}")
    print(f"{'-'*30} {'-'*10} {'-'*40}")

    for company, success, file_path, message in results:
        status = "SUCCESS" if success else "FAILED"
        display_path = file_path if success else message[:40]
        print(f"{company:<30} {status:<10} {display_path:<40}")

    # Count successes
    successful = sum(1 for _, success, _, _ in results if success)
    print(
        f"\nSuccessfully downloaded CSV files for {successful}/{len(results)} companies"
    )

    if successful < len(results):
        failed_count = len(results) - successful
        print(f"\n💡 For the {failed_count} failed companies:")
        print("1. Check if they have NPRI data for 2024")
        print("2. Verify Chrome WebDriver is installed and up to date")
        print("3. Check the debug files in the downloads folder")
        print("4. Try running with visible browser (remove headless mode)")


if __name__ == "__main__":
    main()
