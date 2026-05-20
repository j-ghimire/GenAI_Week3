from executor import run_pipeline

BENCHMARK = [
    {"question": "List productName and buyPrice from products where buyPrice > 100", "expected_sql": ""},
    {"question": "Show customerName and country for customers in USA", "expected_sql": ""},
]

def main():
    rows = []
    totals = {"executed":0, "success":0, "retry_success":0, "failed":0}
    for item in BENCHMARK:
        q = item["question"]
        res = run_pipeline(q)
        executed = res.get("status") == "success"
        retry = res.get("retry_used")
        if executed:
            totals["success"] += 1
        else:
            totals["failed"] += 1
        if retry and executed:
            totals["retry_success"] += 1
        totals["executed"] += 1
        rows.append({
            "Question": q,
            "Generated SQL": res.get("sql"),
            "Executed Successfully": res.get("status") == "success",
            "Retry Needed": bool(res.get("retry_used")),
            "Final Status": res.get("status")
        })
    # Print report
    print("Benchmark Report")
    for r in rows:
        print("-"*40)
        for k,v in r.items():
            print(f"{k}: {v}")
    print("-"*40)
    print(f"Executed: {totals['executed']}, Success: {totals['success']}, Retry Success: {totals['retry_success']}, Failed: {totals['failed']}")

if __name__ == '__main__':
    main()
import json
from pathlib import Path
from typing import List, Dict, Any

from executor import run_pipeline

BENCHMARK = [
    {"question": "Count customers in USA", "expected_sql": "SELECT COUNT(*) FROM customers WHERE \"country\" = 'USA';"},
    {"question": "Orders from Germany", "expected_sql": "SELECT o.\"orderNumber\", c.\"customerName\" FROM orders o JOIN customers c ON o.\"customerNumber\" = c.\"customerNumber\" WHERE c.\"country\" = 'Germany';"},
]


def evaluate(dataset: List[Dict[str, Any]]) -> None:
    results: List[Dict[str, Any]] = []
    for item in dataset:
        q = item['question']
        record = run_pipeline(q, execute=True)
        results.append({
            'question': q,
            'generated_sql': record.get('sql'),
            'executed_successfully': record.get('status') == 'success',
            'correct_result': None,
            'retry_needed': record.get('attempts', 0) > 1,
            'final_status': record.get('status'),
        })

    # Print table
    print(f"{'Question':40} | {'Executed':8} | {'Retry':5} | {'Status':10}")
    print('-' * 80)
    for r in results:
        print(f"{r['question'][:40]:40} | {str(r['executed_successfully']):8} | {str(r['retry_needed']):5} | {r['final_status']:10}")

    # Metrics
    total = len(results)
    executed = sum(1 for r in results if r['executed_successfully'])
    retries = sum(1 for r in results if r['retry_needed'])
    failed = sum(1 for r in results if r['final_status'] != 'success')
    print('\nMetrics:')
    print(f'Total: {total}, Executed: {executed}, Retries used: {retries}, Failed: {failed}')


if __name__ == '__main__':
    evaluate(BENCHMARK)
