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

로컬 실행

```bash
uv run uvicorn main:app --reload
```

프로덕션 실행

```bash
ENVIRONMENT=production uv run uvicorn main:app
```

### 3. 테스트 실행

```bash
uv run pytest
```

### Code Quality

```bash
uv run ruff check .
uv run ruff format --check .
```

## API 목록

| Method | Endpoint          | 설명               |
| ------ | ----------------- | ------------------ |
| GET    | `/ai`             | 서버 상태 확인     |
| POST   | `/ai/v1/stt`      | 음성 → 텍스트 변환 |
| POST   | `/ai/v1/feedback` | AI 피드백 생성     |

## 파일 구조

```bash
tree -I "node_modules|.git|**pycache**|audio_data|__pycache__|jupyter"
```
