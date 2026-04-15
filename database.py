import sqlite3
from flask import g

DATABASE = 'test_generator.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

def execute_query(query, args=(), commit=False):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(query, args)
    if commit:
        db.commit()
    return cursor

def init_db(app):
    with app.app_context():
        db = get_db()
        # Create Tables
        cursor = db.cursor()
        
        # User Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user'
            )
        ''')
        
        # Questions Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                options TEXT NOT NULL, -- JSON string of options
                answer TEXT NOT NULL,
                subject TEXT NOT NULL,
                difficulty TEXT NOT NULL,
                tags TEXT -- Comma separated keywords
            )
        ''')
        
        # Attempts Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                subject TEXT NOT NULL,
                difficulty TEXT NOT NULL,
                score INTEGER NOT NULL,
                total_questions INTEGER NOT NULL,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        db.commit()

def close_db(e=None):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()
