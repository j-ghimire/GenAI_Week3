import re
from pathlib import Path
from typing import Dict, List

SQL_FILE = Path(__file__).resolve().parent / 'seed (1).sql'
CREATE_TABLE_RE = re.compile(r'CREATE TABLE\s+"?(\w+)"?\s*\((.*?)\);', re.S | re.I)
FK_RE = re.compile(
    r'FOREIGN KEY\s*\(\s*"?(\w+)"?\s*\)\s+REFERENCES\s+"?(\w+)"?\s*\(\s*"?(\w+)"?\s*\)',
    re.I,
)
COLUMN_RE = re.compile(r'^"?(\w+)"?\s+[A-Za-z0-9_\(\),\s]+', re.I)


def parse_schema(sql_path: str = None) -> Dict[str, Dict[str, List[str]]]:
    sql_path = Path(sql_path or SQL_FILE)
    text = sql_path.read_text(encoding='utf-8')
    schema: Dict[str, Dict[str, List[str]]] = {}

    for table_name, body in CREATE_TABLE_RE.findall(text):
        columns: List[str] = []
        foreign_keys: List[Dict[str, str]] = []
        for raw_line in body.splitlines():
            line = raw_line.strip().rstrip(',')
            if not line:
                continue
            upper = line.upper()
            if upper.startswith(('PRIMARY KEY', 'FOREIGN KEY', 'UNIQUE', 'CHECK', 'CONSTRAINT')):
                if upper.startswith('FOREIGN KEY'):
                    fk_match = FK_RE.search(line)
                    if fk_match:
                        foreign_keys.append(
                            {
                                'column': fk_match.group(1),
                                'ref_table': fk_match.group(2),
                                'ref_column': fk_match.group(3),
                            }
                        )
                continue

            col_match = COLUMN_RE.match(line)
            if col_match:
                columns.append(col_match.group(1))

        schema[table_name] = {
            'columns': columns,
            'foreign_keys': foreign_keys,
        }

    return schema
