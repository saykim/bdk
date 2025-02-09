from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app import models
from app.database import engine, get_db, AsyncSessionLocal
from app.routers import tasks, auth
from app.security import get_password_hash

app = FastAPI(title="Todo App")

# 정적 파일과 템플릿 설정
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# 라우터 포함
app.include_router(auth.router)
app.include_router(tasks.router)

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)
    
    # 기본 계정들 생성
    test_users = [
        {"email": "admin@example.com", "password": "admin123", "name": "관리자"},
        {"email": "user1@example.com", "password": "user123", "name": "김철수"},
        {"email": "user2@example.com", "password": "user123", "name": "이영희"},
        {"email": "user3@example.com", "password": "user123", "name": "박민수"},
        {"email": "user4@example.com", "password": "user123", "name": "정지원"},
        {"email": "user5@example.com", "password": "user123", "name": "한미영"}
    ]
    
    async with AsyncSessionLocal() as session:
        for user_data in test_users:
            result = await session.execute(
                select(models.User).where(models.User.email == user_data["email"])
            )
            if not result.scalar_one_or_none():
                user = models.User(
                    email=user_data["email"],
                    hashed_password=get_password_hash(user_data["password"]),
                    name=user_data["name"]
                )
                session.add(user)
        
        await session.commit()

@app.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register")
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request}) 