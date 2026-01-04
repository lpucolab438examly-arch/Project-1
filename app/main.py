import streamlit as st

# ✅ MUST be first Streamlit command
st.set_page_config(
    layout="wide",
    page_icon="🤑",
    page_title="Email Generator"
)

import pandas as pd
try:
    from langchain_community.document_loaders import WebBaseLoader
except ModuleNotFoundError:
    WebBaseLoader = None

import requests
from bs4 import BeautifulSoup
from chains import Chain
from portfolio import Portfolio


def _mask_key(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return "(not set)"
    if len(value) <= 10:
        return "(set)"
    return f"{value[:4]}...{value[-4:]}"

# --- Custom CSS for style ---
st.markdown("""
    <style>
        .main { background-color: #f7f7f7; }
        h1 { color: #ff4b4b; }
        .stTextInput > div > div > input {
            border: 2px solid #ff4b4b;
            border-radius: 8px;
        }
        .stButton > button {
            background-color: #ff4b4b;
            color: white;
            border-radius: 8px;
            padding: 0.5em 1em;
        }
        .stButton > button:hover {
            background-color: #d63c3c;
            color: white;
        }
    </style>
""", unsafe_allow_html=True)

def create_stream_app(llm, portfolio):
    st.title("🚀 Cold Email Generator")
    st.markdown("**Enter a job listing URL and let the AI craft tailored cold emails.**")

    with st.expander("⚙️ Config (debug)"):
        st.write("GROQ_API_KEY:", _mask_key(st.session_state.get("_groq_key", "")))
        st.write("GROQ_MODEL:", st.session_state.get("_groq_model", "(default)"))

    col1, col2 = st.columns([3, 1])
    with col1:
        url_input = st.text_input("🌐 Job Listing URL:", 
            value="https://jobdetails.nestle.com/job/Esplugues-Llobregat-Technology-Expert-R&D-Information-Technology-B-08950/1204832601/?feedId=256801"
        )
    with col2:
        submit_button = st.button("🔥 Generate Emails")

    pasted_text = st.text_area(
        "📋 Paste job page text (optional — use this if the site blocks scraping)",
        value="",
        height=200,
        placeholder="If the URL returns 403/blocked, open it in your browser and paste the job description text here...",
    )

    if submit_button:
        with st.spinner("🧠 Thinking... extracting jobs & crafting emails..."):
            try:
                if pasted_text and pasted_text.strip():
                    data = pasted_text.strip()
                else:
                    if WebBaseLoader is not None:
                        loader = WebBaseLoader([url_input])
                        data = loader.load().pop().page_content
                    else:
                        st.warning("⚠️ langchain-community not available; using basic HTML loader.")
                        resp = requests.get(url_input, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
                        if resp.status_code == 403:
                            raise RuntimeError(
                                "This site blocked automated access (HTTP 403). Paste the job text into the box above and try again."
                            )
                        resp.raise_for_status()
                        soup = BeautifulSoup(resp.text, "html.parser")
                        data = soup.get_text(" ", strip=True)

                portfolio.load_portfolio()
                jobs = llm.extract_jobs(data)

                email_records = []

                for job in jobs:
                    # Get job details with fallbacks
                    title = job.get('title') or job.get('role') or 'Untitled Role'
                    skills = job.get('skills', [])
                    
                    # Handle skills formatting
                    if isinstance(skills, str):
                        skills = [s.strip() for s in skills.split(',') if s.strip()]
                    elif not isinstance(skills, list):
                        skills = []
                    
                    # Only query portfolio if skills exist
                    if skills:
                        links = portfolio.query_links(skills)
                    else:
                        links = []
                        st.warning(f"⚠️ No skills found for {title}")
                    
                    email = llm.write_mail(job, links)

                    st.subheader(f"💼 {title}")
                    st.markdown(f"**Skills Required:** {', '.join(skills) if skills else 'N/A'}")
                    st.code(email, language='markdown')

                    email_records.append({
                        "Job Title": title,
                        "Skills": ", ".join(skills),
                        "Email": email
                    })

                if email_records:
                    df = pd.DataFrame(email_records)
                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Download All Emails as CSV",
                        data=csv,
                        file_name="generated_emails.csv",
                        mime="text/csv"
                    )

            except Exception as e:
                st.error(f"❌ An Error Occurred: {e}")
                st.info("💡 Please check if the URL is accessible and contains job information.")

if __name__ == "__main__":
    import os

    st.sidebar.header("🔑 API Setup")
    st.sidebar.caption("Key is kept local on your machine. Don’t paste it into chat.")

    key_input = st.sidebar.text_input("GROQ_API_KEY", value="", type="password")
    model_default = os.getenv("GROQ_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")
    model_input = st.sidebar.text_input("GROQ_MODEL", value=model_default)

    if key_input and key_input.strip():
        os.environ["GROQ_API_KEY"] = key_input.strip()
    if model_input and model_input.strip():
        os.environ["GROQ_MODEL"] = model_input.strip()

    # Capture env-derived config for a masked debug display.
    st.session_state["_groq_key"] = os.getenv("GROQ_API_KEY", "")
    st.session_state["_groq_model"] = os.getenv("GROQ_MODEL", "")

    try:
        chain = Chain()
    except Exception as e:
        st.error(f"❌ Groq config error: {e}")
        st.info("💡 Paste a fresh Groq key in the sidebar (or update app/.env) and rerun.")
        st.stop()

    try:
        portfolio = Portfolio()
        create_stream_app(chain, portfolio)
    except Exception as e:
        st.error(f"❌ Failed to initialize application: {e}")
        st.info("💡 Please check if all required files are present and properly configured.")
