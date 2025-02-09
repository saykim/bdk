from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Index, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import sessionmaker, Session, declarative_base
import os
from datetime import datetime
from dotenv import load_dotenv
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from pathlib import Path

# 환경변수 로드
load_dotenv()

# 기본 경로 설정
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATE_DIR = BASE_DIR / "templates"

app = FastAPI(title="BPMN Process Manager")

# CORS 설정
origins = os.getenv('ALLOWED_ORIGINS', 'http://localhost:5000').split(',')
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 오리진 허용
    allow_credentials=True,
    allow_methods=["*"],  # 모든 메서드 허용
    allow_headers=["*"],  # 모든 헤더 허용
)

# 정적 파일과 템플릿 설정
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))

# Jinja2 환경 설정
templates.env.globals.update({
    "url_for": lambda name, **path_params: app.url_path_for(name, **path_params) if name != "static" 
    else f"/static/{path_params['filename']}"
})

# 데이터베이스 설정
SQLALCHEMY_DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///instance/bpmn.db')
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 관리자 비밀번호
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')

# 캐시 설정
CACHE_TIMEOUT = 300
process_cache = {}

# 모델 정의
class Process(Base):
    __tablename__ = "process"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    xml_data = Column(Text, nullable=False)
    major_version = Column(Integer, nullable=False)
    minor_version = Column(Integer, nullable=False)
    author = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_name_version', 'name', 'major_version', 'minor_version'),
    )

# Pydantic 모델
class ProcessBase(BaseModel):
    name: str
    author: str
    xml: str
    is_major_update: Optional[bool] = False

class ProcessResponse(BaseModel):
    id: int
    name: str
    major_version: int
    minor_version: int
    author: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# 데이터베이스 의존성
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 관리자 인증 의존성
async def verify_admin(request: Request):
    admin_password = request.headers.get('X-Admin-Password')
    if not ADMIN_PASSWORD:
        raise HTTPException(status_code=500, detail="Admin password not configured")
    if not admin_password:
        raise HTTPException(status_code=401, detail="관리자 비밀번호가 필요합니다")
    if admin_password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="잘못된 관리자 비밀번호입니다")
    return True

# 입력값 검증
def validate_process_data(data: ProcessBase):
    if len(data.name) > 100:
        return False, "프로세스 이름이 너무 깁니다"
    if len(data.author) > 100:
        return False, "작성자 이름이 너무 깁니다"
    return True, None

# 라우트 정의
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/process", response_model=dict)
async def save_process(process: ProcessBase, db: Session = Depends(get_db)):
    try:
        # 입력값 검증
        is_valid, error_message = validate_process_data(process)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_message)

        # 동일한 이름의 최신 버전 프로세스 찾기
        existing_process = db.query(Process).filter_by(name=process.name).order_by(
            Process.major_version.desc(),
            Process.minor_version.desc()
        ).first()

        if existing_process and process.is_major_update:
            major_version = existing_process.major_version + 1
            minor_version = 0
        elif existing_process:
            major_version = existing_process.major_version
            minor_version = existing_process.minor_version + 1
        else:
            major_version = 1
            minor_version = 0

        new_process = Process(
            name=process.name,
            xml_data=process.xml,
            major_version=major_version,
            minor_version=minor_version,
            author=process.author
        )

        db.add(new_process)
        db.commit()
        db.refresh(new_process)

        # 캐시 무효화
        process_cache.clear()

        return {
            'message': 'Process saved successfully',
            'id': new_process.id,
            'major_version': major_version,
            'minor_version': minor_version
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/process/{id}", response_model=dict)
async def get_process(id: int, db: Session = Depends(get_db)):
    # 캐시 확인
    cache_key = f'process_{id}'
    if cache_key in process_cache:
        return process_cache[cache_key]

    process = db.query(Process).get(id)
    if not process:
        raise HTTPException(status_code=404, detail="Process not found")

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
    return result

@app.get("/api/processes", response_model=List[ProcessResponse])
async def get_processes(db: Session = Depends(get_db)):
    # 캐시 확인
    cache_key = 'all_processes'
    if cache_key in process_cache:
        return process_cache[cache_key]

    processes = db.query(Process).order_by(
        Process.name,
        Process.major_version.desc(),
        Process.minor_version.desc()
    ).all()

    result = [ProcessResponse.from_orm(p) for p in processes]
    
    # 캐시 저장
    process_cache[cache_key] = result
    return result

@app.delete("/api/process/{id}", response_model=dict)
async def delete_process(
    id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    try:
        # 관리자 인증 체크
        await verify_admin(request)
        
        process = db.query(Process).get(id)
        if not process:
            raise HTTPException(status_code=404, detail="Process not found")

        db.delete(process)
        db.commit()

        # 캐시 무효화
        process_cache.clear()

        return {'message': 'Process deleted successfully'}
    except HTTPException as e:
        raise e
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/process/versions/{name}", response_model=List[ProcessResponse])
async def get_process_versions(name: str, db: Session = Depends(get_db)):
    # 캐시 확인
    cache_key = f'versions_{name}'
    if cache_key in process_cache:
        return process_cache[cache_key]

    versions = db.query(Process).filter_by(name=name).order_by(
        Process.major_version.desc(),
        Process.minor_version.desc()
    ).all()

    result = [ProcessResponse.from_orm(p) for p in versions]

    # 캐시 저장
    process_cache[cache_key] = result
    return result

# 데이터베이스 초기화 함수
def init_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("데이터베이스가 초기화되었습니다.")

if __name__ == "__main__":
    import uvicorn
    Base.metadata.create_all(bind=engine)
    uvicorn.run(app, host="0.0.0.0", port=8000) 