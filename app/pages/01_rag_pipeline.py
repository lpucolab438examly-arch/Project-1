import os
import streamlit as st

from portfolio import Portfolio

st.set_page_config(page_title="RAG Pipeline", page_icon="🔍", layout="wide")


def _mask(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return "(not set)"
    if len(value) <= 8:
        return "(set)"
    return f"{value[:4]}...{value[-4:]}"


def _portfolio_status():
    try:
        portfolio = Portfolio()
        portfolio.load_portfolio()

        if portfolio.use_chroma and portfolio.collection:
            try:
                count = portfolio.collection.count()
            except Exception:
                count = "unknown"
            return {
                "mode": "Chroma vector store",
                "path": getattr(portfolio, "chroma_client", None) and getattr(portfolio.chroma_client, "_client", None) and getattr(portfolio.chroma_client._client, "base_path", "(path unavailable)"),
                "docs_indexed": count,
            }

        return {
            "mode": "CSV keyword fallback",
            "path": portfolio.file_path,
            "docs_indexed": len(portfolio.data.index),
        }
    except Exception as exc:  # pragma: no cover - defensive
        return {"mode": "unavailable", "error": str(exc)}


st.title("RAG Pipeline Overview")
st.caption("How the app fetches job data, retrieves portfolio evidence, and generates cold emails.")

col1, col2 = st.columns([2, 1])
with col1:
    st.subheader("Pipeline Steps")
    st.markdown(
        """
        1) **Ingest job data** — scrape URL via `WebBaseLoader` or fallback `requests+BeautifulSoup`; manual paste is allowed.
        2) **LLM extraction** — Groq parses roles, experience, skills, and descriptions (`Chain.extract_jobs`).
        3) **Retrieve evidence** — skills query the portfolio knowledge base (Chroma vector store; CSV keyword fallback).
        4) **Generate email** — Groq writes a grounded cold email using the job + retrieved links (`Chain.write_mail`).
        5) **Deliver** — render per-role email and offer CSV download.
        """
    )

    st.subheader("Components")
    st.markdown(
        """
        - **LLM**: Groq chat completion (`GROQ_MODEL`, default meta-llama/llama-4-scout-17b-16e-instruct)
        - **Retriever**: ChromaDB persistent collection `portfolio` (2 nearest links), otherwise CSV keyword matcher
        - **Data**: [app/resourse/my_portfolio.csv](../resourse/my_portfolio.csv) provides links/tech stacks
        - **UI**: Streamlit main page ([app/main.py](../main.py)) + this pipeline page
        """
    )

with col2:
    st.subheader("Config Snapshot")
    st.write({
        "GROQ_API_KEY": _mask(os.getenv("GROQ_API_KEY", "")),
        "GROQ_MODEL": os.getenv("GROQ_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct"),
    })

    st.subheader("Retriever Status")
    status = _portfolio_status()
    st.write(status)

st.divider()

st.subheader("Data Flow (text diagram)")
st.code(
    """
[Job URL or pasted text]
    -> scrape/clean
    -> LLM: extract_jobs
    -> skills
    -> Retriever: Chroma (k=2) or CSV keyword match
    -> links
    -> LLM: write_mail(job, links)
    -> Streamlit renders email + CSV download
    """,
    language="text",
)
