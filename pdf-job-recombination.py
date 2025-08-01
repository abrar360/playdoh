import os
import json
from datetime import datetime, timedelta
from typing import List, Dict

def parse_date_string(date_str: str) -> int:
    """
    Convert date strings in various formats (e.g., "3 weeks ago", "4 months ago", "38d")
    into a datetime object.
    """
    if not date_str:
        return 10000000000

    date_str = date_str.replace("Posted", "").strip()

    try:
        unit = date_str.lower()
        split_date = date_str.split()
        if "day" in unit:
            return int(split_date[0])
        elif "week" in unit:
            return int(split_date[0]) * 7
        elif "month" in unit:
            return int(split_date[0]) * 30 
        elif "year" in unit:
            return int(split_date[0]) * 365
        else:
            print("UNHANDLED....: ", date_str)
            return 10000000000
            # Try parsing as ISO format (e.g., "2023-12-25"
    except:
        return 10000000000

def combine_and_sort_jobs(input_folder: str = "./output", output_file: str = "master_job_list.json") -> None:
    """
    Combine all classified job listings from JSON files in the input folder,
    sort them by posted_date (most recent first), and save to a master JSON file.
    """
    all_jobs = []

    # Read all classified job files
    for filename in os.listdir(input_folder):
        if filename.startswith("classified_") and filename.endswith(".json"):
            filepath = os.path.join(input_folder, filename)
            try:
                with open(filepath, "r") as f:
                    jobs = json.load(f)
                    all_jobs.extend(jobs)
            except Exception as e:
                print(f"Error reading {filename}: {e}")

    if not all_jobs:
        print("No job listings found in the input folder.")
        return

    # Sort jobs by posted_date (most recent first)
    try:
        sorted_jobs = sorted(
            all_jobs,
            key=lambda x: parse_date_string(x["posted_date"]),
            reverse=False
        )
    except Exception as e:
        print(f"Error sorting jobs: {e}")
        return

    # Save the sorted master list
    try:
        with open(output_file, "w") as f:
            json.dump(sorted_jobs, f, indent=2)
        print(f"Successfully created master job list with {len(sorted_jobs)} jobs in {output_file}")
    except Exception as e:
        print(f"Error saving master job list: {e}")

if __name__ == "__main__":
    combine_and_sort_jobs(input_folder="./output", output_file="master_job_list.json")
