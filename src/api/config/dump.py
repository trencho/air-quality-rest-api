from sqlite3 import connect, Cursor
from typing import Any


def generate_sql_dump(database_file: str) -> str:
    with connect(database_file) as conn:
        cursor = conn.cursor()
        dump_content = [
            f"-- Table: {table_name}\n{generate_insert_statements(cursor, table_name)}"
            for table_name in get_table_names(cursor)
        ]
    return "\n\n".join(dump_content)


def get_table_names(cursor: Cursor) -> list[str]:
    cursor.execute("SELECT NAME FROM SQLITE_MASTER WHERE TYPE='table'")
    return [row[0] for row in cursor.fetchall()]


def generate_insert_statements(cursor: Cursor, table_name: str) -> str:
    cursor.execute(f"SELECT * FROM {table_name}")
    columns = [description[0] for description in cursor.description]
    insert_statements = [
        f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(format_sql_value(value) for value in row)});"
        for row in cursor.fetchall()
    ]
    return "\n".join(insert_statements)


def format_sql_value(value: Any) -> str:
    if isinstance(value, str):
        return f"'{value}'"
    elif value is None:
        return "NULL"
    else:
        return str(value)
