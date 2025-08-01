# This uses browser-use agents to go to indeed and grab job listings. 
from browser_use.llm import ChatOpenAI, ChatGoogle
from browser_use import Agent
from dotenv import load_dotenv
from browser_use import Agent, Controller
from browser_use.browser import BrowserSession
from browser_use.agent.views import ActionResult
import subprocess
import logging
import os
import json
logger = logging.getLogger(__name__)
import json
import hashlib
import shutil

def generate_dict_id_robust(dictionary):
    dict_str = json.dumps(dictionary, sort_keys=True)
    return hashlib.sha256(dict_str.encode()).hexdigest()


load_dotenv()

import asyncio
#from browser_use.browser.profile import BrowserProfile

# For now we will just stick with OpenAI's model since local mistral is having issues with context length limitation
#llm = ChatOpenAI(model="mistral-small", base_url="http://localhost:8080", api_key="sk-1111")
#page_extraction_llm = ChatOpenAI(model="gpt-4.1-mini")

#llm = ChatOpenAI(model="gpt-4.1")
#llm = ChatGoogle(model="gemini-2.0-flash-exp")
llm = ChatOpenAI(model="gpt-4.1")
#browser_profile = BrowserProfile(stealth = True)

#controller = Controller(exclude_actions=["extract_structured_data"])
controller = Controller()


@controller.action('Upload file to interactive element with filename')
async def upload_file(index: int, filename: str, browser_session: BrowserSession):
	# if path not in available_file_paths:
	# 	return ActionResult(error=f'File path {path} is not available')

	path = os.path.join("./agent_file_system/browseruse_agent_data/", filename)
	if not os.path.exists(path):
		return ActionResult(error=f'File {path} does not exist')

	file_upload_dom_el = await browser_session.find_file_upload_element_by_index(index, max_height=3, max_descendant_depth=3)

	if file_upload_dom_el is None:
		msg = f'No file upload element found at index {index}'
		logger.info(msg)
		return ActionResult(error=msg)

	file_upload_el = await browser_session.get_locate_element(file_upload_dom_el)

	if file_upload_el is None:
		msg = f'No file upload element found at index {index}'
		logger.info(msg)
		return ActionResult(error=msg)

	try:
		await file_upload_el.set_input_files(path)
		msg = f'Successfully uploaded file to index {index}'
		logger.info(msg)
		return ActionResult(extracted_content=msg, include_in_memory=True)
	except Exception as e:
		msg = f'Failed to upload file to index {index}: {str(e)}'
		logger.info(msg)
		return ActionResult(error=msg)

@controller.action('Get a resume for the current job')
async def get_resume_for_job(job_title: str, company_name: str, job_desc_file_path: str):
    try:
        if not os.path.exists("./agent_file_system/browseruse_agent_data/job_desc.md"):
            return ActionResult(error=f'File job_desc.md does not exist. You must save the job description before you can retrieve the resume.')

        if not os.path.exists("./agent_file_system/browseruse_agent_data/FinalLatexResume2025.pdf"):
            script_dir = os.path.dirname(__file__)
            wdir = os.path.join(script_dir, 'smolagents')
            subprocess.run(['python', 'custom-resume.py'], cwd=wdir, check=True) 
        msg = f'Successfully retrieved resume for current job. File saved as: FinalLatexResume2025.pdf'
        logger.info(msg)
        return ActionResult(extracted_content=msg, include_in_memory=True, attachments=["FinalLatexResume2025.pdf"])
    except Exception as e:
        msg = f'Failed to get resume for the current job'
        logger.info(msg)
        return ActionResult(error=msg)

	
async def main():
    master_file_path = "attempted_jobs.json"  # or "master_results.csv" for CSV format
    session = None

    # Initialize or load existing data (if file exists)
    try:
        with open(master_file_path, 'r') as f:
            existing_data = json.load(f)  # or pd.read_csv() for CSV
    except (FileNotFoundError, json.JSONDecodeError):
        existing_data = []

    with open("final_filtered_jobs.json") as f:
        job_list = json.load(f)

    print(f"Successfully loaded {len(job_list)} jobs from file.")
    for curr_job in job_list:
        if not all(key in curr_job for key in ["job_title", "company", "industry"]):
            continue
        
        location = "United States"
        if "location" in curr_job:
            location = curr_job["location"]
        
        if "Amazon" in curr_job["company"]:
            print("Skipping Amazon job")
            continue

        agent, session = await Agent.create_stealth_agent(
            task=f"""
                Your goal is to apply to the following job:
                "job_title": {curr_job["job_title"]},
                "company": {curr_job["company"]},
                "industry": {curr_job["industry"]},
                "location": {location}

                Follow these instructions for locating the job and applying to it:
                There are five stages: LOCATE THE JOB LISTING -> TAILOR YOUR RESUME -> APPLY TO THE JOB -> FIX ERRORS -> CONFIRM SUBMISSION
                DO NOT MOVE ON TO THE NEXT STAGE UNTIL YOU COMPLETE THE CURRENT STAGE YOU ARE ON.

                THE ONLY REASON YOU SHOULD EVER USE extract_structured_data IS for extracting job details in the TAILOR YOUR RESUME phase. NEVER USE IT FOR ANYTHING ELSE.

                First, LOCATE JOB LISTING:
                1. Use Google to search for the company's career page. Always start by searching for '[COMPANY] careers'
                2. In the Google search options, if you see a Greenhouse link for the company's career page prioritize clicking on that result.
                3. Search the careers page for the job that you are looking for.
                4. Once you find a match, click on the job to go to the job posting page. If you are asked about cookies and opting out, reject all cookies if possible OR click the 'X' button on the dialog at the bottom of the page.

                Next, TAILOR YOUR RESUME:
                5. Use extract_structured_data to extract ALL relevant job details listed on the job page including the job description, "What you’ll do", "Relevant skills and experience" and MAKE SURE to save them to a file called 'job_desc.md'.
                6. THEN MAKE SURE TO use the get_resume_for_job tool to retrieve the resume document so that you can have the resume in your filesystem. 

                Lastly, APPLY TO THE JOB:
                7. Now proceed to fill out the job application fields in the order that they appear on the page (top to bottom). 
                8. Consider each and every field one at a time:
                    - Decide whether to fill it.
                    - If you decide to fill the field: BEFORE USING input_text on any field: first use click_element_by_index to click on it, then use input_text.
                    - Double check that the value you entered makes sense.
                9. Scroll down a little to view the subsequent fields on the page.
                10. Repeat steps 7-9 until you reach the end of the page. Once you reach the end of the page, click the submit button.
                IMPORTANT NOTES:
                - For voluntary self-identification questions, always select "Decline to self identify"
                - If you ever see an option to "Autofill from resume" choose it and upload your resume.
                - When you reach the field/button for uploading a resume, DO NOT CLICK ON THE ATTACH BUTTON. Instead, use the upload_file tool with the button's index.
                - ANY FIELD WITH AN ASTERISK (usually a red asterisk) IS A REQUIRED FIELD THAT YOU MUST FILL.
            
                Last, FIX ERRORS:
                11. If nothing happens when you click the submit button, carefully review the fields and see if there is any red text indicating missing or incorrect values. Fix these errors and try resubmitting.
                12. Check to see if any of the SPECIAL CASES are applicable and have been handled properly.

                Finally, CONFIRM SUBMISSION:
                13. Look at the screenshot of the page and make sure it says the application was submitted successfully. DO NOT USE extract_structured_data for this.


                Here is applicant information that you might need:
                - Name: Daniel Phantom
                - Email: dphantom@gmail.com
                - Phone: +11234567890
                - Github: github.com/dphantom
                - LinkedIn URL: linkedin.com/in/danny-phantom
                - Current Location: New York, NY
                - Most recent employer: Google
                - US Citizen
                - Do not and will not need sponsorship for employment-based immigration.
                - Legally authorized to work in the United States.
                
                For generic questions like this, answer like this:
                    - How did you hear about us?: Facebook
                    - Are you currently a student?: No
                    - Have you interviewed with us before?: No

                SPECIAL CASES:
                If a page ever sends you a verification code to your email. FOLLOW THESE INSTRUCTIONS:
                    1. Go to gmail.com and click login
                    2. Enter this email address: d.phantom@gmail.com
                    3. Click continue
                    4. Enter this password: d.phantom
                    5. Click login and wait for the inbox to load.
                    6. Obtain the verification code and enter it where needed.

                If you ever encounter a Cloudflare verification checkbox, wait for the verification checkbox to appear, click it once, and wait for 10 seconds. Don't worry if you get redirected.

                If you ever encounter essay based application questions (such as "why do you want to work at our company"), answer them in a very enthusiastic and comprehensive manner. 

                If the application requires you to submit a video or provide something you don't have access to, then just fail to complete the task.

                If you are ever required to login to anything, use the following credentials: email: d.phantom@gmail.com, password: d.phantom72 and try to see if your account exists already.
                If you are ever required to create an account for anything, and you have verified that the credentials above don't work then create a new account with those credentials.

                """,
            llm=llm,
            file_system_path="./agent_file_system",
            controller=controller,
            browser_session=session,
            max_history_items=15
        )
        result = await agent.run()
        print(result)
        final_result = result.action_results()
        if final_result:
            final_result = final_result[-1]
            is_done = final_result.is_done
            success = final_result.success
            log_result = final_result.extracted_content

            job_uid = generate_dict_id_robust(curr_job)
            if os.path.exists("./agent_file_system/browseruse_agent_data/FinalLatexResume2025.pdf"):
                shutil.copy("./agent_file_system/browseruse_agent_data/FinalLatexResume2025.pdf", f"./tailored_docs/resume_{job_uid}.pdf")
                shutil.copy("./agent_file_system/browseruse_agent_data/job_desc.md", f"./tailored_docs/job_desc_{job_uid}.md")

            curr_job["is_done"] = is_done
            curr_job["success"] = success
            curr_job["log_result"] = log_result
            existing_data.append(curr_job)

            # Write back to file at each iteration
            with open(master_file_path, 'w') as f:
                json.dump(existing_data, f, indent=2)
        
        if len(session.browser_context.pages) >= 1:
            print("Cleaning up browser tabs from this session.")
            for tab in session.browser_context.pages[:]:
                await tab.close()

asyncio.run(main())
