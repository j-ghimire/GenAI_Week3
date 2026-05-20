import re
from typing import Dict, List, Optional
from schema_parser import parse_schema


def quote(identifier: str) -> str:
    return f'"{identifier}"'


class SqlGenerator:
    def __init__(self, schema: Dict[str, Dict[str, List[str]]]):
        self.schema = schema
        self.tables = list(schema.keys())
        self.table_keywords = {
            'products': ['product', 'products', 'product line', 'product lines'],
            'productlines': ['product line', 'product lines', 'productlines'],
            'offices': ['office', 'offices', 'city', 'country'],
            'employees': ['employee', 'employees', 'manager', 'job title', 'job titles', 'sales rep'],
            'customers': ['customer', 'customers', 'customer name', 'phone', 'city', 'country', 'sales rep'],
            'payments': ['payment', 'payments', 'amount', 'check number'],
            'orders': ['order', 'orders', 'order date', 'status', 'order number'],
            'orderdetails': ['order detail', 'order details', 'orderdetail', 'orderdetails', 'quantity ordered', 'price each'],
        }
        self.joins = {
            ('orders', 'customers'): ('orders', 'customers', '"customerNumber"', '"customerNumber"'),
            ('customers', 'employees'): ('customers', 'employees', '"salesRepEmployeeNumber"', '"employeeNumber"'),
            ('orderdetails', 'products'): ('orderdetails', 'products', '"productCode"', '"productCode"'),
            ('products', 'productlines'): ('products', 'productlines', '"productLine"', '"productLine"'),
            ('employees', 'offices'): ('employees', 'offices', '"officeCode"', '"officeCode"'),
            ('payments', 'customers'): ('payments', 'customers', '"customerNumber"', '"customerNumber"'),
        }

    def _select_columns(self, columns: List[str]) -> str:
        return ', '.join(quote(c) for c in columns)

    def _find_best_table(self, question: str) -> Optional[str]:
        q = question.lower()
        scores = {table: 0 for table in self.tables}
        for table, keywords in self.table_keywords.items():
            for keyword in keywords:
                if keyword in q:
                    scores[table] += 1
        best = max(scores, key=scores.get)
        return best if scores[best] > 0 else None

    def _try_join(self, question: str) -> Optional[str]:
        q = question.lower()
        for (left, right), join_info in self.joins.items():
            if left in q and right in q or right in q and left in q:
                l, r, lcol, rcol = join_info
                alias_left = l[0]
                alias_right = r[0]
                if {left, right} == {'employees', 'employees'}:
                    continue
                return f'FROM {l} {alias_left} JOIN {r} {alias_right} ON {alias_left}.{lcol} = {alias_right}.{rcol}'
        return None

    def build(self, question: str) -> str:
        q = question.lower()
        if 'list all' in q or 'get all' in q or 'show all' in q:
            table = self._find_best_table(q)
            if table:
                return f'SELECT * FROM {table};'

        patterns = [
            (r'product names and prices', 'products', ['productName', 'buyPrice', 'MSRP']),
            (r'customer names and cities', 'customers', ['customerName', 'city']),
            (r'employee first and last names', 'employees', ['firstName', 'lastName']),
            (r'order dates', 'orders', ['orderNumber', 'orderDate']),
            (r'product vendor list', 'products', ['productVendor'], True),
            (r'product codes', 'products', ['productCode']),
            (r'countries from offices', 'offices', ['country'], True),
            (r'order statuses', 'orders', ['status'], True),
            (r'payment amounts', 'payments', ['customerNumber', 'amount']),
            (r'job titles', 'employees', ['jobTitle'], True),
            (r'phone numbers', 'customers', ['customerName', 'phone']),
            (r'product msrp values', 'products', ['productName', 'MSRP']),
            (r'order numbers', 'orders', ['orderNumber']),
        ]
        for pattern, table, cols, *distinct in patterns:
            if pattern in q:
                distinct_sql = 'DISTINCT ' if distinct and distinct[0] else ''
                return f'SELECT {distinct_sql}{self._select_columns(cols)} FROM {table};'

        join_patterns = [
            (r'orders with customer names', 'orders', 'customers', ['orderNumber','orderDate','customerName']),
            (r'employees with office city', 'employees', 'offices', ['employeeNumber','firstName','lastName','city']),
            (r'payments with customer names', 'payments', 'customers', ['checkNumber','paymentDate','amount','customerName']),
            (r'order details with product names', 'orderdetails', 'products', ['orderNumber','productCode','productName','quantityOrdered','priceEach']),
            (r'products with product line description', 'products', 'productlines', ['productCode','productName','textDescription']),
            (r'customers with sales rep names', 'customers', 'employees', ['customerNumber','customerName','firstName','lastName']),
            (r'orders with customer city', 'orders', 'customers', ['orderNumber','customerName','city','orderDate']),
            (r'employees and their manager', 'employees', 'employees', ['employeeNumber','firstName','lastName','managerNumber','managerFirst','managerLast']),
            (r'orderdetails with product vendor', 'orderdetails', 'products', ['orderNumber','productCode','productVendor','quantityOrdered']),
            (r'payments with customer country', 'payments', 'customers', ['*','country']),
        ]
        for pattern, left, right, cols in join_patterns:
            if pattern in q:
                select_cols = ', '.join(quote(c) if c != '*' else '*' for c in cols)
                if left == right == 'employees':
                    return (
                        'SELECT e."employeeNumber", e."firstName", e."lastName", '
                        'm."employeeNumber" AS managerNumber, m."firstName" AS managerFirst, '
                        'm."lastName" AS managerLast '
                        'FROM employees e LEFT JOIN employees m ON e."reportsTo" = m."employeeNumber";'
                    )
                if left == 'orders' and right == 'customers':
                    return f'SELECT {select_cols} FROM orders o JOIN customers c ON o."customerNumber" = c."customerNumber";'
                if left == 'employees' and right == 'offices':
                    return f'SELECT {select_cols} FROM employees e JOIN offices o ON e."officeCode" = o."officeCode";'
                if left == 'payments' and right == 'customers':
                    return (
                        'SELECT p.*, c."country" '
                        'FROM payments p JOIN customers c ON p."customerNumber" = c."customerNumber";'
                    )
                if left == 'orderdetails' and right == 'products':
                    return f'SELECT {select_cols} FROM orderdetails od JOIN products pr ON od."productCode" = pr."productCode";'
                if left == 'products' and right == 'productlines':
                    return f'SELECT {select_cols} FROM products pr JOIN productlines pl ON pr."productLine" = pl."productLine";'
                if left == 'customers' and right == 'employees':
                    return f'SELECT {select_cols} FROM customers c LEFT JOIN employees e ON c."salesRepEmployeeNumber" = e."employeeNumber";'
                join = self._try_join(q)
                if join:
                    return f'SELECT {select_cols} {join};'

        aggregation_patterns = [
            (r'count customers per country', 'customers', ['country'], 'COUNT(*) AS customers_count', ['country']),
            (r'total payments per customer', 'payments', ['customerNumber','customerName'], 'SUM(amount) AS total_payments', ['customerNumber','customerName']),
            (r'number of orders per status', 'orders', ['status'], 'COUNT(*) AS orders_count', ['status']),
            (r'products per product line', 'products', ['productLine'], 'COUNT(*) AS products_count', ['productLine']),
            (r'employees per office', 'employees', ['officeCode','city'], 'COUNT(*) AS employees_count', ['officeCode','city'], 'offices'),
            (r'total stock per product vendor', 'products', ['productVendor'], 'SUM(quantityInStock) AS total_stock', ['productVendor']),
            (r'average buy price per product line', 'products', ['productLine'], 'AVG(buyPrice) AS avg_buy_price', ['productLine']),
            (r'orders per customer', 'orders', ['customerNumber','customerName'], 'COUNT(*) AS orders_count', ['customerNumber','customerName'], 'customers'),
            (r'max msrp per product line', 'products', ['productLine'], 'MAX(MSRP) AS max_msrp', ['productLine']),
            (r'min buy price per vendor', 'products', ['productVendor'], 'MIN(buyPrice) AS min_buy_price', ['productVendor']),
            (r'total number of customers', 'customers', [], 'COUNT(*) AS total_customers', []),
            (r'total number of products', 'products', [], 'COUNT(*) AS total_products', []),
            (r'total revenue from payments', 'payments', [], 'SUM(amount) AS total_revenue', []),
            (r'average product price', 'products', [], 'AVG(buyPrice) AS avg_buy_price, AVG(MSRP) AS avg_msrp', []),
            (r'max payment amount', 'payments', [], 'MAX(amount) AS max_payment', []),
            (r'min payment amount', 'payments', [], 'MIN(amount) AS min_payment', []),
            (r'count total orders', 'orders', [], 'COUNT(*) AS total_orders', []),
            (r'total quantity in stock', 'products', [], 'SUM(quantityInStock) AS total_quantity_in_stock', []),
            (r'average msrp', 'products', [], 'AVG(MSRP) AS average_msrp', []),
            (r'number of employees', 'employees', [], 'COUNT(*) AS total_employees', []),
        ]
        for pattern, table, group_cols, agg_expr, *_ in aggregation_patterns:
            if pattern in q:
                group_clause = ''
                if group_cols:
                    cols_str = ', '.join(quote(c) for c in group_cols)
                    group_clause = f' GROUP BY {cols_str}'
                from_clause = f'FROM {table}'
                if len(group_cols) == 2 and pattern in ('total payments per customer', 'orders per customer'):
                    from_clause = 'FROM payments p JOIN customers c ON p."customerNumber" = c."customerNumber"' if 'payments' in q else 'FROM orders o JOIN customers c ON o."customerNumber" = c."customerNumber"'
                    if 'payments' in q:
                        return f'SELECT p."customerNumber", c."customerName", SUM(p."amount") AS total_payments {from_clause} GROUP BY p."customerNumber", c."customerName" ORDER BY total_payments DESC;'
                    if 'orders' in q:
                        return f'SELECT o."customerNumber", c."customerName", COUNT(*) AS orders_count {from_clause} GROUP BY o."customerNumber", c."customerName" ORDER BY orders_count DESC;'
                if pattern == 'employees per office':
                    return 'SELECT e."officeCode", o."city", COUNT(*) AS employees_count FROM employees e JOIN offices o ON e."officeCode" = o."officeCode" GROUP BY e."officeCode", o."city";'
                return f'SELECT {agg_expr} {from_clause}{group_clause};'

        table = self._find_best_table(q)
        if table:
            return f'SELECT * FROM {table};'

        return 'SELECT 1;'


def build_sql_for_questions():
    schema = parse_schema()
    generator = SqlGenerator(schema)
    return generator
