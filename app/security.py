import sqlglot
from sqlglot import exp
from typing import Tuple

FORBIDDEN_EXPRESSIONS = (
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Drop,
    exp.Alter,
    exp.Create,
    exp.Command,
    exp.TruncateTable,
)

def validate_and_sanitize_sql(sql: str, default_limit: int = 100) -> Tuple[bool, str, str]:
    cleaned = sql.strip().rstrip(";")
    if not cleaned:
        return False, "", "Empty SQL query."

    try:
        statements = sqlglot.parse(cleaned, read="postgres")
        if len(statements) != 1:
            return False, "", "Multiple SQL statements are strictly prohibited."
        
        parsed = statements[0]
        if not parsed:
            return False, "", "Could not parse SQL query."

        for node in parsed.walk():
            if isinstance(node, FORBIDDEN_EXPRESSIONS):
                return False, "", f"Forbidden SQL operation detected: {node.key.upper()}"

        if not isinstance(parsed, (exp.Select, exp.Union)):
            return False, "", f"Only SELECT queries are allowed. Got: {type(parsed).__name__}"

        sanitized_sql = parsed.sql(dialect="postgres")
        return True, sanitized_sql, ""

    except sqlglot.errors.ParseError as pe:
        return False, "", f"SQL Syntax/Parse error: {pe}"
    except Exception as e:
        return False, "", f"SQL Security Validation error: {e}"
