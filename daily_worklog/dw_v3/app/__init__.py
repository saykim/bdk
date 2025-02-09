from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from datetime import datetime
import os

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    
    # 기본 설정
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///worklog.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # 데이터베이스 초기화
    db.init_app(app)
    
    # 로그인 매니저 설정
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '로그인이 필요한 페이지입니다.'

    with app.app_context():
        # 모델 임포트
        from app.models import user, worklog
        
        # 블루프린트 등록
        from app.routes import auth, worklog
        app.register_blueprint(auth.bp)
        app.register_blueprint(worklog.bp)

        # 데이터베이스 생성
        db.create_all()

        return app 