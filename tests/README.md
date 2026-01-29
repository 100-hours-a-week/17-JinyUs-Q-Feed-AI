# QFeed AI 테스트 가이드

## 테스트 구조

```
tests/
├── conftest.py         # 공통 fixtures (app, client, 마커)
├── unit/               # 단위 테스트 (Mock 사용, 빠른 실행)
│   ├── conftest.py     # Unit 전용 fixtures
│   ├── providers/      # LLM, STT Provider 테스트
│   └── services/       # 서비스 로직 테스트
├── integration/        # 통합 테스트 (Router → Service, 외부 API Mock)
│   ├── conftest.py     # Integration 전용 fixtures
│   ├── test_feedback_api.py
│   └── test_stt_api.py
└── e2e/                # E2E 테스트 (실제 서버 + 실제 API)
    ├── conftest.py     # E2E 전용 fixtures
    └── test_feedback_e2e.py
```

## 테스트 레벨 비교

---

## 테스트 실행 방법

### 전체 테스트 실행 (E2E 제외)

```bash
uv run pytest tests/unit tests/integration
```

### Unit 테스트만 실행

```bash
uv run pytest tests/unit
```

### Integration 테스트만 실행

```bash
uv run pytest tests/integration
```

### E2E 테스트 실행 (수동 방식)

> ⚠️ **주의**: E2E 테스트는 실제 Gemini API를 호출합니다. API 비용이 발생할 수 있습니다.

E2E 테스트는 **서버를 먼저 실행**한 후 별도로 테스트를 실행합니다.

```bash
# 1. 터미널 1: 서버 실행
uv run uvicorn main:app --port 8000

# 2. 터미널 2: E2E 테스트 실행
uv run pytest tests/e2e -v
```

```bash
# 특정 테스트만 실행
uv run pytest tests/e2e/test_feedback_e2e.py::TestFeedbackE2ENormalCases -v
```

### 특정 파일만 실행

```bash
uv run pytest tests/{파일 경로}
```
