import sqlite3

connection = sqlite3.connect('movies.db')
cursor = connection.cursor()

with open('sql_queries/schema_update.sql', 'r', encoding='utf-8') as file:
    sql_script = file.read()

try:
    cursor.executescript(sql_script)
    connection.commit()
except sqlite3.Error as e:
    print(f"Unable to execute script. Encountered error: {e}")
finally:
    connection.close()
