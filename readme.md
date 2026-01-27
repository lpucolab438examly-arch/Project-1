# 🚀 Cold Email Generator

An AI-powered tool that generates personalized cold emails for job applications by analyzing job postings and matching them with your portfolio.

## Features

- Extract job requirements from job posting URLs
- Generate tailored cold emails using AI
- Portfolio matching based on required skills
- Download generated emails as CSV

## Live Demo

[Streamlit App](https://your-app-url.streamlit.app)

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/cold-email-generator-tool.git
cd cold-email-generator-tool
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set up your Groq API key:

- Get your API key from [Groq Console](https://console.groq.com)
- Update the API key in `app/chains.py`

4. Run the app:

```bash
streamlit run app/main.py
```

## Usage

1. Enter a job posting URL
2. Click "Generate Emails"
3. View and download personalized cold emails

## Tech Stack

- Streamlit
- LangChain
- Groq LLM
- ChromaDB
- BeautifulSoup4
