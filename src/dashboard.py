import streamlit as st
from utils import *

st.title("Welcome to Recruiting AI!")

resume = st.file_uploader('To personalize your experience, please upload your resume as a PDF', type="pdf")

if resume is not None:
    try:
        resume_image = convert_from_bytes(resume.read())
        if st.button("Preview resume"):
            st.image(resume_image)

    except Exception as e:
        st.error(f"Error reading resume file: {e}")

job_posting = st.text_input('Optional: upload a job posting you are interested in. To bypass this step, please write "None".') 

if resume is not None and job_posting != '':
    try:
        base64_img_data_url = get_base64_pdf_image(resume_image)
        if st.button("Begin practice interview"):
            st.write("feature coming soon!")

        if st.button("Generate sample questions and responses"):
            with st.spinner('Generating questions and responses...'):
                summary =  generate_questions(job_posting, base64_img_data_url)
                st.subheader("Example questions and responses:")
                st.write(summary)

        # if st.button("Generate cover letter"):
        #     with st.spinner('Generating cover letter...'):
        #         summary = generate_cover_letter(job_posting, base64_img_data_url)
        #         st.subheader("Example cover letter:")
        #         st.write(summary)
    
    except Exception as e:
        st.error(f"Please upload a resume: {e}")
