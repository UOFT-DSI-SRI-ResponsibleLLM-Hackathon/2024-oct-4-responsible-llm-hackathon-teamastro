import PyPDF2
from openai import OpenAI
import os
import dotenv
import json

# Load environment variables
dotenv.load_dotenv()

def read_pdf(file):
    pdf_reader = PyPDF2.PdfReader(file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text


class MockInterviewer:
    def __init__(self, api_key=None, max_tokens=1000):
        if api_key is None: 
            api_key = os.environ.get("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key)
        self.max_tokens = max_tokens

    def _get_response(self, prompt):
        response = self.client.chat.completions.create(model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": "You are a interviewer thats interviewing someone applying for a job."},
                      {"role": "user", "content": prompt}],
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
        self.question_ideas = response.split('\n')  # Split into a list of questions
        return self.question_ideas

    def preprocess(self, job_posting_text, resume_text):
        self._summarize_job_posting(job_posting_text)
        self._analyze_resume(resume_text)
        self._brainstorm_interview_ideas()
    
    def run_mock_interview(self):
        prompt = f"""
        Hello ChatGPT, you are the interviewer for the following position
        
        {self.job_summary}
        
        I want you to run an interview session with me. Make sure you structure it as a question-and-answer session, 
        with each question followed by a response from me.

        Make it clear when the interview is completed. At the end, I would like for you to evaluate my responses and make a final hiring recommendation based on my performance in the interview. At the very end, give an expansive evaluation, and include any recommendations that you would have on improving my answers

        Here are my resume:
        {self.resume_summary}

        Feel free to leverage the ideas below:
        {self.question_ideas}
        
        Let's start the interview session now.
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
        api_key = os.environ.get("OPENAI_API_KEY")  # Load the API key from the environment
        mock_interviewer = cls(api_key=api_key)  # Pass the API key when initializing
        mock_interviewer.job_summary = data["job_summary"]
        mock_interviewer.resume_summary = data["resume_summary"]
        mock_interviewer.question_ideas = data["question_ideas"]
        return mock_interviewer



class Student:
    def __init__(self, name, resume_details, mock_interviewer):
        self.name = name
        self.resume_details = resume_details
        self.mock_interviewer = mock_interviewer

    def respond_to_question(self, question):
        if "experience" in question.lower():
            return f"My experience includes {self.resume_details['experience']}."
        elif "skills" in question.lower():
            return f"I have skills in {', '.join(self.resume_details['skills'])}."
        elif "education" in question.lower():
            return f"I completed my {self.resume_details['education']}."
        else:
            initial_response = "That's a great question! I would approach it by"
            prompt = f"{initial_response} providing a detailed answer to the question: '{question}'"
            # AI response for generic questions
            ai_generated_response = self.mock_interviewer._get_response(prompt)
            return f"{initial_response} {ai_generated_response}"
        
    def get_resume_summary(self):
        summary = f"{self.name} has experience in {self.resume_details['experience']}, with skills in {', '.join(self.resume_details['skills'])}. "
        summary += f"I have completed {self.resume_details['education']}."
        return summary

    def ask_question(self, question):
        prompt = f"{self.name} asks: {question}"
        response = self.mock_interviewer._get_response(prompt)
        return response


if __name__ == '__main__':
    # Load job posting and resume text from PDF
    job_posting_text = read_pdf("data/job_posting.pdf")
    resume_text = read_pdf("data/resume.pdf")

    cached_data = "mock_interview_data.json"
    if not os.path.exists(cached_data):
        mock_interviewer = MockInterviewer()
        mock_interviewer.preprocess(job_posting_text, resume_text)
        mock_interviewer.save(cached_data)
    else:
        mock_interviewer = MockInterviewer.load(cached_data)

    # Create a student instance
    student_name = "Bob Jeff"
    resume_details = {
        'experience': '3 years in data analysis and machine learning projects',
        'skills': ['Python', 'Machine Learning', 'Data Visualization'],
        'education': 'Bachelor of Science in Statistics'
    }
    student = Student(student_name, resume_details, mock_interviewer)

    # Start an interactive conversation
    print("Welcome to the Mock Interview!")
    
     # Counter for the number of replies
    reply_count = 0
    max_replies = 3  # Limit the total number of replies

    while reply_count < max_replies:
        for question in mock_interviewer.question_ideas:  # Iterate through all questions
            if reply_count >= max_replies:
                break  # Exit if the maximum number of replies is reached

            print(f"Interviewer: {question}")
            response = student.respond_to_question(question)
            print(f"{student.name}: {response}")
            reply_count += 1
            
            # Optionally, generate and ask a follow-up question
            follow_up_prompt = f"Based on the previous response: '{response}', generate a follow-up question."
            follow_up_question = mock_interviewer._get_response(follow_up_prompt)
            print(f"Interviewer: {follow_up_question}")
            follow_up_response = student.respond_to_question(follow_up_question)
            print(f"{student.name}: {follow_up_response}")
            reply_count += 1

            # Check if the maximum number of replies is reached
            if reply_count >= max_replies:
                break

        # Check if the interview should continue or end
        continue_interview = input("Do you want to continue the interview? (yes/no): ").strip().lower()
        if continue_interview == 'no':
            break
        else:
            max_replies=0


    # Final evaluation
    evaluation = mock_interviewer.run_mock_interview()
    print("Mock Interview Completed!")
    print(evaluation)
