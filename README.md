1. 프로젝트 초기화
   ''' uv init '''

2. 프로젝트 실행(uv run을 통해 가상환경도 동시에 실행)

- fastAPI 서버 실행
  uv run uvicorn main:app --reload

- 테스트 실행
  uv run python main.py
  uv run pytest

- AI서버 API 리스트
- /api/v1/stt
- /api/v1/feedback
