import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import os
# import requests
from fastapi import FastAPI, status, Depends, HTTPException, APIRouter
from typing import Generator
from contextlib import contextmanager

# Load environment variables from .env
load_dotenv()

# Fetch variables from environment
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
secret_key = os.getenv("SECRET_KEY")
algorithm = os.getenv("ALGORITHM")

# @contextmanager
def get_db_connection():
    connection = None
    cursor = None
    try:
        connection = psycopg2.connect(user=DB_USER,password=DB_PASSWORD,host=DB_HOST,port=DB_PORT,dbname=DB_NAME)
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        yield cursor
        # connection.commit()
    except Exception as e:
        # if connection:
        #     connection.rollback()
        raise e
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def _connect():
    return psycopg2.connect(user=DB_USER,password=DB_PASSWORD,host=DB_HOST,port=DB_PORT,dbname=DB_NAME)


def execute_returning_one(query: str, params: dict | None = None):
    """
    Execute a DML (INSERT/UPDATE/DELETE) with RETURNING and fetch a single row
    in a short-lived connection (suitable for transaction poolers).
    """
    conn = None
    cur = None
    try:
        conn = _connect()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(query, params or {})
        row = None
        try:
            row = cur.fetchone()
        except Exception:
            row = None
        conn.commit()
        return row
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def execute_all(query: str, params: dict | None = None):
    """
    Execute a SELECT and fetchall in a short-lived connection.
    """
    conn = None
    cur = None
    try:
        conn = _connect()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(query, params or {})
        rows = cur.fetchall()
        return rows
    except Exception as e:
        raise e
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@contextmanager
def get_cursor():
    """
    Context manager for getting a cursor
    """
    connection = None
    try:
        connection = psycopg2.connect(user=DB_USER,password=DB_PASSWORD,host=DB_HOST,port=DB_PORT,dbname=DB_NAME)
        cursor = connection.cursor()
        yield cursor
    except Exception as e:
        if connection:
            connection.rollback()
        raise e
    finally:
        if connection:
            connection.commit()
            connection.close()

def get_datas(cursor,query):
    try:
        cursor.execute(query)
        return cursor.fetchall()
    except Exception as e:
        raise e
    
def get_data(cursor,query):
    try:
        cursor.execute(query)
        return cursor.fetchone()
    except Exception as e:
        raise e

def execute_query(cursor, query, params=None):
    try:
        cursor.execute(query, params or ())
        return cursor.fetchall()
    except Exception as e:
        raise e

def update(cursor,query):
    try:
        cursor.execute(query)
        return
    except Exception as e:
        raise e
    
def insert(cursor,query):
    try:
        cursor.execute(query)
        return
    except Exception as e:
        print(e)
        raise e

def return_insert(cursor,query, params=None):
    try:
        cursor.execute(query, params or ())
        return cursor.fetchone()
    except Exception as e:
        raise e
    
def return_update(cursor,query):
    try:
        cursor.execute(query)
        return cursor.fetchone()
    except Exception as e:
        raise e
    

a= """
    CREATE TABLE IF NOT EXISTS vi.user_details (
        user_id INTEGER PRIMARY KEY,
        full_name TEXT NOT NULL,
        bio TEXT,
        gender TEXT,
        date_of_birth DATE,
        age INTEGER,                     -- optional, or calculate from DOB
        mobile_number TEXT,
        website TEXT,
        interests TEXT,                  -- JSON string or comma-separated
        country TEXT,
        profile_pic_dms TEXT,
        is_private BOOLEAN DEFAULT FALSE,
        last_seen TIMESTAMP WITH TIME ZONE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        
        FOREIGN KEY (user_id) REFERENCES users(id)
    );

"""
def check_db_connection(timeout: int = 5) -> bool:
    """
    Returns True if DB is reachable and responds to SELECT 1, else False.
    """
    conn = None
    try:
        conn = psycopg2.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            connect_timeout=timeout,
        )
        with conn.cursor() as cur:
            # Use lowercase unquoted identifiers to avoid case-sensitive schema issues
            cur.execute("SELECT 1;")
            print(cur.fetchone())
        return True
    except Exception as e:
        print(e)
        return False
    finally:
        if conn:
            conn.close()

print(check_db_connection())