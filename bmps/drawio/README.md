# 프로세스 맵 에디터

프로세스 맵을 쉽게 만들고 관리할 수 있는 웹 기반 에디터입니다.

## 주요 기능

- 도형 추가 및 이동
- 도형 간 연결선 생성
- 다이어그램 저장 및 불러오기
- 확대/축소 및 이동 기능
- 실시간 미리보기

## 기술 스택

- Backend: FastAPI
- Frontend: HTML5 Canvas, JavaScript
- Database: SQLite

## 설치 방법

1. 필요한 패키지 설치:
```bash
pip install -r requirements.txt
```

2. 서버 실행:
```bash
uvicorn main:app --reload
```

3. 웹 브라우저에서 접속:
```
http://localhost:8000
```

## 사용 방법

1. "도형 추가" 버튼을 클릭하여 새로운 도형을 추가합니다.
2. 도형을 드래그하여 위치를 조정합니다.
3. 도형의 연결점(파란색 점)을 드래그하여 다른 도형과 연결합니다.
4. 다이어그램 이름을 입력하고 "저장" 버튼을 클릭하여 작업을 저장합니다.
5. 저장된 다이어그램은 왼쪽 사이드바에서 불러올 수 있습니다.

## 단축키

- Delete: 선택한 도형 삭제
- 마우스 휠: 확대/축소
- 드래그: 도형 이동 또는 연결선 생성 