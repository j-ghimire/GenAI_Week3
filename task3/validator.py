import re

SELECT_ONLY = re.compile(r'^\s*SELECT\b', re.I)
DANGEROUS = re.compile(r'\b(DELETE|DROP|UPDATE|INSERT|ALTER|TRUNCATE|MERGE|CREATE)\b', re.I)
CODE_FENCE = re.compile(r'^```(?:sql)?\s*|\s*```$', re.IGNORECASE)


def _clean_sql(sql: str) -> str:
    cleaned = sql.strip()
    cleaned = CODE_FENCE.sub('', cleaned)
    if cleaned.startswith('`') and cleaned.endswith('`'):
        cleaned = cleaned[1:-1].strip()
    return cleaned.strip()


def is_select(sql: str) -> bool:
    cleaned = _clean_sql(sql)
    return bool(SELECT_ONLY.search(cleaned)) and not bool(DANGEROUS.search(cleaned))


def assert_safe(sql: str) -> None:
    if not is_select(sql):
        raise ValueError('Only safe SELECT statements are allowed.')
