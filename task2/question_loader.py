from pathlib import Path
import pandas as pd


def load_questions(excel_path: str = None):
    excel_path = Path(excel_path or Path(__file__).resolve().parent / 'SQL_QUESTIONS.xlsx')
    df = pd.read_excel(excel_path, sheet_name='sql_questions_only')
    if 'question' not in df.columns:
        raise ValueError("Expected a 'question' column in SQL_QUESTIONS.xlsx")
    return [str(q).strip() for q in df['question'].dropna()]
