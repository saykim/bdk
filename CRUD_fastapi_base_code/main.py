from typing import Optional
from fastapi import FastAPI, Request, Form, HTTPException, Depends, UploadFile, File  # type: ignore
from fastapi.templating import Jinja2Templates  # type: ignore
from fastapi.staticfiles import StaticFiles  # type: ignore
from fastapi.responses import RedirectResponse, FileResponse  # type: ignore
from fastapi.middleware.cors import CORSMiddleware  # type: ignore
from fastapi.encoders import jsonable_encoder  # type: ignore
from sqlalchemy.orm import Session  # type: ignore
from sqlalchemy import text  # 추가된 부분
from app.routers import posts
from app.database import engine, get_db, SessionLocal
from app import models  # type: ignore
import math
from pathlib import Path
import shutil
import uuid
import os

# 데이터베이스 테이블 생성
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="게시판 API",
    description="FastAPI를 이용한 게시판 CRUD API",
    version="1.0.0"
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000"],  # 실제 프로덕션 환경에서는 구체적인 도메인 지정
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# 정적 파일과 템플릿 설정
BASE_DIR = Path(__file__).resolve().parent
static_dir = BASE_DIR / "app" / "static"

# 디버깅을 위한 출력 추가
print("="*50)
print(f"Current working directory: {Path.cwd()}")
print(f"Base directory: {BASE_DIR}")
print(f"Static directory path: {static_dir}")
print(f"Static directory exists: {static_dir.exists()}")
print(f"CSS file exists: {(static_dir / 'css' / 'style.css').exists()}")
print("="*50)

if not static_dir.exists():
    raise RuntimeError(f"Static directory not found: {static_dir}")

app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

template_dir = BASE_DIR / "app" / "templates"
if not template_dir.exists():
    raise RuntimeError(f"Template directory not found: {template_dir}")
templates = Jinja2Templates(directory=str(template_dir))

# API 라우터 포함
app.include_router(posts.router)

# 상태별 색상 매핑을 위한 템플릿 필터
def status_color(status):
    color_map = {
        "대기": "secondary",
        "진행중": "primary",
        "완료": "success",
        "문제발생": "danger"
    }
    return color_map.get(status, "secondary")

# Jinja2 템플릿에 필터 추가
templates.env.filters["status_color"] = status_color

@app.get("/")
async def home(
    request: Request,
    search: str = None,
    author: str = None,
    category: str = None,
    status: str = None,
    page: int = 1,
    db: Session = Depends(get_db)
):
    per_page = 10
    query = db.query(models.Post)
    
    # 검색 조건 적용
    if search:
        query = query.filter(
            models.Post.title.contains(search) | 
            models.Post.content.contains(search)
        )
    if author:
        query = query.filter(models.Post.author.contains(author))
    if category:
        query = query.filter(models.Post.category == category)
    if status:
        query = query.filter(models.Post.status == status)
    
    total_posts = query.count()
    total_pages = math.ceil(total_posts / per_page) if total_posts > 0 else 1
    
    posts = query.order_by(models.Post.created_at.desc())\
                .offset((page - 1) * per_page)\
                .limit(per_page)\
                .all()
    
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "posts": posts,
            "page": page,
            "total_pages": total_pages,
            "search": search or "",
            "author": author or "",
            "category": category or "",
            "status": status or "",
            "ProcessStatus": models.ProcessStatus
        }
    )

@app.get("/write")
async def create_post_form(request: Request):
    return templates.TemplateResponse("create.html", {"request": request})

@app.post("/write")
async def create_post(
    request: Request,
    title: str = Form(...),
    content: str = Form(...),
    author: str = Form(...),
    category: str = Form(...),
    product_name: str = Form(None),
    process_step: str = Form(None),
    status: str = Form(...),
    attachment: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    try:
        # 파일 업로드 처리
        attachment_path = None
        if attachment and attachment.filename:
            file_extension = attachment.filename.split(".")[-1]
            unique_filename = f"{uuid.uuid4()}.{file_extension}"
            file_path = f"uploads/{unique_filename}"
            
            # uploads 디렉토리가 없으면 생성
            os.makedirs("uploads", exist_ok=True)
            
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(attachment.file, buffer)
            attachment_path = file_path
        
        # 게시글 생성
        post = models.Post(
            title=title.strip(),
            content=content.strip(),
            author=author.strip(),
            category=category,
            product_name=product_name,
            process_step=process_step,
            status=status,
            attachment_path=attachment_path
        )
        
        db.add(post)
        db.commit()
        db.refresh(post)
        
        return RedirectResponse(url="/", status_code=302)
        
    except Exception as e:
        db.rollback()
        return templates.TemplateResponse(
            "create.html",
            {
                "request": request,
                "error": str(e),
                "title": title,
                "content": content,
                "author": author,
                "ProcessStatus": models.ProcessStatus
            },
            status_code=400
        )

@app.get("/view/{post_id}")
async def view_post(request: Request, post_id: int, db: Session = Depends(get_db)):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if post is None:
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse("detail.html", {"request": request, "post": post})

@app.get("/edit/{post_id}")
async def edit_post_form(request: Request, post_id: int, db: Session = Depends(get_db)):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if post is None:
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse("edit.html", {"request": request, "post": post})

@app.post("/edit/{post_id}")
async def edit_post(
    request: Request,
    post_id: int,
    title: str = Form(...),
    content: str = Form(...),
    author: str = Form(...),
    category: str = Form(...),
    product_name: str = Form(None),
    process_step: str = Form(None),
    status: str = Form(...),
    attachment: UploadFile = File(None),
    delete_attachment: bool = Form(False),
    db: Session = Depends(get_db)
):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if post is None:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    
    try:
        # 첨부 파일 처리
        if delete_attachment and post.attachment_path:
            if os.path.exists(post.attachment_path):
                os.remove(post.attachment_path)
            post.attachment_path = None
        
        if attachment and attachment.filename:
            # 기존 파일 삭제
            if post.attachment_path and os.path.exists(post.attachment_path):
                os.remove(post.attachment_path)
            
            # 새 파일 업로드
            file_extension = attachment.filename.split(".")[-1]
            unique_filename = f"{uuid.uuid4()}.{file_extension}"
            file_path = f"uploads/{unique_filename}"
            
            os.makedirs("uploads", exist_ok=True)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(attachment.file, buffer)
            post.attachment_path = file_path
        
        # 게시글 정보 업데이트
        post.title = title.strip()
        post.content = content.strip()
        post.author = author.strip()
        post.category = category
        post.product_name = product_name
        post.process_step = process_step
        post.status = status
        
        db.commit()
        return RedirectResponse(url=f"/view/{post_id}", status_code=302)
        
    except Exception as e:
        db.rollback()
        return templates.TemplateResponse(
            "edit.html",
            {
                "request": request,
                "error": str(e),
                "post": post,
                "ProcessStatus": models.ProcessStatus
            },
            status_code=400
        )

@app.post("/delete/{post_id}")
async def delete_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if post:
        db.delete(post)
        db.commit()
    return RedirectResponse(url="/", status_code=302)

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    file_extension = file.filename.split(".")[-1]
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = f"uploads/{unique_filename}"
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return {"filename": unique_filename, "path": file_path}

@app.get("/download/{post_id}")
async def download_file(post_id: int, db: Session = Depends(get_db)):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post or not post.attachment_path:
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")
    
    if not os.path.exists(post.attachment_path):
        raise HTTPException(status_code=404, detail="파일이 서버에 존재하지 않습니다.")
    
    return FileResponse(
        post.attachment_path,
        filename=os.path.basename(post.attachment_path),
        media_type='application/octet-stream'
    )

# 앱 시작 시 데이터베이스 연결 확인
@app.on_event("startup")
async def startup_event():
    db = None
    try:
        # 데이터베이스 연결 테스트
        db = SessionLocal()
        db.execute(text("SELECT 1"))  # text() 함수 사용
    except Exception as e:
        print(f"데이터베이스 연결 실패: {e}")
        raise e
    finally:
        if db:
            db.close() 