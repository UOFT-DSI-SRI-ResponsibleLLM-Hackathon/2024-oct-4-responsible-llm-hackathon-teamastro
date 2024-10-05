import dotenv
dotenv.load_dotenv()
import streamlit as st
import os
from openai import OpenAI
import producepdf as pt
from streamlit_option_menu import option_menu
import re

import PyPDF2

# utility functions
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

def markdown_to_pdf(markdown_text, output_file):
    pt.convert_html_to_pdf(markdown_text, output_file)

openai_api_key = os.environ.get("OPENAI_API_KEY", None)

class Agent:
    def __init__(self, client=None, max_tokens=5000):
        if client is None:
            self.client = OpenAI(api_key=openai_api_key)
        else:
            self.client = client
        self.max_tokens = max_tokens

    def _get_response(self, prompt, system_message=None):
        if system_message is None:
            system_message = "You are a helpful assistant that analyzes resumes and job postings."
        response = self.client.chat.completions.create(model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            max_tokens=self.max_tokens
        )
        return response.choices[0].message.content

    def _analyze_job_posting(self, job_posting_text):
        prompt = f"""
        This is a job posting. Please summarize the job posting. Make sure to mention the job title, 
        company, key requirements, responsibilities, and qualifications from the job posting,
        and other important information.

        job posting:
        {job_posting_text}

        summary:
        """
        response = self._get_response(prompt)
        return response

    def _analyze_resume(self, resume_text):
        prompt = f"""
        This is a resume. Please summarize key information from the resume. Make sure to mention the candidate's name,
        work experience, skills, education, and other relevant details.

        resume:
        {resume_text}

        summary:
        """
        response = self._get_response(prompt)
        return response

    def _compare_resume_to_job_posting(self, resume_summary, job_summary):
        prompt = f"""
        I have a resume and a job posting. I need you to analyze them and suggest improvements to the resume to better match the job posting.

        Summary of resume:
        {resume_summary}

        Summary of job posting:
        {job_summary}

        Please provide the following:
        1. A summary of the key requirements from the job posting.
        2. An analysis of how well the resume matches these requirements.
        3. Specific suggestions for improving the resume to better align with the job posting.
        """
        response = self._get_response(prompt)
        return response

    def _revise_resume(self, resume_text, suggestions):
        prompt = f"""
        I have a resume and suggestions for improving it. Please revise the resume to incorporate the suggestions.
        
        Resume:
        {resume_text}
        
        Suggestions:
        {suggestions}
        
        Please provide the revised resume in markdown format.

        Revised Resume:
        """
        response = self._get_response(prompt)
        return response

    def _extract_modified_resume(self, revised_resume):
        """Extracts markdown text embedded between triple backticks in a response."""
        # Regular expression pattern to match markdown between triple backticks
        pattern = r"```(?:markdown)?\s*([\s\S]*?)\s*```"
    
        # Find all matches in the response
        matches = re.findall(pattern, revised_resume, re.IGNORECASE)
    
        if matches:
            return matches[0].strip()
        else:
            return revised_resume

    def analyze(self, resume_text, job_posting_text):
        job_summary = self._analyze_job_posting(job_posting_text)
        resume_summary = self._analyze_resume(resume_text)
        analysis = self._compare_resume_to_job_posting(resume_summary, job_summary)
        revised_resume = self._revise_resume(resume_text, analysis)
        # parse the response to extract the relevant information
        revised_resume_parsed = self._extract_modified_resume(revised_resume)
        res = {
            "analysis": analysis,
            "job_summary": job_summary,
            "resume_summary": resume_summary,
            "revised_resume": revised_resume,
            "revised_resume_parsed": revised_resume_parsed
        }
        return res
    
# ============
#   main app
# ============

st.set_page_config(page_title="AI Resume Builder", page_icon="📝")

#create the side bar
with st.sidebar:
    selected = option_menu("Options", 
                           ["Resume builder",
                            "Mock interview", 
                            ], 
                            menu_icon='robot',
                            icons=['chat-dots-fill', 'image-fill', 'textarea-t', 'patch-question-fill'],
                            default_index=0
                           )

if selected == "Resume builder":
    st.title("📝 Resume Builder")

    uploaded_resume = st.file_uploader("Upload your resume", type=["pdf", "txt"])
    uploaded_job_posting = st.file_uploader("Upload the job posting", type=["pdf", "txt"])

    # Initialize session state variables
    if 'generate_button' not in st.session_state:
        st.session_state.generate_button = False
    if 'response' not in st.session_state:
        st.session_state.response = {}

    generate_button = st.button("Generate Analysis")
    if generate_button:
        st.session_state.generate_button = True

    if st.session_state.generate_button:
        if not openai_api_key:
            st.info("Please add your OpenAI API key in the environment to continue.")
        elif not uploaded_resume or not uploaded_job_posting:
            st.info("Please upload both your resume and the job posting to proceed.")
        else:
            with st.spinner("Generating analysis..."):
                resume_text = read_file(uploaded_resume)
                job_posting_text = read_file(uploaded_job_posting)

                if st.session_state.response != {}:
                    pass
                else:
                    agent = Agent()
                    response = agent.analyze(resume_text, job_posting_text)
                    st.session_state.response = response

            st.write("### Analysis")
            response = st.session_state.response
            st.write(response['analysis'])  
            html_text = response_to_markdown(response['revised_resume_parsed'])
            pt.markdown_to_pdf(html_text, 'output_resume.pdf')

            st.write("### Download Resume")

            # Provide a download button for the generated PDF
            pdf_path = 'output_resume.pdf'
            with open(pdf_path, "rb") as pdf_file:
                pdf_bytes = pdf_file.read()
                st.download_button(
                    label="Download resume PDF",
                    data=pdf_bytes,
                    file_name="generated_resume.pdf",
                    mime="application/pdf"
                )

