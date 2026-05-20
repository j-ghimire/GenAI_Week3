import pandas as pd
from pathlib import Path
path = Path('SQL_QUESTIONS.xlsx')
df = pd.read_excel(path, sheet_name='sql_questions_only')
for i, q in enumerate(df['question'].tolist(), 1):
    print(i, q)
