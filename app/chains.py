import os
from groq import Groq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.exceptions import OutputParserException
from dotenv import load_dotenv

# Load .env from the repo root (cwd) and app folder as a fallback.
# Use override=True so a stale Windows env var doesn't keep breaking the app.
load_dotenv(override=True)
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'), override=True)

class Chain:
    def __init__(self):
        api_key = (os.getenv("GROQ_API_KEY") or "").strip()
        if not api_key:
            raise ValueError("GROQ_API_KEY not found. Please set it in .env file or environment variables.")

        if any(ch.isspace() for ch in api_key):
            raise ValueError("GROQ_API_KEY contains whitespace. Remove spaces/newlines from the key in your .env.")

        self.model = os.getenv("GROQ_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")
        self.client = Groq(api_key=api_key)

    def _chat(self, prompt):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        return response.choices[0].message.content or ""

    def extract_jobs(self,cleaned_text):
        prompt_extract = PromptTemplate.from_template(
            """
            ### Scraped text from website:
            {page_data} 
            ### INSTRUCTION:
            The scraped text is from the career's page of a website.
            Your job is to extract the job postings and return them in JSON format containing the following keys: 'role', 'experience', 'skills' and 'description'.
            For skills, provide them as a comma-separated string.
            Only return the valid JSON.
            ### NO PREAMBLE only give me the json object
            """
        )       

        prompt = prompt_extract.format(page_data=cleaned_text)
        res = self._chat(prompt)

        try:
            json_parser = JsonOutputParser()
            res = json_parser.parse(res)
        except OutputParserException:
            raise OutputParserException("Context too big...")
        return res if isinstance(res,list) else [res]
    
    def write_mail(self,job,links):
        prompt_email = PromptTemplate.from_template(
            """
            ### JOB DESCRIPTION
            {job_description}

            ### INSTRUCTION:
            You are Manideep, a business development executive at Anarch. Anarch is an AI and software solution company focused on seamless integration of business processes through automated tools. Over our experience, we have empowered numerous enterprises with tailored solutions, process optimization, cost reduction and heightened overall efficiency.
            Your job is to write a cold email to the client regarding the job mentioned above describing the capability in fulfilling their needs.
            Also showcase the most relevant ones from the following links from Anarch's portfolio: {link_list}
            Remember you are Manideep, BDE at Anarch.
            Do not provide a preamble.

            ### NO PREAMBLE only give me the email
            """
        )
        prompt = prompt_email.format(job_description=str(job), link_list=links)
        return self._chat(prompt)
    
if __name__ == "__main__":
    print(os.getenv("GROQ_API_KEY"))