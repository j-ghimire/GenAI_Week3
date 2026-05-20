import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from sql_generator import decompose, generate_sql, fix_sql
from validator import assert_safe
from database import execute_query

LOG_FILE = Path(__file__).resolve().parent / 'logs' / 'query_logs.json'
LOG_FILE.parent.mkdir(exist_ok=True, parents=True)


def _append_log(entry: Dict[str, Any]) -> None:
    with LOG_FILE.open('a', encoding='utf-8') as fh:
        fh.write(json.dumps(entry, default=str) + "\n")


def run_pipeline(question: str, execute: bool = True, database_url: Optional[str] = None) -> Dict[str, Any]:
    record: Dict[str, Any] = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'question': question,
        'sql': None,
        'status': 'generated',
        'error': None,
        'attempts': 0,
        'rows': None,
        'columns': None,
    }

    try:
        decomposition = decompose(question)
        sql = generate_sql(decomposition)
        record['sql'] = sql
        assert_safe(sql)
    except Exception as e:
        record.update({'status': 'failed', 'error': str(e)})
        _append_log(record)
        return record

    if not execute:
        _append_log(record)
        return record

    for attempt in range(1, 3):
        record['attempts'] = attempt
        columns, rows, err = execute_query(sql + ';', database_url=database_url)
        if err is None:
            record.update({'status': 'success', 'error': None, 'rows': rows, 'columns': columns})
            _append_log(record)
            return record

        record['error'] = err
        record['status'] = 'failed'
        _append_log(record)

        if attempt == 1:
            candidate = fix_sql(sql, err, decomposition)
            if candidate is None:
                return record
            try:
                assert_safe(candidate)
            except Exception as cf_error:
                record.update({'status': 'failed', 'error': str(cf_error)})
                _append_log(record)
                return record
            sql = candidate
            record['sql'] = sql
            continue

        return record

    return record
