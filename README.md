# Q-Feed AI Server

AI 기반 기술 면접 연습 플랫폼의 AI 서버입니다.

## 기술 스택

- Python 3.12
- FastAPI
- uv (패키지 매니저)

## 설치 및 실행

### 1. 프로젝트 초기화

```bash
uv sync
```

### 2. 서버 실행

```bash
uv run uvicorn main:app --reload
```

### 3. 테스트 실행

```bash
uv run pytest
```

## API 목록

| Method | Endpoint           | 설명               |
| ------ | ------------------ | ------------------ |
| GET    | `/`                | 서버 상태 확인     |
| POST   | `/api/v1/stt`      | 음성 → 텍스트 변환 |
| POST   | `/api/v1/feedback` | AI 피드백 생성     |
