# FastAPI 게시판 API

FastAPI와 SQLite를 이용한 간단한 게시판 API 서버입니다.

## 기능
- 게시글 작성
- 게시글 조회 (목록/상세)
- 게시글 수정
- 게시글 삭제

## 설치 및 실행

1. 가상환경 생성 및 활성화
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

2. 패키지 설치
```bash
pip install -r requirements.txt
```

3. 서버 실행
```bash
uvicorn main:app --reload
```

## API 문서
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc
