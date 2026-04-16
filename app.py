from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from database import init_db, get_db, close_db, execute_query
from nlp_utils import tag_difficulty, extract_keywords
import json
import random
import sqlite3

app = Flask(__name__)
app.secret_key = 'super_secret_test_generator_key'

# Initialization happens when we run init_db.py separately, but we still ensure close_db runs
app.teardown_appcontext(close_db)

# --- MIDDLEWARE & HELPERS ---
def get_current_user():
    user_id = session.get('user_id')
    if not user_id:
        return None
    cursor = execute_query("SELECT * FROM users WHERE id = ?", (user_id,))
    return cursor.fetchone()

def login_required(func):
    def wrapper(*args, **kwargs):
        if not session.get('user_id'):
            flash("Please log in to access this page.", "warning")
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

def admin_required(func):
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if not user or user['role'] != 'admin':
            flash("Admin access required.", "danger")
            return redirect(url_for('index'))
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

# --- PUBLIC ROUTES ---
@app.route('/')
def index():
    if 'user_id' in session:
        user = get_current_user()
        if user['role'] == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('user_dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        cursor = execute_query("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            flash('Logged in successfully!', 'success')
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('user_dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
            
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        db = get_db()
        cursor = db.cursor()
        
        try:
            hashed_pw = generate_password_hash(password)
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_pw))
            db.commit()
            flash('Account created! Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username already taken.', 'danger')
            
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

# --- USER ROUTES ---
@app.route('/dashboard')
@login_required
def user_dashboard():
    user = get_current_user()
    if user['role'] == 'admin': return redirect(url_for('admin_dashboard'))
    
    # Get available subjects for test generation
    cursor = execute_query("SELECT DISTINCT subject FROM questions")
    subjects = [row['subject'] for row in cursor.fetchall()]
    
    # Get previous attempts
    cursor = execute_query("SELECT * FROM attempts WHERE user_id = ? ORDER BY date DESC", (user['id'],))
    attempts = cursor.fetchall()
    
    return render_template('user_dashboard.html', user=user, subjects=subjects, attempts=attempts)

@app.route('/generate_test', methods=['POST'])
@login_required
def generate_test():
    subject = request.form['subject']
    difficulty = request.form.get('difficulty') # Can be 'All' or specific
    
    query = "SELECT * FROM questions WHERE subject = ?"
    params = [subject]
    
    if difficulty and difficulty != 'All':
        query += " AND difficulty = ?"
        params.append(difficulty)
        
    cursor = execute_query(query, tuple(params))
    questions = cursor.fetchall()
    
    if len(questions) == 0:
        flash("No questions found for the selected criteria.", "warning")
        return redirect(url_for('user_dashboard'))
        
    # Pick up to 5 random questions
    test_questions = random.sample(questions, min(len(questions), 5))
    
    # Convert sqlite3.Row to dict for session serialization
    test_q_dicts = []
    for q in test_questions:
        test_q_dicts.append({
            'id': q['id'],
            'question': q['question'],
            'options': json.loads(q['options']),
            'answer': q['answer'],
            'subject': q['subject'],
            'difficulty': q['difficulty']
        })
        
    # Store current test session
    session['current_test'] = test_q_dicts
    session['test_metadata'] = {'subject': subject, 'difficulty': difficulty if difficulty else 'Mixed'}
    
    return redirect(url_for('test_page'))

@app.route('/test_page')
@login_required
def test_page():
    test_data = session.get('current_test')
    if not test_data:
        flash("No active test. Generate one first.", "danger")
        return redirect(url_for('user_dashboard'))
        
    return render_template('test_page.html', questions=test_data)

@app.route('/submit_test', methods=['POST'])
@login_required
def submit_test():
    test_data = session.get('current_test')
    if not test_data:
        return redirect(url_for('user_dashboard'))
        
    score = 0
    total = len(test_data)
    
    for q in test_data:
        user_answer = request.form.get(f"q_{q['id']}")
        if user_answer == q['answer']:
            score += 1
            
    # Save attempt to DB
    user_id = session['user_id']
    meta = session.get('test_metadata', {'subject': 'Unknown', 'difficulty': 'Unknown'})
    
    execute_query(
        "INSERT INTO attempts (user_id, subject, difficulty, score, total_questions) VALUES (?, ?, ?, ?, ?)",
        (user_id, meta['subject'], meta['difficulty'], score, total),
        commit=True
    )
    
    # Clear test session state but pass results logic
    session.pop('current_test', None)
    session.pop('test_metadata', None)
    
    return render_template('results.html', score=score, total=total)

# --- ADMIN ROUTES ---
@app.route('/admin_dashboard')
@login_required
@admin_required
def admin_dashboard():
    # Fetch questions
    cursor = execute_query("SELECT * FROM questions ORDER BY id DESC")
    questions = cursor.fetchall()
    
    # Fetch user performance overview
    cursor = execute_query('''
        SELECT u.username, a.subject, a.score, a.total_questions, a.date 
        FROM attempts a 
        JOIN users u ON a.user_id = u.id 
        ORDER BY a.date DESC LIMIT 20
    ''')
    recent_attempts = cursor.fetchall()
    
    return render_template('admin_dashboard.html', questions=questions, attempts=recent_attempts)

@app.route('/add_question', methods=['POST'])
@login_required
@admin_required
def add_question():
    question = request.form['question']
    opt1 = request.form['opt1']
    opt2 = request.form['opt2']
    opt3 = request.form['opt3']
    opt4 = request.form['opt4']
    answer = request.form['answer'] # Ensure it matches one of the options
    subject = request.form['subject']
    
    options = [opt1, opt2, opt3, opt4]
    
    # Auto tag with NLP
    difficulty = tag_difficulty(question)
    tags = extract_keywords(question)
    
    execute_query('''
        INSERT INTO questions (question, options, answer, subject, difficulty, tags) 
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (question, json.dumps(options), answer, subject, difficulty, ", ".join(tags)), commit=True)
    
    flash("Question added successfully! NLP tagged it as " + difficulty, "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/delete_question/<int:q_id>', methods=['POST'])
@login_required
@admin_required
def delete_question(q_id):
    execute_query("DELETE FROM questions WHERE id = ?", (q_id,), commit=True)
    flash("Question deleted.", "info")
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

