import pandas as pd
xls = pd.ExcelFile('SQL_QUESTIONS.xlsx')
print('sheets', xls.sheet_names)
df = pd.read_excel('SQL_QUESTIONS.xlsx')
print('shape', df.shape)
print(df.head(10).to_csv(index=False))
