#!/usr/bin/env python3
"""
Convert the contact info JSON to CSV format
"""

import csv
import json


def convert_json_to_csv():
    """Convert company_contact_info.json to CSV format"""

    try:
        # Read JSON data
        with open("company_contact_info.json", "r", encoding="utf-8") as file:
            contact_data = json.load(file)

        if not contact_data:
            print("No data found in JSON file")
            return

        # Get all possible fields from successful extractions
        all_fields = set()
        for data in contact_data:
            contact_info = data.get("contact_info")
            if contact_info:
                all_fields.update(contact_info.keys())

        # Create fieldnames for CSV
        fieldnames = ["company_name", "npri_id", "success"] + sorted(all_fields)

        # Write CSV file
        with open(
            "company_contact_info.csv", "w", newline="", encoding="utf-8"
        ) as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for data in contact_data:
                row = {
                    "company_name": data["company_name"],
                    "npri_id": data["npri_id"],
                    "success": data["success"],
                }

                # Add contact info fields
                contact_info = data.get("contact_info", {})
                if contact_info:
                    for field in all_fields:
                        row[field] = contact_info.get(field, "")
                else:
                    for field in all_fields:
                        row[field] = ""

                writer.writerow(row)

        print("✅ Successfully converted JSON to CSV: company_contact_info.csv")

        # Display summary
        successful = sum(1 for data in contact_data if data["success"])
        print(
            f"📊 Summary: {successful}/{len(contact_data)} companies have contact information"
        )

    except FileNotFoundError:
        print("❌ company_contact_info.json file not found")
    except Exception as e:
        print(f"❌ Error converting to CSV: {e}")


if __name__ == "__main__":
    convert_json_to_csv()
