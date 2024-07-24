from openai import OpenAI
import base64
from pdf2image import convert_from_bytes
from io import BytesIO
import re
import asyncio
import uuid
from hume import HumeVoiceClient, VoiceConfig
from twilio.rest import Client
import os
from dotenv import load_dotenv

load_dotenv()
OPENAI_KEY = os.getenv("OPENAI_KEY")
HUME_API_KEY = os.getenv("HUME_API_KEY")
TWILIO_ACCOUNT_SID=os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN=os.getenv("TWILIO_AUTH_TOKEN")
CONFIG_ID=None
openAIClient = OpenAI(api_key=OPENAI_KEY)

humeClient = HumeVoiceClient(HUME_API_KEY)

def get_base64_pdf_image(resume_image):    
    # Assuming we want the first page
    first_page_image = resume_image[0]

    # Save the image to a BytesIO object
    buffered = BytesIO()
    first_page_image.save(buffered, format="JPEG")
    
    # Get the base64 encoded string
    base64_encoded = base64.b64encode(buffered.getvalue()).decode('utf-8')
    
    # Return as data URL
    return f"data:image/jpeg;base64,{base64_encoded}"


def generate_questions(job_posting, base64_img_data_url):
    if job_posting == "None":
        prompt = """You are a job recruiter. 
        You are given a resume and your job is to provide a list of questions that you want to ask based on the resume that you are given, 
        and sample responses the interviewee can provide based on this resume. Please have each sample response under each potential question."""
    else:
        prompt = f"""You are a recruiter who is hiring for the job based on its description. The link is here: {job_posting}
        You are given a resume and your job is to provide a list of questions that you want to ask 
        based on the resume that you are given and sample responses that the interviewee can provide. 
        Please have each sample response under each potential question. Also consider the job description, 
        and your company knowledge which you will understand via a web search. Start off with general questions first, 
        like 'tell me about yourself'. Try to simulate real-life interview questions as much as possible with the context of the job. 
        You need to understand the company and what they do via a web search."""
    
    response = openAIClient.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": [{"type": "text", "text": f"Link: {job_posting}"},
                                                    {"type": "image_url", 
                                                     "image_url": {"url": base64_img_data_url}}]}],
                    max_tokens=2000, temperature=0.6)
    summary = response.choices[0].message.content.strip()
    print(questions_list(summary))
    return summary

def questions_list(questions):
    prompt = "You need to take the user prompt and parse out ONLY the interview questions. Your response should only contain the interview questions, making sure they are numbered."
    input_params = {
        "model": "gpt-3.5-turbo",
        "messages":[{"role": "system", "content": prompt},
                    {"role": "user", "content": [{"type": "text", "text": f"{questions}"},]}],
        "temperature": 0.1,
        "max_tokens": 2000

    }
    response = openAIClient.chat.completions.create(**input_params).choices[0].message.content.strip()
    return response

# Configuring Hume AI Prompt

def generate_unique_id():
    return str(uuid.uuid4())

def make_prompt_and_config(name="Toufiq", link="https://wellfound.com/jobs/3045197-senior-data-scientist?utm_campaign=google_jobs_apply&utm_source=google_jobs_apply&utm_medium=organic"):
    
    prompt = f"""You are a recruiter who is hiring for a given job based on its description. 
    The link to the job is here: {link}

    Make sure you do a web search on this job description to understand it before talking to the client.
    You are given a resume and your job is to assess candidate fit based on your understanding of the job description, 
    the organization that is hiring for the particular role, and the candidate's experiences as outlined in their resume. 
    You will do this by asking behavioral questions pertaining to the role. Assume that you are on call with the candidate.

    Make sure to address the candidate by their name, {name}.
    """
    
    # Create prompt    
    # Create config with the prompt
    config: VoiceConfig = humeClient.create_config(
        name= generate_unique_id(),
        prompt= prompt
    )
    
    return config.id

# Usage

async def make_twilio_call(phone_number, config_id=CONFIG_ID):
    account_sid = TWILIO_ACCOUNT_SID
    auth_token = TWILIO_AUTH_TOKEN
    twilio_client = Client(account_sid, auth_token)
    evi_webhook_url = f"https://api.hume.ai/v0/evi/twilio?config_id={config_id}&api_key={HUME_API_KEY}"

    call = twilio_client.calls.create(
        url=evi_webhook_url,
        to=phone_number,
        from_="15103986913"
    )
    # Wait for the call to complete
    while call.status != 'completed':
        await asyncio.sleep(1)
        call = twilio_client.calls(call.sid).fetch()

    client.delete_config(config_id)


    

# Usage
async def main():
    phone_number = input("Enter phone number: ")
    await make_twilio_call(phone_number, make_prompt_and_config())

asyncio.run(main())








