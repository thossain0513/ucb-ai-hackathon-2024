from openai import OpenAI
import base64
from pdf2image import convert_from_bytes
from io import BytesIO
import re

client = OpenAI(api_key='sk-proj-8h8YSkEOQss5XNj53ZO9T3BlbkFJvqDTvPIoHDnkuK48aBi8')

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
        prompt = "You are a job recruiter. You are given a resume and your job is to provide a list of questions that you want to ask based on the resume that you are given, and sample responses the interviewee can provide based on this resume. Please have each sample response under each potential question."
    else:
        # prompt = "You are a recruiter who is hiring for the job at the provided link. You are given a resume and your job is to provide a list of questions that you want to ask based on the resume that you are given and the job posting, and sample responses the interviewee can provide based on this resume. Please make sure the questions are as specific to the job posting as possible, including questions involving specific job requirements and responsibilities. Please have each sample response under each potential question."

        prompt = "You are a recruiter who is hiring for a given job based on its description. You are given a resume and your job is to provide a list of questions that you want to ask based on the resume that you are given and sample responses that the interviewee can provide. Please have each sample response under each potential question. Also consider the job description, and your company knowledge which you will understand via a web search. Start off with general questions first, like 'tell me about yourself'. Try to simulate real-life interview questions as much as possible with the context of the job. You need to understand the company and what they do via a web search."
    
    response = client.chat.completions.create(
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
    prompt = "You need to take the user prompt and parse out ONLY the interview queestions. Your response should only contain the interview questions, making sure they are numbered."
    input_params = {
        "model": "gpt-3.5-turbo",
        "messages":[{"role": "system", "content": prompt},
                    {"role": "user", "content": [{"type": "text", "text": f"{questions}"},]}],
        "temperature": 0.1,
        "max_tokens": 2000

    }
    response = client.chat.completions.create(**input_params).choices[0].message.content.strip()
    return response



#def generate_cover_letter








