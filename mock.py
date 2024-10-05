# steps:
# 1. A summary of the key requirements from the job posting.
import PyPDF2
from openai import OpenAI
import os
import dotenv
dotenv.load_dotenv()
import json
from typing import List, Dict


def read_pdf(file):
    pdf_reader = PyPDF2.PdfReader(file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

class MockInterviewer:
    def __init__(self, api_key=None, max_tokens=10000):
        if api_key is None: 
            api_key = os.environ.get("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key)
        self.max_tokens = max_tokens

    def _get_response(self, prompt):
        response = self.client.chat.completions.create(model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that analyzes resumes and job postings."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=self.max_tokens
        )
        return response.choices[0].message.content

    def _summarize_job_posting(self, job_posting_text):
        prompt = f"""
        This is a job posting. Please summarize the job posting. Make sure to mention the job title, 
        company, key requirements, responsibilities, and qualifications from the job posting,
        and other important information.

        job posting:
        {job_posting_text}

        summary:
        """
        response = self._get_response(prompt)
        self.job_summary = response
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
        self.resume_summary = response
        return response

    def _brainstorm_interview_ideas(self):
        prompt = f"""
        Based on the summary of the resume and job posting, please suggest key interview questions that
        will help assess the candidate's fit for the job.

        Resume: 
        {self.resume_summary}
        
        Job Posting:
        {self.job_summary}

        Questions ideas:
        """ 
        response = self._get_response(prompt)
        self.question_ideas = response
        return response

    def preprocess(self, job_posting_text, resume_text):
        self._summarize_job_posting(job_posting_text)
        self._analyze_resume(resume_text)
        self._brainstorm_interview_ideas()
    
    def start_interview(self):
        prompt = f"""
        Hello ChatGPT, you are the interviewer for the following position
        
        {self.job_summary}
        
        I want you to run an interview session with me. Make sure you structure it as a question-and-answer session, 
        with each question followed by a response from me.

        Make it clear when the interview is completed by saying OVER. At the end, I would like for you to evaluate my responses and make a final hiring recommendation based on my performance in the interview. At the very end, give an expansive evaluation, and include any recommendations that you would have on improving my answers

        This is a real time, turn based exercise. After each question, you should stop, let me input a response for each question in turn. Do not say anything that
        will make me feel you are not a real interviewer.

        Here are my resume:
        {self.resume_summary}

        Feel free to leverage the ideas below:
        {self.question_ideas}
        
        Let's start the interview session now.
        """
        response = self._get_response(prompt)
        return response

    def ask_question(self):
        prompt = f"""
        Question:
        """
        response = self._get_response(prompt)
        return response

    def save(self, filename):
        data = {
            "job_summary": self.job_summary,
            "resume_summary": self.resume_summary,
            "question_ideas": self.question_ideas
        }
        with open(filename, "w") as f:
            json.dump(data, f, indent=4)
        
    @classmethod
    def load(cls, filename):
        with open(filename, "r") as f:
            data = json.load(f)
        mock_interviewer = cls()
        mock_interviewer.job_summary = data["job_summary"]
        mock_interviewer.resume_summary = data["resume_summary"]
        mock_interviewer.question_ideas = data["question_ideas"]
        return mock_interviewer


class MockInterviewee:
    def __init__(self, api_key=None, max_tokens=10000):
        if api_key is None:
            api_key = os.environ.get("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key)
        self.max_tokens = max_tokens
        self.resume_summary = ""
        self.job_summary = ""

    def _get_response(self, prompt, history):
        messages = [
            {"role": "system", "content": "You are an interviewee for a job position. Try to respond to the questions as best as you can."},
        ]
        for entry in history:
            messages += [
                {"role": "assistant", "content": entry["question"]},
                {"role": "user", "content": entry["answer"]}
            ]

        messages += [
            {"role": "user", "content": prompt}
        ]
        
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an interviewee for a job position. Try to respond to the questions as best as you can."},
            ]
            for entry in history:
                messages += [
                    {"role": "assistant", "content": entry["question"]},
                    {"role": "user", "content": entry["answer"]}
                ]
            messages += [
                {"role": "user", "content": prompt}
            ],
            max_tokens=self.max_tokens
        )
        return response.choices[0].message.content

    def prepare_for_interview(self, resume_summary: str, job_summary: str):
        self.resume_summary = resume_summary
        self.job_summary = job_summary

    def answer_question(self, question: str, history = []) -> str:
        prompt = f"""
        You are a job candidate interviewing for the following position:
        {self.job_summary}

        Your resume summary:
        {self.resume_summary}

        Your previous questions and answers with the interviewer:

        """
        + "\n".join([f"Q: {entry['question']}\nA: {entry['answer']}" for entry in self.history]) + \
        f"""

        The interviewer has now asked you the following question:
        {question}

        Please provide a thoughtful and relevant answer to this question, showcasing your skills and experience as described in your resume summary. Keep your answer concise but informative.

        Your answer:
        """
        response = self._get_response(prompt)
        self.history.append({"question": question, "answer": response})
        return response

    def forget_history(self):
        self.history = []


def conduct_mock_interview(interviewer: MockInterviewer, interviewee: MockInterviewee) -> List[Dict[str, str]]:
    question = interviewer.start_interview()
    answer = interviewee.answer_question(question)
    history = [{"question": question, "answer": answer}]
    
    interview_script = interviewer.ask_question()
    questions = [q.strip() for q in interview_script.split('\n') if q.strip().endswith('?')]
    return interviewee.run_mock_interview(questions)

if __name__ == '__main__':
    job_posting_text = read_pdf("data/job_posting.pdf")
    resume_text = read_pdf("data/resume.pdf")

    cached_data = "mock_interview_data.json"
    if not os.path.exists(cached_data):
        mock_interviewer = MockInterviewer()
        mock_interviewer.preprocess(job_posting_text, resume_text)
        mock_interviewer.save(cached_data)
    else:
        mock_interviewer = MockInterviewer.load(cached_data)

    mock_interviewee = MockInterviewee()
    mock_interviewee.prepare_for_interview(mock_interviewer.resume_summary, mock_interviewer.job_summary)

    interview_log = conduct_mock_interview(mock_interviewer, mock_interviewee)

    print("Mock Interview Results:")
    for entry in interview_log:
        print(f"Q: {entry['question']}")
        print(f"A: {entry['answer']}")
        print()
