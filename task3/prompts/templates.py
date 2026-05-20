SCHEMA_CONTEXT = '''
-- classicmodels simplified schema
DROP TABLE IF EXISTS orderdetails CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS payments CASCADE;
DROP TABLE IF EXISTS customers CASCADE;
DROP TABLE IF EXISTS employees CASCADE;
DROP TABLE IF EXISTS offices CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS productlines CASCADE;

CREATE TABLE productlines (
  "productLine" VARCHAR(50) PRIMARY KEY,
  "textDescription" VARCHAR(4000),
  "htmlDescription" TEXT,
  "image" BYTEA
);

CREATE TABLE products (
  "productCode" VARCHAR(15) PRIMARY KEY,
  "productName" VARCHAR(70) NOT NULL,
  "productLine" VARCHAR(50) NOT NULL,
  "productScale" VARCHAR(10) NOT NULL,
  "productVendor" VARCHAR(50) NOT NULL,
  "productDescription" TEXT NOT NULL,
  "quantityInStock" INTEGER NOT NULL,
  "buyPrice" NUMERIC(10,2) NOT NULL,
  "MSRP" NUMERIC(10,2) NOT NULL
);

CREATE TABLE offices (
  "officeCode" VARCHAR(10) PRIMARY KEY,
  "city" VARCHAR(50) NOT NULL,
  "phone" VARCHAR(50) NOT NULL,
  "addressLine1" VARCHAR(50) NOT NULL,
  "addressLine2" VARCHAR(50),
  "state" VARCHAR(50),
  "country" VARCHAR(50) NOT NULL,
  "postalCode" VARCHAR(15) NOT NULL,
  "territory" VARCHAR(10) NOT NULL
);

CREATE TABLE employees (
  "employeeNumber" INTEGER PRIMARY KEY,
  "lastName" VARCHAR(50) NOT NULL,
  "firstName" VARCHAR(50) NOT NULL,
  "extension" VARCHAR(10) NOT NULL,
  "email" VARCHAR(100) NOT NULL,
  "officeCode" VARCHAR(10) NOT NULL,
  "reportsTo" INTEGER,
  "jobTitle" VARCHAR(50) NOT NULL
);

CREATE TABLE customers (
  "customerNumber" INTEGER PRIMARY KEY,
  "customerName" VARCHAR(50) NOT NULL,
  "contactLastName" VARCHAR(50) NOT NULL,
  "contactFirstName" VARCHAR(50) NOT NULL,
  "phone" VARCHAR(50) NOT NULL,
  "addressLine1" VARCHAR(50) NOT NULL,
  "addressLine2" VARCHAR(50),
  "city" VARCHAR(50) NOT NULL,
  "state" VARCHAR(50),
  "postalCode" VARCHAR(15),
  "country" VARCHAR(50) NOT NULL,
  "salesRepEmployeeNumber" INTEGER,
  "creditLimit" NUMERIC(10,2)
);

CREATE TABLE payments (
  "customerNumber" INTEGER,
  "checkNumber" VARCHAR(50),
  "paymentDate" DATE NOT NULL,
  "amount" NUMERIC(10,2) NOT NULL,
  PRIMARY KEY ("customerNumber", "checkNumber")
);

CREATE TABLE orders (
  "orderNumber" INTEGER PRIMARY KEY,
  "orderDate" DATE NOT NULL,
  "requiredDate" DATE NOT NULL,
  "shippedDate" DATE,
  "status" VARCHAR(15) NOT NULL,
  "comments" TEXT,
  "customerNumber" INTEGER NOT NULL
);

CREATE TABLE orderdetails (
  "orderNumber" INTEGER,
  "productCode" VARCHAR(15),
  "quantityOrdered" INTEGER NOT NULL,
  "priceEach" NUMERIC(10,2) NOT NULL,
  "orderLineNumber" SMALLINT NOT NULL,
  PRIMARY KEY ("orderNumber", "productCode")
);
'''

DECOMPOSE_PROMPT = '''You are a JSON extractor for SQL generation. Given a natural language question and a database schema, return exactly one valid JSON object only. Do not include any explanation, markdown fences, or extra text.

The JSON object must contain keys: "intent" (select/aggregate), "tables" (list of table names), "columns" (list of table.column or *), "filters" (list of {{table, column, operator, value}}), and "joins" (list of {{left_table,left_column,right_table,right_column,join_type}}).
Use the schema to pick table and column names exactly as in the schema.

Schema:
{schema}

Question:
{question}
'''

GENERATION_PROMPT = '''You are an assistant that converts a structured decomposition and schema into a PostgreSQL SELECT query. Inputs:
- decomposition JSON: {decomposition}
- schema: {schema}
Rules:
- Output a single valid SQL SELECT statement only. Do not include explanatory text.
- Use table aliases if helpful (o, c, p, etc.)
- Ensure column names match schema exactly and wrap identifiers in double quotes where needed.
- If the decomposition intent is aggregate, use SQL aggregate functions such as MIN, MAX, SUM, AVG, COUNT.
Return only the SQL.
'''

FIX_PROMPT = '''A SQL execution failed with error: {error}
Original SQL:
{sql}
Schema:
{schema}

Please provide a corrected SQL SELECT statement that fixes the error. Return only SQL. If it cannot be fixed safely, return the string: CANNOT_FIX
'''

DECOMPOSE_HINTS = """When decomposing, prefer explicit column lists, avoid aggregation unless asked, and keep filters as SQL snippets."""
DECOMPOSE_RETRY_HINTS = """If the previous response was invalid, retry with only valid JSON. Do not return any explanation or markdown fences."""

GENERATION_HINTS = """Prefer explicit JOINs, use table aliases (t1, t2), and add LIMIT 100 when result set could be large."""

FIX_HINTS = """Return the smallest change that fixes syntax or missing column errors. If column missing, suggest an alternative from schema."""
