from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models.user import User
from app import db
from werkzeug.security import generate_password_hash

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('worklog.index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('worklog.index'))
        flash('아이디 또는 비밀번호가 잘못되었습니다.')
    
    return render_template('auth/login.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('worklog.index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        department = request.form.get('department')
        
        if User.query.filter_by(username=username).first():
            flash('이미 존재하는 사용자명입니다.')
            return redirect(url_for('auth.register'))
            
        if User.query.filter_by(email=email).first():
            flash('이미 등록된 이메일입니다.')
            return redirect(url_for('auth.register'))
            
        user = User(username=username, email=email, department=department)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('회원가입이 완료되었습니다. 로그인해주세요.')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/register.html') 