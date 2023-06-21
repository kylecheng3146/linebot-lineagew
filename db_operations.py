import psycopg2

def connect_to_db():
    conn = psycopg2.connect(
        host="ep-white-firefly-975577-pooler.us-east-1.postgres.vercel-storage.com",
        port="5432",
        database="verceldb",
        user="default",
        password="kyx8GQivump6"
    )
    return conn


def select_member(cursor, lineagew_name, line_name):
    query = "SELECT * FROM member WHERE lineagew_name = %s OR line_name = %s"
    data = (lineagew_name, line_name)
    cursor.execute(query, data)
    return cursor.fetchone()


def insert_member(cursor, conn, lineagew_name, line_name):
    query = "INSERT INTO member (lineagew_name, line_name) VALUES (%s, %s)"
    data = (lineagew_name, line_name)
    cursor.execute(query, data)
    conn.commit()


def close_connection(conn):
    conn.close()
