#!/usr/bin/env python3
"""
Clean up the contact data and create a final CSV
"""

import csv
import json
import re


def clean_contact_data():
    """Clean up the improved contact data and create final CSV"""

    try:
        # Read the improved JSON data
        with open("improved_contact_info.json", "r", encoding="utf-8") as file:
            data = json.load(file)

        # Clean up the data
        cleaned_data = []

        for item in data:
            if item["success"] and item["contact_info"]:
                contact_info = item["contact_info"].copy()

                # Clean up position field (remove HTML tags)
                if "position" in contact_info:
                    position = contact_info["position"]
                    # Remove HTML tags
                    position = re.sub(r"<[^>]+>", "", position)
                    # Clean up extra whitespace
                    position = re.sub(r"\s+", " ", position).strip()
                    contact_info["position"] = position

                cleaned_item = {
                    "company_name": item["company_name"],
                    "npri_id": item["npri_id"],
                    "contact_info": contact_info,
                    "success": item["success"],
                }
                cleaned_data.append(cleaned_item)

        # Save cleaned JSON
        with open("final_contact_info.json", "w", encoding="utf-8") as file:
            json.dump(cleaned_data, file, indent=2, ensure_ascii=False)

        # Create CSV
        if cleaned_data:
            # Get all possible fields
            all_fields = set()
            for item in cleaned_data:
                all_fields.update(item["contact_info"].keys())

            fieldnames = ["company_name", "npri_id"] + sorted(all_fields)

            with open(
                "final_contact_info.csv", "w", newline="", encoding="utf-8"
            ) as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                for item in cleaned_data:
                    row = {
                        "company_name": item["company_name"],
                        "npri_id": item["npri_id"],
                    }

                    # Add contact info fields
                    for field in sorted(all_fields):
                        row[field] = item["contact_info"].get(field, "")

                    writer.writerow(row)

        print("✅ Contact data cleaned and saved:")
        print("   📄 final_contact_info.json")
        print("   📄 final_contact_info.csv")

        # Display final summary
        print(f"\n📊 FINAL CONTACT INFORMATION SUMMARY")
        print("=" * 60)

        for item in cleaned_data:
            print(f"\n🏢 {item['company_name']} (NPRI {item['npri_id']}):")
            for key, value in item["contact_info"].items():
                print(f"   {key.replace('_', ' ').title()}: {value}")

        print(
            f"\n🎯 Total: {len(cleaned_data)} companies with complete contact information"
        )

    except Exception as e:
        print(f"❌ Error cleaning data: {e}")


if __name__ == "__main__":
    clean_contact_data()
