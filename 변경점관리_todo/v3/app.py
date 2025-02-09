import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, g, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev'
app.config['DATABASE'] = os.path.join(app.instance_path, 'tasks.db')

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# 데이터베이스 연결
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()

# 데이터베이스 초기화
def init_db():
    if not os.path.exists(app.instance_path):
        os.makedirs(app.instance_path)
    
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql') as f:
            db.executescript(f.read().decode('utf8'))
        db.commit()

# User 클래스 정의
class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if user is None:
        return None
    return User(user['id'], user['username'])

# 라우트 정의
@app.route('/')
@login_required
def index():
    status_filter = request.args.get('status', 'all')
    db = get_db()
    
    if status_filter == 'all':
        tasks = db.execute(
            'SELECT * FROM tasks ORDER BY created_at DESC'
        ).fetchall()
    else:
        tasks = db.execute(
            'SELECT * FROM tasks WHERE status = ? ORDER BY created_at DESC',
            (status_filter,)
        ).fetchall()
    
    return render_template('index.html', tasks=tasks, current_status=status_filter)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None
        user = db.execute(
            'SELECT * FROM users WHERE username = ?', (username,)
        ).fetchone()

        if user is None:
            error = '잘못된 사용자명입니다.'
        elif not check_password_hash(user['password'], password):
            error = '잘못된 비밀번호입니다.'

        if error is None:
            login_user(User(user['id'], user['username']))
            return redirect(url_for('index'))

        flash(error)

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None

        if not username:
            error = '사용자명이 필요합니다.'
        elif not password:
            error = '비밀번호가 필요합니다.'
        elif db.execute(
            'SELECT id FROM users WHERE username = ?', (username,)
        ).fetchone() is not None:
            error = f'사용자 {username}은(는) 이미 등록되어 있습니다.'

        if error is None:
            db.execute(
                'INSERT INTO users (username, password) VALUES (?, ?)',
                (username, generate_password_hash(password))
            )
            db.commit()
            return redirect(url_for('login'))

        flash(error)

    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/add_task', methods=['POST'])
@login_required
def add_task():
    order_number = request.form['order_number']
    work_order = request.form['work_order']
    description = request.form['description']
    start_date = request.form['start_date']
    end_date = request.form['end_date']
    assignee = request.form['assignee']
    
    db = get_db()
    db.execute(
        'INSERT INTO tasks (order_number, work_order, description, start_date, end_date, assignee, created_by)'
        ' VALUES (?, ?, ?, ?, ?, ?, ?)',
        (order_number, work_order, description, start_date, end_date, assignee, current_user.id)
    )
    db.commit()
    flash('작업이 성공적으로 추가되었습니다.')
    return redirect(url_for('index'))

@app.route('/task/<int:task_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    db = get_db()
    task = db.execute('SELECT * FROM tasks WHERE id = ?', (task_id,)).fetchone()
    
    if task is None:
        flash('작업을 찾을 수 없습니다.')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        order_number = request.form['order_number']
        work_order = request.form['work_order']
        description = request.form['description']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        assignee = request.form['assignee']
        status = request.form['status']
        
        db.execute(
            'UPDATE tasks SET order_number = ?, work_order = ?, description = ?, '
            'start_date = ?, end_date = ?, assignee = ?, status = ? '
            'WHERE id = ?',
            (order_number, work_order, description, start_date, end_date, 
             assignee, status, task_id)
        )
        db.commit()
        flash('작업이 성공적으로 수정되었습니다.')
        return redirect(url_for('index'))
    
    return render_template('edit_task.html', task=task)

@app.route('/task/<int:task_id>/delete', methods=['POST'])
@login_required
def delete_task(task_id):
    db = get_db()
    db.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
    db.commit()
    flash('작업이 삭제되었습니다.')
    return redirect(url_for('index'))

@app.route('/task/<int:task_id>/status', methods=['POST'])
@login_required
def update_status(task_id):
    new_status = request.form['status']
    db = get_db()
    db.execute(
        'UPDATE tasks SET status = ? WHERE id = ?',
        (new_status, task_id)
    )
    db.commit()
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    init_db()
    app.run(debug=True) 