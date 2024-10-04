import streamlit as st
from openai import OpenAI
import producepdf as pt

import PyPDF2

st.set_page_config(page_title="Resume Builder", page_icon="📝")

with st.sidebar:
    openai_api_key = st.text_input("OpenAI API Key", key="file_qa_api_key", type="password")

if openai_api_key:
    client = OpenAI(api_key=openai_api_key)

st.title("📝 Resume Builder")

uploaded_resume = st.file_uploader("Upload your resume", type=["pdf", "txt"])
uploaded_job_posting = st.file_uploader("Upload the job posting", type=["pdf", "txt"])

def read_pdf(file):
    pdf_reader = PyPDF2.PdfReader(file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def read_file(file):
    if file.type == "application/pdf":
        return read_pdf(file)
    elif file.type == "text/plain":
        return file.getvalue().decode("utf-8")
    else:
        return "Unsupported file type"

def response_to_markdown(markdown_text):
    return pt.convert_markdown_to_html(markdown_text)

generate_button = st.button("Generate Analysis")
html_text = ""
if generate_button:
    if not openai_api_key:
        st.info("Please add your OpenAI API key in the sidebar to continue.")
    elif not uploaded_resume or not uploaded_job_posting:
        st.info("Please upload both your resume and the job posting to proceed.")
    else:
        with st.spinner("Generating analysis..."):
            resume_text = read_file(uploaded_resume)
            job_posting_text = read_file(uploaded_job_posting)

            prompt = f"""
            I have a resume and a job posting. I need you to analyze them and suggest improvements to the resume to better match the job posting.

            Resume:
            {resume_text}

            Job Posting:
            {job_posting_text}

            Please provide the following:
            1. A summary of the key requirements from the job posting.
            2. An analysis of how well the resume matches these requirements.
            3. Specific suggestions for improving the resume to better align with the job posting.
            4. A rewritten version of the resume that incorporates these improvements.
            """
            response = client.chat.completions.create(model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that analyzes resumes and job postings."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=10000)

        st.write("### Suggestions")
        st.write(response.choices[0].message.content)  
        html_text = response_to_markdown(response.choices[0].message.content)
        pt.markdown_to_pdf(html_text, 'output_resume.pdf')