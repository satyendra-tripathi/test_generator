import sqlite3
import json
from werkzeug.security import generate_password_hash
from nlp_utils import extract_keywords, tag_difficulty
import os

DATABASE = 'test_generator.db'

sample_questions = [
    {
        "question": "What is the powerhouse of the cell?",
        "options": ["Nucleus", "Mitochondria", "Ribosome", "Endoplasmic Reticulum"],
        "answer": "Mitochondria",
        "subject": "Biology",
    },
    {
        "question": "Solve for x: 2x + 5 = 15",
        "options": ["5", "10", "4", "6"],
        "answer": "5",
        "subject": "Math",
    },
    {
        "question": "Who wrote 'Romeo and Juliet'?",
        "options": ["Charles Dickens", "William Shakespeare", "Jane Austen", "Mark Twain"],
        "answer": "William Shakespeare",
        "subject": "English",
    },
    {
        "question": "What is the chemical symbol for gold?",
        "options": ["Au", "Ag", "Pb", "Fe"],
        "answer": "Au",
        "subject": "Chemistry",
    },
    {
        "question": "Calculate the derivative of f(x) = 3x^2 + 2x with respect to x.",
        "options": ["6x + 2", "3x + 2", "6x^2", "x^2 + 2x"],
        "answer": "6x + 2",
        "subject": "Math"
    },
    {
        "question": "Explain the concept of quantum entanglement and its implications for faster-than-light communication.",
        "options": ["Instant communication", "Information transfer", "Particles correlation", "No faster-than-light communication allowed"],
        "answer": "No faster-than-light communication allowed",
        "subject": "Physics"
    }
]

def initialize():
    # Remove existing db to start fresh (for dev purposes)
    if os.path.exists(DATABASE):
        os.remove(DATABASE)

    # Note: normally we would call app.app_context() from Flask, but here we can just execute sqlite3 commands directly
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Create Tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user'
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            options TEXT NOT NULL,
            answer TEXT NOT NULL,
            subject TEXT NOT NULL,
            difficulty TEXT NOT NULL,
            tags TEXT
        )
    ''')
    
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
    
    # Insert Admin User
    admin_password = generate_password_hash('admin123')
    cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                   ('admin', admin_password, 'admin'))
                   
    # Insert Sample User
    user_password = generate_password_hash('user123')
    cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                   ('testuser', user_password, 'user'))

    # Insert Sample Questions
    for q in sample_questions:
        print(f"Processing question: {q['question']}")
        difficulty = tag_difficulty(q['question'])
        keywords = extract_keywords(q['question'])
        tags_str = ", ".join(keywords)
        
        cursor.execute('''
            INSERT INTO questions (question, options, answer, subject, difficulty, tags)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (q['question'], json.dumps(q['options']), q['answer'], q['subject'], difficulty, tags_str))
        
    conn.commit()
    conn.close()
    print("Database initialized successfully with sample data!")

if __name__ == '__main__':
    initialize()
