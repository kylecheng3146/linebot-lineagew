import psycopg2
import os

def connect_to_db():
    conn = psycopg2.connect(
        host = os.getenv("POSTGRES_HOST"),
        port = "5432",
        database = os.getenv("POSTGRES_DATABASE"),
        user = os.getenv("POSTGRES_USER"),
        password = os.getenv("POSTGRES_PASSWORD")
    )
    return conn


def select_member(cursor, lineagew_name, line_name):
    query = "SELECT * FROM member WHERE lineagew_name = %s OR line_name = %s"
    data = (lineagew_name, line_name)
    cursor.execute(query, data)
    return cursor.fetchone()

def select_combat_team(cursor, lineagew_name):
    query = "SELECT * FROM combat_team WHERE lineagew_name = %s"
    data = (lineagew_name)
    cursor.execute(query, data)
    return cursor.fetchone()

def update_member(cursor, lineagew_name, line_name, old_lineagew_name, old_line_name):
    query = "UPDATE member SET lineagew_name = %s, line_name = %s, WHERE lineagew_name = %s OR line_name = %s"
    data = (lineagew_name, line_name, old_lineagew_name, old_line_name)
    cursor.execute(query, data)
    # 提交更新操作
    conn.commit()

def insert_member(cursor, conn, lineagew_name, line_name):
    query = "INSERT INTO member (lineagew_name, line_name) VALUES (%s, %s)"
    data = (lineagew_name, line_name)
    cursor.execute(query, data)
    conn.commit()

def insert_combat_team(cursor, conn, lineagew_name, excitation):
    query = "INSERT INTO combat_team (lineagew_name, excitation) VALUES (%s, %s)"
    data = (lineagew_name, excitation)
    cursor.execute(query, data)
    conn.commit()


def close_connection(conn):
    conn.close()
