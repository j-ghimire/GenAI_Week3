import streamlit as st
import requests
import os

st.set_page_config(page_title="Agentic Text-to-SQL", layout="centered")

st.title("Agentic Text-to-SQL (Streamlit)")

api_url = os.getenv("API_URL", "http://api:8000/agent/sql")

query = st.text_area("Enter a natural language question for the database:")

if st.button("Run") and query.strip():
    with st.spinner("Running workflow..."):
        try:
            resp = requests.post(api_url, json={"question": query}, timeout=60)
            resp.raise_for_status()
            data = resp.json()

            st.subheader("Summary")
            st.write(data.get("summary") or data.get("final_answer") or "No summary returned.")

            st.subheader("Generated SQL")
            st.code(data.get("sql") or "")

            st.subheader("Result")
            st.write(data.get("result") if data.get("result") is not None else data.get("execution_results") or [])

            st.subheader("Status")
            st.write(data.get("status"))

            if data.get("errors"):
                st.error(data.get("errors"))
        except Exception as e:
            st.exception(e)
