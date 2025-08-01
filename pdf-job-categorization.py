import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from typing import List, Dict, Optional

# Initialize OpenAI client
load_dotenv()
#client = OpenAI(base_url="http://localhost:8080", api_key="sk-1111")  # Replace with your actual API key
client = OpenAI()

# Define the Pydantic model for job listings (inferred from previous code)
class JobListing:
    def __init__(self, job_title: str, company: str, industry: str, location: str, posted_date: str):
        self.job_title = job_title
        self.company = company
        self.industry = industry
        self.location = location
        self.posted_date = posted_date

    def to_dict(self):
        return {
            "job_title": self.job_title,
            "company": self.company,
            "industry": self.industry,
            "location": self.location,
            "posted_date": self.posted_date
        }

# Define tier 1 and tier 2 company lists
TIER_1_COMPANIES = {
    "Apple", "Google", "Meta", "xAI", "ByteDance", "TikTok", "OpenAI",
    "Anthropic", "NVIDIA", "Microsoft", "DeepMind", "Tesla", "SpaceX"
}

TIER_2_COMPANIES = {
    "Amazon", "Uber", "Lyft", "AMD", "Intel", "Salesforce", "Oracle",
    "PayPal", "Spotify", "Shopify", "Stripe", "Coinbase", "Robinhood",
    "Palantir", "Zoom", "Slack", "Docusign", "HubSpot"
}

def classify_job_tier(job: JobListing) -> Optional[str]:
    """
    Classify a job as Tier 1 or Tier 2 based on company name and job title.
    If neither criteria match, uses OpenAI API for classification.
    """
    company = job.company.lower()
    job_title = job.job_title.lower()

    # Check for Tier 1 companies
    if any(tier1.lower() in company for tier1 in TIER_1_COMPANIES):
        return "Tier 1"

    # Check for Tier 2 companies
    if any(tier2.lower() in company for tier2 in TIER_2_COMPANIES):
        return "Tier 2"

    # Check for PhD in job title (Tier 1)
    if "phd" in job_title:
        return "Tier 1"

    # For ambiguous cases, use OpenAI API
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": f"""You are a job classification expert. Classify the following job as 'Tier 1' or 'Tier 2' based on the company's prestige and the nature of the role. 
                    
                    Tier 1 includes companies such as: {TIER_1_COMPANIES}
                    
                    
                    Tier 2 includes companies such as: {TIER_2_COMPANIES}

                    Tier 3 includes everything else.
                    
                    
                    
                    Respond with just the classification (Tier 1, Tier 2, Tier 3)."""
                },
                {
                    "role": "user",
                    "content": f"Company: {job.company}\nJob Title: {job.job_title}\nIndustry: {job.industry}\nLocation: {job.location}\n\nClassification:"
                }
            ],
            max_tokens=10
        )

        classification = response.choices[0].message.content.strip()
        if classification in ["Tier 1", "Tier 2", "Tier 3"]:
            return classification
    except Exception as e:
        print(f"Error classifying job with OpenAI: {e}")
        return None

    return None

def process_job_listings(input_folder="input_pdfs", output_folder="output"):
    """
    Process all JSON files in the input folder, classify jobs into tiers,
    and save the results to the output folder.
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for filename in os.listdir(input_folder):
        if filename.endswith('.json'):
            input_path = os.path.join(input_folder, filename)
            output_path = os.path.join(output_folder, f"classified_{filename}")
            print(f"Processing {filename}")

            try:
                with open(input_path, 'r') as f:
                    job_listings = json.load(f)

                classified_jobs = []
                for job_data in job_listings:
                    print(job_data)
                    job = JobListing(**job_data)
                    tier = classify_job_tier(job)
                    if tier:
                        job_data["tier"] = tier
                        classified_jobs.append(job_data)

                with open(output_path, 'w') as f:
                    json.dump(classified_jobs, f, indent=2)

                print(f"Successfully processed {filename}. {len(classified_jobs)} jobs classified.")
            except Exception as e:
                print(f"Error processing {filename}: {e}")
if __name__ == "__main__":
    process_job_listings(input_folder="./input_pdfs", output_folder="./output")
