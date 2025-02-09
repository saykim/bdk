from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from app import models, schemas
from app.database import get_db

router = APIRouter(
    prefix="/api/posts",
    tags=["posts"]
)

@router.post("/", response_model=schemas.Post, status_code=status.HTTP_201_CREATED)
def create_post(post: schemas.PostCreate, db: Session = Depends(get_db)):
    db_post = models.Post(**post.model_dump())
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post

@router.get("/", response_model=List[schemas.Post])
def read_posts(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = Query(None, description="검색어 (제목, 내용)"),
    author: Optional[str] = Query(None, description="작성자 검색"),
    db: Session = Depends(get_db)
):
    query = db.query(models.Post)
    
    if search:
        query = query.filter(
            or_(
                models.Post.title.contains(search),
                models.Post.content.contains(search)
            )
        )
    
    if author:
        query = query.filter(models.Post.author.contains(author))
    
    posts = query.offset(skip).limit(limit).all()
    return posts

@router.get("/{post_id}", response_model=schemas.Post)
def read_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return post

@router.put("/{post_id}", response_model=schemas.Post)
def update_post(post_id: int, post: schemas.PostCreate, db: Session = Depends(get_db)):
    db_post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if db_post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    
    for key, value in post.model_dump().items():
        setattr(db_post, key, value)
    
    db.commit()
    db.refresh(db_post)
    return db_post

@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    
    db.delete(post)
    db.commit()
    return None 