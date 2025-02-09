from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
import json

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    
    # 설정
    app.config['SECRET_KEY'] = 'dev'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////' + os.path.join(app.instance_path, 'worklog.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # JSON 파싱 필터 추가
    @app.template_filter('fromjson')
    def fromjson_filter(value):
        return json.loads(value) if value else []

    # 데이터베이스 초기화
    db.init_app(app)
    migrate.init_app(app, db)

    # 블루프린트 등록
    from .views import main_bp
    app.register_blueprint(main_bp)

    # 데이터베이스 생성
    with app.app_context():
        db.create_all()

    return app 