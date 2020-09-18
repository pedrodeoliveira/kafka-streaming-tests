import sqlite3
import os
import sys

DATABASE_PATH = os.getenv('DATABASE_PATH', 'results.db')

sql_results_table = """ 
    CREATE TABLE "results" (
        run_id INTEGER,
        uid TEXT,
        publish_ts NUMERIC,
        streaming_consume_ts NUMERIC,
        streaming_publish_ts NUMERIC,
        consume_ts NUMERIC,
        pub_to_stream_time_ms INTEGER,
        inference_time_ms INTEGER,
        stream_to_cons_time_ms INTEGER,
        total_time_ms INTEGER
    );
    """


def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    try:
        return sqlite3.connect(db_file)
    except sqlite3.Error as e:
        print(e)
    return None


def create_table(conn, create_table_sql):
    """ create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except sqlite3.Error as e:
        print(e)


if __name__ == "__main__":

    if os.path.exists(DATABASE_PATH):
        print(f'Database file [{DATABASE_PATH}] already exists')
        sys.exit()

    # create a database connection
    conn = create_connection(DATABASE_PATH)

    # create tables
    if conn is not None:
        # create projects table
        create_table(conn, sql_results_table)
    else:
        print("Error! cannot create the database connection.")
        sys.exit(1)
