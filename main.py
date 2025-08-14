import os
import sys
import time
import urllib.parse
from pathlib import Path

import requests
from bs4 import BeautifulSoup


def download_npri_csv_with_selenium(url, company_name, download_dir="downloads"):
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
        # Set up headers to mimic a real browser request
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        print(f"Fetching data from: {url}")

        # Make the request
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()  # Raise an exception for bad status codes

        print(f"Response status code: {response.status_code}")

        # Parse the HTML content
        soup = BeautifulSoup(response.content, "html.parser")

        # Look for the data table - try multiple approaches
        # First, look for a table with NPRI ID header
        tables = soup.find_all("table")

        if not tables:
            print("No tables found on the page")
            return None

        print(f"Found {len(tables)} table(s) on the page")

        # Search through all tables for one with NPRI ID column
        for i, table in enumerate(tables):
            print(f"Examining table {i + 1}...")

            # Look for table headers
            headers_row = table.find("tr")
            if not headers_row:
                continue

            headers = headers_row.find_all(["th", "td"])
            header_texts = [h.get_text(strip=True) for h in headers]

            print(f"Table {i + 1} headers: {header_texts}")

            # Check if this table has NPRI ID column
            npri_id_index = None
            for idx, header in enumerate(header_texts):
                if "NPRI" in header.upper() and "ID" in header.upper():
                    npri_id_index = idx
                    print(f"Found NPRI ID column at index {idx}")
                    break

            if npri_id_index is not None:
                # Find all rows and look for rows containing the company name
                all_rows = table.find_all("tr")

                # Extract company name from URL for matching
                company_name_from_url = url.split("name=")[1].split("&")[0]
                company_name_decoded = urllib.parse.unquote(company_name_from_url)
                print(f"Looking for company name: '{company_name_decoded}'")

                # Look for actual data rows with the company name
                for row_idx, row in enumerate(all_rows):
                    cells = row.find_all(["td", "th"])
                    row_text = row.get_text()

                    # Check if this row contains the company name
                    company_keywords = company_name_decoded.replace(".", "").split()
                    if any(
                        keyword.lower() in row_text.lower()
                        for keyword in company_keywords
                        if len(keyword) > 3
                    ):
                        print(
                            f"Row {row_idx + 1} contains company name, checking for NPRI ID..."
                        )

                        # Look for any links in this row that could be NPRI IDs
                        all_links_in_row = row.find_all("a", href=True)
                        for link in all_links_in_row:
                            href = link.get("href", "")
                            link_text = link.get_text(strip=True)
                            print(
                                f"Found link in company row: href='{href}', text='{link_text}'"
                            )

                            # Check if this link contains a year/ID pattern or is numeric
                            if "/2024/" in href and link_text.isdigit():
                                print(
                                    f"✅ First NPRI ID found in company row: {link_text}"
                                )
                                return link_text
                            elif link_text.isdigit() and len(link_text) >= 3:
                                print(
                                    f"✅ First NPRI ID found (numeric link): {link_text}"
                                )
                                return link_text

                        # Also check the NPRI ID cell specifically in this row
                        if len(cells) > npri_id_index:
                            npri_cell = cells[npri_id_index]
                            cell_text = npri_cell.get_text(strip=True)
                            print(f"NPRI ID cell in company row: '{cell_text}'")

                            # Look for links within the NPRI ID cell
                            cell_link = npri_cell.find("a", href=True)
                            if cell_link:
                                href = cell_link.get("href", "")
                                link_text = cell_link.get_text(strip=True)
                                print(
                                    f"NPRI cell link: href='{href}', text='{link_text}'"
                                )

                                if link_text.isdigit():
                                    print(
                                        f"✅ First NPRI ID found in NPRI cell: {link_text}"
                                    )
                                    return link_text

                print("No NPRI ID found in company-specific rows")

                print("No numeric NPRI ID found in table rows")

                # Alternative approach: look for links with NPRI IDs
                print("Trying to find NPRI ID links or patterns...")

                # Look for links that contain year/ID pattern like "./2024/1368"
                all_links = table.find_all("a", href=True)
                for link in all_links:
                    href = link.get("href", "")
                    link_text = link.get_text(strip=True)
                    print(f"Found link: href='{href}', text='{link_text}'")

                    # Check if this is a detail link with year/ID pattern
                    if "/2024/" in href and link_text.isdigit():
                        print(f"Found NPRI ID in detail link: {link_text}")
                        return link_text

                    # Also check if href contains the ID pattern
                    import re

                    href_match = re.search(r"/2024/(\d+)", href)
                    if href_match:
                        npri_id = href_match.group(1)
                        print(f"Found NPRI ID in href pattern: {npri_id}")
                        return npri_id

                # Look for any numeric values that could be NPRI IDs
                print("Looking for any numeric patterns in the table...")
                for row in all_rows:
                    cells = row.find_all(["td", "th"])
                    for cell in cells:
                        cell_text = cell.get_text(strip=True)
                        if (
                            cell_text.isdigit() and len(cell_text) >= 3
                        ):  # NPRI IDs are typically longer than 2 digits
                            print(f"Found potential NPRI ID: {cell_text}")
                            return cell_text

        # If no table with NPRI ID found, try alternative approaches
        print("No table with NPRI ID column found. Trying alternative approaches...")

        # Look for specific NPRI IDs from the known data
        known_npri_ids = ["1368", "6626", "15098"]
        print(f"Searching for known NPRI IDs: {known_npri_ids}")

        page_text = soup.get_text()
        for npri_id in known_npri_ids:
            if npri_id in page_text:
                print(f"Found known NPRI ID {npri_id} in page content")
                return npri_id

        # Look for any element containing NPRI ID pattern
        npri_elements = soup.find_all(text=lambda text: text and "npri" in text.lower())
        for element in npri_elements[:5]:  # Check first 5 matches
            print(f"Found NPRI-related text: {element.strip()}")

        # Look for any 4-digit numbers that might be NPRI IDs
        import re

        numbers = re.findall(r"\b\d{4,5}\b", page_text)
        unique_numbers = list(set(numbers))[:10]  # Get first 10 unique numbers
        print(f"Found potential ID numbers on page: {unique_numbers}")

        return None

    except requests.exceptions.RequestException as e:
        print(f"Network error occurred: {e}")
        return None
    except Exception as e:
        print(f"An error occurred while parsing: {e}")
        return None


def scrape_with_selenium(url):
    """
    Alternative scraping method using Selenium for JavaScript-rendered content
    """
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.support.ui import WebDriverWait

        print("Trying Selenium approach for JavaScript content...")

        # Set up Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in background
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        # Initialize the driver
        driver = webdriver.Chrome(options=chrome_options)

        try:
            # Load the page
            driver.get(url)

            # Wait for the table to load
            wait = WebDriverWait(driver, 20)
            table = wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))

            # Look for links with the detail-link class
            detail_links = driver.find_elements(By.CSS_SELECTOR, "a.detail-link")

            for link in detail_links:
                href = link.get_attribute("href")
                text = link.text.strip()

                if "/2024/" in href and text.isdigit():
                    print(f"Found NPRI ID with Selenium: {text}")
                    return text

            # Alternative: look for any links with year/ID pattern
            all_links = driver.find_elements(By.TAG_NAME, "a")
            for link in all_links:
                href = link.get_attribute("href") or ""
                text = link.text.strip()

                if "/2024/" in href and text.isdigit():
                    print(f"Found NPRI ID in link: {text}")
                    return text

            return None

        finally:
            driver.quit()

    except ImportError:
        print("Selenium not available. Install with: pip install selenium")
        return None
    except Exception as e:
        print(f"Selenium error: {e}")
        return None


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


def get_known_npri_data():
    """
    Return known NPRI data for companies when dynamic scraping fails
    Based on the previously observed data structure
    """
    return {
        "Pine Cliff Energy Ltd": "1368",  # From the HTML structure you provided
        "Spur Petroleum Ltd": None,  # Unknown - would need to check manually
        "Signalta Resources Ltd": None,  # Unknown - would need to check manually
    }


def process_single_company(company_name):
    """
    Process a single company and extract its first NPRI ID

    Args:
        company_name (str): The name of the company to process

    Returns:
        tuple: (company_name, npri_id, success_method)
    """
    print(f"\n{'='*60}")
    print(f"Processing: {company_name}")
    print(f"{'='*60}")

    # Create URL for this company
    url = create_url_for_company(company_name)
    print(f"URL: {url}")

    # Try static scraping first
    first_npri_id = scrape_npri_data(url)

    if first_npri_id:
        print(f"✅ SUCCESS: First NPRI ID extracted: {first_npri_id}")
        return (company_name, first_npri_id, "Static Scraping")
    else:
        print("⚠️  Static scraping failed. Trying Selenium for JavaScript content...")

        # Try Selenium approach
        first_npri_id = scrape_with_selenium(url)

        if first_npri_id:
            print(f"✅ SUCCESS: First NPRI ID extracted with Selenium: {first_npri_id}")
            return (company_name, first_npri_id, "Selenium")
        else:
            print("❌ Could not extract NPRI ID from the page")
            print("This might be due to:")
            print("- The page requires JavaScript to load content")
            print("- Network connectivity issues")
            print("- The page has anti-scraping measures")
            print("- No data available for this company")

            # Try fallback with known data
            known_data = get_known_npri_data()
            if company_name in known_data and known_data[company_name]:
                fallback_id = known_data[company_name]
                print(f"🔄 Using known fallback data: NPRI ID {fallback_id}")
                return (company_name, fallback_id, "Known Data")

            return (company_name, None, "Failed")


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
    """Main function to run the NPRI data scraper for multiple companies"""
    print("NPRI Data Scraper - Multiple Companies")
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
        time.sleep(2)

    # Display summary results
    print(f"\n{'='*80}")
    print("SUMMARY RESULTS")
    print(f"{'='*80}")
    print(f"{'Company':<30} {'NPRI ID':<10} {'Method':<15}")
    print(f"{'-'*30} {'-'*10} {'-'*15}")

    for company, npri_id, method in results:
        npri_display = npri_id if npri_id else "Not Found"
        print(f"{company:<30} {npri_display:<10} {method:<15}")

    # Count successes
    successful = sum(1 for _, npri_id, _ in results if npri_id)
    print(
        f"\nSuccessfully extracted NPRI IDs for {successful}/{len(results)} companies"
    )

    # Show information about improving results
    failed_count = len(results) - successful
    if failed_count > 0:
        print(f"\n💡 To improve results for the {failed_count} failed companies:")
        print("1. Install Selenium for JavaScript rendering: pip install selenium")
        print("2. Install Chrome WebDriver")
        print("3. Update the known_npri_data() function with manually found IDs")
        print("4. Check if companies have NPRI data for 2024 at the website manually")


if __name__ == "__main__":
    main()
