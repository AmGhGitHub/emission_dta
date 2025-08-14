#!/usr/bin/env python3
"""
Read the first value from the second line of the downloaded CSV file
"""

import csv
from pathlib import Path


def read_first_npri_id(csv_file_path):
    """
    Read the first NPRI ID from the CSV file

    Args:
        csv_file_path (str): Path to the CSV file

    Returns:
        str: The first NPRI ID value
    """
    try:
        with open(csv_file_path, "r", encoding="utf-8") as file:
            csv_reader = csv.reader(file)

            # Skip the header row
            header = next(csv_reader)
            print(f"📊 Header: {header}")

            # Read the first data row (second line)
            first_data_row = next(csv_reader)
            print(f"📋 First data row: {first_data_row}")

            # Get the first value (NPRI ID)
            first_npri_id = first_data_row[0]
            print(f"🎯 First NPRI ID: {first_npri_id}")

            return first_npri_id

    except FileNotFoundError:
        print(f"❌ Error: File '{csv_file_path}' not found")
        return None
    except Exception as e:
        print(f"❌ Error reading CSV file: {e}")
        return None


def main():
    # Path to the downloaded CSV file (use the newest one for Spur Petroleum)
    csv_file = "downloads/National Pollutant Release Inventory data search (1).csv"

    print("NPRI CSV Reader")
    print("=" * 40)
    print(f"📄 Reading file: {csv_file}")

    # Read the first NPRI ID
    npri_id = read_first_npri_id(csv_file)

    if npri_id:
        print(f"\n✅ SUCCESS: First NPRI ID from second line: {npri_id}")
    else:
        print("\n❌ FAILED: Could not read NPRI ID")


if __name__ == "__main__":
    main()
