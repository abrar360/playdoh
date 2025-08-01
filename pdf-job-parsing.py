import os
import fitz  # PyMuPDF for PDF to image conversion
from PIL import Image
import openai
from openai import OpenAI
from dotenv import load_dotenv
import base64
import json

# Okay suppose we will have a handful of pdfs inside a folder.abs
# We want to do the following for each pdf:
# For each page:
#     1. Take the page and convert it into an image
#     2. Inference openAI GPT4o, and ask it to take the image and extract all job listings from it in a structured format like this:
#     {
#         "job_title": "Salesforce Solutions Architect (Technical Solutions Engineer)",
#         "company": "AgentSync",
#         "industry": "Insurance industry compliance",
#         "location": "Remote (Georgia)",
#         "posted_date": "1 month ago",
#     },
#     3. Then append each of the job listings to a file format which can easily be parsed in python.



# Initialize OpenAI client
#load_dotenv()
client = OpenAI(base_url="http://localhost:8080", api_key="sk-1111")  # Replace with your actual API key
#client = OpenAI()

# Function to convert PDF page to image
def pdf_page_to_image(pdf_path, page_num, output_dir="images"):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    doc = fitz.open(pdf_path)
    page = doc.load_page(page_num)
    pix = page.get_pixmap()
    image_path = os.path.join(output_dir, f"page_{page_num}.png")
    pix.save(image_path)

    return image_path

from pydantic import BaseModel
from typing import List

# Define the Pydantic model for job listings
class JobListing(BaseModel):
    job_title: str
    company: str
    industry: str
    location: str
    posted_date: str

# Function to extract job listings using OpenAI GPT-4o vision with structured output
def extract_job_listings(image_path):
    # Read and encode the image as base64
    with open(image_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode('utf-8')

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "You are an expert at extracting job listings from documents. Please respond only with valid JSON containing all job listings from the provided image in the specified structured format."
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Extract all job listings from this image and respond ONLY with valid JSON in the following format:",
                        "text": """[
                            {
                                "job_title": "string",
                                "company": "string",
                                "industry": "string",
                                "location": "string",
                                "posted_date": "string"
                            }
                        ]"""
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        response_format={"type": "json_object"},
        max_tokens=2000
    )

    # Get the parsed output
    response_data = response.choices[0].message.content
    # Parse the response data and handle the 'jobs' array
    try:
        #print("Raw response: ", response_data)
        response_json = json.loads(response_data)
        if isinstance(response_json, list):
            # Directly use the list if it's already in correct format
            return [JobListing.model_validate(job) for job in response_json]
        elif isinstance(response_json, dict) and 'jobs' in response_json:
            # Handle the case where jobs are under a 'jobs' key
            return [JobListing.model_validate(job) for job in response_json['jobs']]
        elif isinstance(response_json, dict):
            jbs = []
            for jkey in response_json.keys():
                for job in response_json[jkey]:
                    jbs.append(JobListing.model_validate(job))
            return jbs
        else:
            raise ValueError("Unexpected response format from GPT-4o")
    except Exception as e:
        print(f"Error parsing job listings: {e}")
        return []

# Function to process all PDFs in a folder
def process_pdfs(input_folder="pdfs"):
    if not os.path.exists(input_folder):
        os.makedirs(input_folder)

    for pdf_file in os.listdir(input_folder):
        if pdf_file.lower().endswith('.pdf'):
            pdf_path = os.path.join(input_folder, pdf_file)
            print(f"Processing {pdf_path}")

            # Create output filename by replacing .pdf with .json
            base_name = os.path.splitext(pdf_file)[0]
            output_file = os.path.join(input_folder, f"{base_name}.json")
            if os.path.exists(output_file):
                print(f"Skipping {pdf_file} as {output_file} already exists")
                continue

            all_job_listings = []

            doc = fitz.open(pdf_path)
            for page_num in range(len(doc)):
                print(f"Processing page {page_num + 1} of {len(doc)}")
                image_path = pdf_page_to_image(pdf_path, page_num)
                job_listings = extract_job_listings(image_path)
                all_job_listings.extend(job_listings)

            # Convert Pydantic models to dictionaries before JSON serialization
            all_job_listings_dicts = [listing.model_dump() for listing in all_job_listings]

                    # Save the results to a separate file for each PDF
            with open(output_file, 'w') as f:
                json.dump(all_job_listings_dicts, f, indent=2)
            print(f"Job listings saved to {output_file}")

# Run the processing
if __name__ == "__main__":
    process_pdfs(input_folder="./input_pdfs")
