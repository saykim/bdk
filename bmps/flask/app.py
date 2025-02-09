from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime
from dotenv import load_dotenv
from functools import wraps

# 환경변수 로드
load_dotenv()

app = Flask(__name__)

# CORS 설정 - 특정 도메인만 허용
CORS(app, resources={
    r"/api/*": {
        "origins": os.getenv('ALLOWED_ORIGINS', 'http://localhost:5000').split(','),
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type", "X-Admin-Password"]
    }
})

# 데이터베이스 설정
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///bpmn.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')  # 환경변수로 이동
db = SQLAlchemy(app)

# 캐시 설정
CACHE_TIMEOUT = 300  # 5분
process_cache = {}

# 모델 정의
class Process(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    xml_data = db.Column(db.Text, nullable=False)
    major_version = db.Column(db.Integer, nullable=False)
    minor_version = db.Column(db.Integer, nullable=False)
    author = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.Index('idx_name_version', 'name', 'major_version', 'minor_version'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'major_version': self.major_version,
            'minor_version': self.minor_version,
            'author': self.author,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

# 에러 핸들러
@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'error': 'Internal server error'}), 500

# 관리자 인증 데코레이터
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not ADMIN_PASSWORD:
            return jsonify({'error': 'Admin password not configured'}), 500
        if request.headers.get('X-Admin-Password') != ADMIN_PASSWORD:
            return jsonify({'error': '관리자 인증이 필요합니다'}), 401
        return f(*args, **kwargs)
    return decorated_function

# 입력값 검증
def validate_process_data(data):
    required_fields = ['name', 'author', 'xml']
    if not all(field in data for field in required_fields):
        return False, '필수 필드가 누락되었습니다'
    if len(data['name']) > 100:
        return False, '프로세스 이름이 너무 깁니다'
    if len(data['author']) > 100:
        return False, '작성자 이름이 너무 깁니다'
    return True, None

# 라우트 정의
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/process', methods=['POST'])
def save_process():
    try:
        data = request.json
        print('Received data:', data)  # 디버깅 로그
        
        # 입력값 검증
        is_valid, error_message = validate_process_data(data)
        if not is_valid:
            print('Validation error:', error_message)  # 디버깅 로그
            return jsonify({'error': error_message}), 400
            
        name = data['name']
        author = data['author']
        xml_data = data['xml']
        
        print('Processing:', name, author)  # 디버깅 로그
        
        # 동일한 이름의 최신 버전 프로세스 찾기
        existing_process = Process.query.filter_by(name=name).order_by(
            Process.major_version.desc(),
            Process.minor_version.desc()
        ).first()

        if existing_process and data.get('is_major_update'):
            major_version = existing_process.major_version + 1
            minor_version = 0
        elif existing_process:
            major_version = existing_process.major_version
            minor_version = existing_process.minor_version + 1
        else:
            major_version = 1
            minor_version = 0

        print('Version:', major_version, minor_version)  # 디버깅 로그

        process = Process(
            name=name,
            xml_data=xml_data,
            major_version=major_version,
            minor_version=minor_version,
            author=author
        )
        
        db.session.add(process)
        db.session.commit()
        
        # 캐시 무효화
        process_cache.clear()
        
        return jsonify({
            'message': 'Process saved successfully',
            'id': process.id,
            'major_version': major_version,
            'minor_version': minor_version
        })
    except Exception as e:
        print('Error:', str(e))  # 디버깅 로그
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/process/<int:id>', methods=['GET'])
def get_process(id):
    # 캐시 확인
    cache_key = f'process_{id}'
    if cache_key in process_cache:
        return jsonify(process_cache[cache_key])
        
    process = Process.query.get_or_404(id)
    result = {
        'id': process.id,
        'name': process.name,
        'xml': process.xml_data,
        'major_version': process.major_version,
        'minor_version': process.minor_version,
        'author': process.author
    }
    
    # 캐시 저장
    process_cache[cache_key] = result
    return jsonify(result)

@app.route('/api/processes', methods=['GET'])
def get_processes():
    # 캐시 확인
    cache_key = 'all_processes'
    if cache_key in process_cache:
        return jsonify(process_cache[cache_key])
        
    processes = Process.query.order_by(
        Process.name,
        Process.major_version.desc(),
        Process.minor_version.desc()
    ).all()
    result = [p.to_dict() for p in processes]
    
    # 캐시 저장
    process_cache[cache_key] = result
    return jsonify(result)

@app.route('/api/process/<int:id>', methods=['DELETE'])
@admin_required
def delete_process(id):
    try:
        process = Process.query.get_or_404(id)
        db.session.delete(process)
        db.session.commit()
        
        # 캐시 무효화
        process_cache.clear()
        
        return jsonify({'message': 'Process deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/process/versions/<name>', methods=['GET'])
def get_process_versions(name):
    # 캐시 확인
    cache_key = f'versions_{name}'
    if cache_key in process_cache:
        return jsonify(process_cache[cache_key])
        
    versions = Process.query.filter_by(name=name).order_by(
        Process.major_version.desc(),
        Process.minor_version.desc()
    ).all()
    result = [p.to_dict() for p in versions]
    
    # 캐시 저장
    process_cache[cache_key] = result
    return jsonify(result)

# 데이터베이스 초기화 함수
def init_db():
    with app.app_context():
        # 기존 테이블 삭제
        db.drop_all()
        # 새 테이블 생성
        db.create_all()
        print("데이터베이스가 초기화되었습니다.")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true') 