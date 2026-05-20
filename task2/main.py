import argparse
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from question_loader import load_questions
from schema_parser import parse_schema
from sql_generator import SqlGenerator
from agent import DatabaseAgent


def print_query(question_number: int, question: str, sql: str):
    print(f'-- Question {question_number}: {question}')
    print(sql)
    print()


def main():
    parser = argparse.ArgumentParser(description='Task 2 Text-to-SQL generator and execution agent')
    parser.add_argument('--number', type=int, help='Question number to generate or execute')
    parser.add_argument('--execute', action='store_true', help='Execute generated SQL against the configured database')
    parser.add_argument('--single', action='store_true', help='Print only a single question result when --number is provided')
    args = parser.parse_args()

    questions = load_questions(BASE_DIR / 'SQL_QUESTIONS.xlsx')
    schema = parse_schema(BASE_DIR / 'seed (1).sql')
    generator = SqlGenerator(schema)

    if args.number:
        if args.number < 1 or args.number > len(questions):
            raise ValueError(f'Question number must be between 1 and {len(questions)}')
        questions = [(args.number, questions[args.number - 1])]
    else:
        questions = list(enumerate(questions, start=1))

    if args.execute:
        agent = DatabaseAgent()

    for idx, question in questions:
        sql = generator.build(question)
        print_query(idx, question, sql)
        if args.execute:
            columns, rows = agent.execute(sql)
            if rows:
                print('RESULT COLUMNS:', columns)
                for row in rows[:10]:
                    print(row)
                if len(rows) > 10:
                    print(f'... ({len(rows) - 10} more rows)')
            else:
                print('No rows returned or non-SELECT result.')
            print()


if __name__ == '__main__':
    main()
