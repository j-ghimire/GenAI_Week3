import os
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
import streamlit as st
import pandas as pd
from executor import run_pipeline

dotenv_path = find_dotenv(usecwd=True)
if not dotenv_path:
    dotenv_path = Path(__file__).resolve().parent / '.env'
load_dotenv(dotenv_path)

st.set_page_config(page_title='Text-to-SQL Pipeline', layout='wide')
st.title('Text-to-SQL Pipeline and Execution')

AI_API_KEY = os.getenv('AI_API_KEY') or os.getenv('OPENAI_API_KEY')
AI_PROVIDER = os.getenv('AI_PROVIDER')
if not AI_PROVIDER:
    if AI_API_KEY and AI_API_KEY.startswith('AIza'):
        AI_PROVIDER = 'google'
    else:
        AI_PROVIDER = 'openai'
AI_PROVIDER = AI_PROVIDER.lower()
AI_MODEL = os.getenv('AI_MODEL', 'gemini-2.5-flash' if AI_PROVIDER == 'google' else 'gpt-4o-mini')

if not AI_API_KEY:
    st.error('AI_API_KEY or OPENAI_API_KEY not set. Please set it in .env or your environment.')
    st.stop()

st.write(f'Using AI provider: {AI_PROVIDER}, model: {AI_MODEL}')

with st.sidebar:
    st.header('Settings')
    execute = st.checkbox('Execute against DB', value=False)
    db_url = st.text_input('DATABASE_URL (optional)', value=os.environ.get('DATABASE_URL', ''))

question = st.text_input('Enter your natural language SQL question')
if st.button('Run') and question:
    with st.spinner('Running pipeline...'):
        record = run_pipeline(question, execute=execute, database_url=db_url or None)

    st.subheader('Generated SQL')
    st.code(record.get('sql') or '(no sql)')

    st.subheader('Status')
    st.write(record.get('status'))

    if not execute:
        st.info('Execution disabled. The query was generated but not run against the database.')

    if record.get('status') == 'success' and execute:
        rows = record.get('rows') or []
        columns = record.get('columns') or []
        if rows and columns:
            try:
                df = pd.DataFrame(rows, columns=columns)
                st.dataframe(df)
            except Exception:
                st.write(rows)
        else:
            st.success('Query executed successfully.')
    elif record.get('status') == 'failed':
        st.error(record.get('error') or 'Failed to generate or execute the query.')
