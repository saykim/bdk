# 식품 사업장 일일 작업 일지 시스템

이 프로젝트는 식품 사업장에서 사용하는 수기 일보를 웹 서비스로 제공하는 데모 애플리케이션입니다.

## 주요 기능

- 실시간 생산 기록 작성 및 저장
- 타임피커를 이용한 작업 시간 선택
- 반응형 테이블로 기록 조회
- 간편한 폼 유효성 검사
- 세션 기반 사용자 관리

## 기술 스택

- Backend: Flask
- Database: SQLite
- Frontend: HTML, CSS (Tailwind CSS), JavaScript (Vanilla JS)
- UI Components: Flatpickr (날짜/시간 선택기)

## 설치 방법

1. 가상환경 생성 및 활성화
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

2. 필요한 패키지 설치
```bash
pip install -r requirements.txt
```

## 실행 방법

1. 가상환경이 활성화되어 있는지 확인

2. 애플리케이션 실행
```bash
python run.py
```

3. 웹 브라우저에서 접속
```
http://localhost:5000
```

## 프로젝트 구조

```
daily_worklog/
├── app/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── worklog.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   └── worklog.py
│   └── templates/
│       ├── base.html
│       ├── auth/
│       │   ├── login.html
│       │   └── register.html
│       └── worklog/
│           └── index.html
├── instance/
├── requirements.txt
└── run.py
```

## 사용 방법

1. 회원가입 후 로그인
2. 작업 일지 작성 폼에서 필요한 정보 입력
3. 저장 버튼 클릭하여 작업 일지 저장
4. 하단의 테이블에서 작성된 작업 일지 확인 가능
5. 각 작업 일지는 수정 및 삭제 가능

## 확장 가능한 기능

- 사용자 인증 시스템 강화
- 엑셀 내보내기 기능
- 통계 차트 구현
- 제품별 필터링 기능
- 이미지 업로드 기능

## 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다.
