import streamlit as st
import requests
import os

st.set_page_config(page_title="Agentic Text-to-SQL", layout="centered")

st.title("Agentic Text-to-SQL (Streamlit)")

api_url = os.getenv("API_URL", "http://api:8000/query")

query = st.text_area("Enter a natural language question for the database:")

if st.button("Run") and query.strip():
    with st.spinner("Running workflow..."):
        try:
            resp = requests.post(api_url, json={"query": query}, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            st.subheader("Final Answer")
            st.write(data.get("final_answer") or "No summary returned.")

            st.subheader("Generated SQL")
            st.code(data.get("generated_sql") or "")

            st.subheader("Execution Results")
            st.write(data.get("execution_results") or [])

            if data.get("errors"):
                st.error(data.get("errors"))
        except Exception as e:
            st.exception(e)
