from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from typing import List, Optional
from datetime import date, datetime
from pydantic import BaseModel
from app.database import get_db
from app.models import Task, User
from app.routers.auth import oauth2_scheme
from app.security import decode_token

router = APIRouter(prefix="/tasks", tags=["tasks"])

class TaskCreate(BaseModel):
    order_number: str
    name: str
    description: Optional[str] = None
    priority: Optional[int] = 0
    start_time: Optional[datetime] = None
    due_date: Optional[datetime] = None
    assignee_id: Optional[int] = None

class TaskUpdate(BaseModel):
    order_number: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[int] = None
    start_time: Optional[datetime] = None
    due_date: Optional[datetime] = None
    completed: Optional[bool] = None
    assignee_id: Optional[int] = None

class UserInfo(BaseModel):
    id: int
    email: str
    name: str

    class Config:
        from_attributes = True

class TaskResponse(BaseModel):
    id: int
    order_number: str
    name: str
    description: Optional[str]
    priority: int
    start_time: Optional[datetime]
    due_date: Optional[datetime]
    completed: bool
    author_id: int
    assignee_id: Optional[int]
    created_at: datetime
    author: Optional[UserInfo]
    assignee: Optional[UserInfo]

    class Config:
        from_attributes = True

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = decode_token(token)
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except:
        raise credentials_exception
        
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user

@router.post("/", response_model=dict)
async def create_task(
    task: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_task = Task(
        **task.dict(),
        author_id=current_user.id
    )
    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)
    return {"message": "Task created successfully", "task_id": new_task.id}

@router.get("/", response_model=List[TaskResponse])
async def read_tasks(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 작업 목록과 관련된 사용자 정보를 함께 조회
    result = await db.execute(
        select(Task, User.email.label("author_email"), User.name.label("author_name"))
        .outerjoin(User, Task.author_id == User.id)
        .offset(skip)
        .limit(limit)
    )
    tasks_with_authors = result.all()
    
    task_responses = []
    for task_row in tasks_with_authors:
        task = task_row[0]  # Task 객체
        
        # 작성자 정보 설정
        author = UserInfo(
            id=task.author_id,
            email=task_row.author_email,
            name=task_row.author_name
        ) if task.author_id else None
        
        # 담당자 정보 조회
        assignee = None
        if task.assignee_id:
            assignee_result = await db.execute(
                select(User).where(User.id == task.assignee_id)
            )
            assignee_user = assignee_result.scalar_one_or_none()
            if assignee_user:
                assignee = UserInfo(
                    id=assignee_user.id,
                    email=assignee_user.email,
                    name=assignee_user.name
                )
        
        task_dict = {
            "id": task.id,
            "order_number": task.order_number,
            "name": task.name,
            "description": task.description,
            "priority": task.priority,
            "start_time": task.start_time,
            "due_date": task.due_date,
            "completed": task.completed,
            "author_id": task.author_id,
            "assignee_id": task.assignee_id,
            "created_at": task.created_at,
            "author": author,
            "assignee": assignee
        }
        task_responses.append(TaskResponse(**task_dict))
    
    return task_responses

@router.put("/{task_id}", response_model=dict)
async def update_task(
    task_id: int,
    task_update: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    update_data = task_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(task, key, value)
    
    await db.commit()
    return {"message": "Task updated successfully"}

@router.delete("/{task_id}", response_model=dict)
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    await db.delete(task)
    await db.commit()
    return {"message": "Task deleted successfully"} 