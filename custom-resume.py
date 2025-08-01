import os
import openai
from openai import OpenAI
from dotenv import load_dotenv
import json

from pydantic import BaseModel
from typing import List
import datetime

# Initialize OpenAI client
load_dotenv()
client_local = OpenAI(base_url="http://localhost:8080", api_key="sk-1111")  # Replace with your actual API key
client = OpenAI()
#client_local = OpenAI()

class BulletsA(BaseModel):
    bullet_a1: str
    bullet_a2: str
    bullet_a3: str

class SkillsA(BaseModel):
    skills_a1: str
    skills_a2: str

def get_bullets_a(job_desc):
    prompt = f"""
            Suppose that you are a hiring manager and have posted a job description for a role.

            Thousands of candidates have applied to the role and out of all of them one stands out as the best fit. The candidate’s name is Jim. You know that the Greenhouse application system relies on keyword matching to rank resumes so that you can make sure to only interview the most promising candidates.
            Resume bullet points are usually kept concise for readability.

            The internal company recruiter you work with has made a bet with you that if you can guess select parts of Jim’s resume exactly, then you will win a cruise vacation to the Bahamas.
            
            Here is what you will need to guess correctly:

            What are the three bullet points on Jim’s resume for his most recent position at Google?

            This is what you know about Jim’s most recent position:
                - Company: Google - Ads Team
                - Position: Machine Learning Engineer 
                - Dates worked: Dec 2021 - Present 
                            
                - The candidate did not release any publications while at this position.

                - Google is a large tech company which manages, Gmail, Google Search etc.

            So given what you know, you will guess in an informed and intelligent manner. For example: If you know that Jim was working at a hedge fund, you wouldn't guess that he was working on ad infrastructure there since it is unlikely that a hedge fund will run ads.

            Today’s date is August 1st 2025.
                            
            Here is the job description for the role you posted: 

            {job_desc}
            """

    response_raw = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {
                "role": "system",
                "content": prompt
            },
        ],
        max_tokens=2000
    )

    # Get the parsed output
    response_data_raw = response_raw.choices[0].message.content

    while True:
        response = client_local.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": f"""Extract only the three proposed resume bullet points and format them into LaTeX. 
                    Follow these exact instructions:
                    1. Remove any HTML bold formatting (double asterisks).
                    2. Selectively choose keywords to emphasize and then use LaTeX's \\textbf{{...}} format to bold them. Be very selective in what you bold and don't bold too many things. Each bullet should typically only have 1-2 bolded words.
                    3. Remove all other HTML formatting tags
                    4. Preserve all other text exactly as-is
                    5. Do not use itemize or any bullet formatting - just the plain text with proper LaTeX bold formatting
                    6. The output should be three separate strings with LaTeX formatting only

                    Example input: "Developed **and implemented** machine learning models"
                    Example output: "Developed and implemented \\textbf{{machine learning}} models"
                                {response_data_raw}    

                                    Please respond only with valid JSON in the specified structured format.
                                """
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Respond ONLY with valid JSON in the following format:",
                            "text": """[
                                {
                                    "bullet_a1": "string",
                                    "bullet_a2": "string",
                                    "bullet_a3": "string",
                                }
                            ]"""
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
            keynames = [jkey for jkey in response_json.keys()]
            print(keynames)
            print(type(response_json))
            if isinstance(response_json, list):
                # Directly use the list if it's already in correct format
                return [BulletsA.model_validate(job) for job in response_json]
            elif isinstance(response_json, dict) and len(keynames) == 1:
                # Handle the case where jobs are under a 'jobs' key
                print("Problem case")
                return BulletsA.model_validate(response_json[keynames[0]])
            elif isinstance(response_json, dict) and len(keynames) == 3:
                return BulletsA.model_validate(response_json)
            else:
                raise ValueError("Unexpected response format from GPT-4o")
        except Exception as e:
            print(f"Error parsing job listings: {e}")
            # Create a debug log file with the problem response
            error_log = {
                "error": str(e),
                "response_json": response_json,
                "timestamp": datetime.datetime.now().isoformat()
            }

            # Create debug directory if it doesn't exist
            os.makedirs("./debug_logs", exist_ok=True)

            # Generate a unique filename with timestamp
            filename = f"./debug_logs/error_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

            # Save the error log to file
            with open(filename, 'w') as f:
                json.dump(error_log, f, indent=2)
            return []


def get_bullets_b(job_desc):
    prompt = f"""
            Suppose that you are a hiring manager and have posted a job description for a role.

            Thousands of candidates have applied to the role and out of all of them one stands out as the best. The candidate’s name is Jim. You know that the Greenhouse application system relies on keyword matching to rank resumes so that you can make sure to only interview the most promising candidates.
            Resume bullet points are usually kept concise for readability.

            The internal company recruiter you work with has made a bet with you that if you can guess select parts of Jim’s resume exactly, then you will win a cruise vacation to the Bahamas.

            Here is what you will need to guess correctly:

            What are the three bullet points on Jim’s resume for his recent position at Microsoft?

            This is what you know about one of Jim’s recent position:

            Company: Hudson River Trading
            Position: Chief Data Shaman
            Dates worked: Jan 2022 - August 2022

            Hudson River Trading is a large HFT hedge fund headquartered in New York.

            Today’s date is August 1st 2025.
                            
            Here is the job description for the role you posted: 

            {job_desc}
            """

    response_raw = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {
                "role": "system",
                "content": prompt
            },
        ],
        max_tokens=2000
    )

    # Get the parsed output
    response_data_raw = response_raw.choices[0].message.content

    response = client_local.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": f"""Extract only the three proposed resume bullet points and format them into LaTeX. 
                Follow these exact instructions:
                1. Remove any HTML bold formatting (double asterisks).
                2. Selectively choose keywords to emphasize and then use LaTeX's \\textbf{{...}} format to bold them. Be very selective in what you bold and don't bold too many things. Each bullet should typically only have 1-2 bolded words.
                3. Remove all other HTML formatting tags
                4. Preserve all other text exactly as-is
                5. Do not use itemize or any bullet formatting - just the plain text with proper LaTeX bold formatting
                6. The output should be three separate strings with LaTeX formatting only

                Example input: "Developed **and implemented** machine learning models"
                Example output: "Developed and implemented \\textbf{{machine learning}} models"
                               {response_data_raw}    

                                Please respond only with valid JSON in the specified structured format.
                            """
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Respond ONLY with valid JSON in the following format:",
                        "text": """[
                            {
                                "bullet_a1": "string",
                                "bullet_a2": "string",
                                "bullet_a3": "string",
                            }
                        ]"""
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
        keynames = [jkey for jkey in response_json.keys()]
        print(type(response_json))
        if isinstance(response_json, list):
            # Directly use the list if it's already in correct format
            return [BulletsA.model_validate(job) for job in response_json]
        elif isinstance(response_json, dict) and len(keynames) == 1:
            # Handle the case where jobs are under a 'jobs' key
            return BulletsA.model_validate(response_json[keynames[0]])
        elif isinstance(response_json, dict) and len(keynames) == 3:
            return BulletsA.model_validate(response_json)
        else:
            raise ValueError("Unexpected response format from GPT-4o")
    except Exception as e:
        print(f"Error parsing job listings: {e}")
        error_log = {
            "error": str(e),
            "response_json": response_json,
            "timestamp": datetime.datetime.now().isoformat()
        }

        # Create debug directory if it doesn't exist
        os.makedirs("debug_logs", exist_ok=True)

        # Generate a unique filename with timestamp
        filename = f"debug_logs/error_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        # Save the error log to file
        with open(filename, 'w') as f:
            json.dump(error_log, f, indent=2)

        return []


# Run the processing
if __name__ == "__main__":
    # Read job description from file
    with open('./agent_file_system/browseruse_agent_data/job_desc.md', 'r') as file:
        desc = file.read()

    a = get_bullets_a(desc)
    print("RESULT: ", a)
    b = get_bullets_b(desc)
    print("RESULT_2: ", b)

    # First copy "./master_resume_template.tex" into "./latex/main.tex"
    import shutil
    import subprocess
    shutil.copy('./master_resume_template.tex', './latex/main.tex')

    # Open the main.tex file for reading and writing
    with open('./latex/main.tex', 'r+') as file:
        content = file.read()

        # Replace the placeholders with the bullet points from the results
        if a and b:
            content = content.replace("BULLETA1", a.bullet_a1.encode('unicode_escape').decode('utf-8').replace('%', '\\%'))
            content = content.replace("BULLETA2", a.bullet_a2.encode('unicode_escape').decode('utf-8').replace('%', '\\%'))
            content = content.replace("BULLETA3", a.bullet_a3.encode('unicode_escape').decode('utf-8').replace('%', '\\%'))
            content = content.replace("BULLETB1", b.bullet_a1.encode('unicode_escape').decode('utf-8').replace('%', '\\%'))
            content = content.replace("BULLETB2", b.bullet_a2.encode('unicode_escape').decode('utf-8').replace('%', '\\%'))
            content = content.replace("BULLETB3", b.bullet_a3.encode('unicode_escape').decode('utf-8').replace('%', '\\%'))

            # Move the file pointer to the beginning of the file
            file.seek(0)
            # Write the modified content back to the file
            file.write(content)
            # Truncate the file if the new content is shorter than the original
            file.truncate()

    # Then run the following shell commmands from inside the ./latex folder:
    # first, this: latexmk --pdf --interaction=nonstopmode main.tex
    # then, this: latexmk -c

    # Change to the latex directory
    latex_dir = './latex'

    try:
        # First command: latexmk --pdf --interaction=nonstopmode main.tex
        subprocess.run(['latexmk', '--pdf', '--interaction=nonstopmode', 'main.tex'],
                      cwd=latex_dir, check=False)

        # Second command: latexmk -c
        subprocess.run(['latexmk', '-c'],
                      cwd=latex_dir, check=False)

        print("PDF generation completed successfully")

    except subprocess.CalledProcessError as e:
        print(f"Error during PDF generation: {e}")
        # Second command: latexmk -c
        subprocess.run(['latexmk', '-c'],
                      cwd=latex_dir, check=False)

    except FileNotFoundError:
        print("latexmk command not found. Please ensure LaTeX is properly installed.")

    shutil.copy('./latex/main.pdf', './agent_file_system/browseruse_agent_data/FinalLatexResume2025.pdf')