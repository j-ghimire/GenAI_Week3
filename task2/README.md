# Task 2: Text-to-SQL Foundation

This folder contains the Task 2 implementation for a Text-to-SQL system built on the same seeded database schema and question dataset from Task 1.

## Purpose
- Use `task2/seed (1).sql` as the database schema source.
- Use `task2/SQL_QUESTIONS.xlsx` as the authoritative question set.
- Generate PostgreSQL queries from natural language questions.
- Provide a basic execution agent that can run SQL against a PostgreSQL database if a connection is available.

## Files
- `schema_parser.py` - Parses `seed (1).sql` to extract table columns and foreign key relations.
- `question_loader.py` - Loads questions from `SQL_QUESTIONS.xlsx`.
- `sql_generator.py` - Builds SQL queries from natural language questions using the schema.
- `agent.py` - Optional PostgreSQL execution agent using `DATABASE_URL`.
- `main.py` - CLI entrypoint for generating or running queries.
- `requirements.txt` - Python dependencies for Task 2.

## Usage
1. Install dependencies in the existing workspace environment:

```powershell
pip install -r task2/requirements.txt
```

2. Generate SQL for all questions:

```powershell
python task2/main.py
```

3. Run a specific question by number:

```powershell
python task2/main.py --number 21
```

4. Execute generated SQL against PostgreSQL (optional):

```powershell
$env:DATABASE_URL = 'postgresql://user:pass@localhost:5432/dbname'
python task2/main.py --execute
```

## Notes
- The implementation is intentionally lightweight and relies on the same database schema and seed file used in the earlier course work.
- If PostgreSQL is not available yet, `main.py` still generates SQL statements for the workbook questions.
