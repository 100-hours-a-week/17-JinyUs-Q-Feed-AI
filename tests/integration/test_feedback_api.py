"""
Feedback API Integration Tests

테스트 대상: POST /ai/interview/feedback/request
- Router → Service(FeedbackService) → Analyzer(AnswerAnalyzerService) 흐름 검증
- 외부 LLM 호출은 mock 처리
- HTTP 요청/응답 형식 및 스키마 필드 검증
"""

from unittest.mock import AsyncMock
from services.feedback_service import feedback_service

class TestFeedbackAPISuccess:
    """Feedback API 성공 케이스 통합 테스트"""

    def test_정상_피드백_생성(
        self,
        client,
        sample_feedback_request_dict,
        sample_analyzer_result_normal,
        sample_rubric_result,
        sample_feedback_content,
    ):
        """
        정상 답변 → analyzer 분석 → 루브릭 평가 → 피드백 생성까지 성공
        (GeminiProvider 호출만 mock)
        """

        # feedback_service.llm과 feedback_service.analyzer.llm은 동일한 객체
        # side_effect로 호출 순서대로 반환값 지정
        feedback_service.llm.generate_structured = AsyncMock(
            side_effect=[
                sample_analyzer_result_normal,   # 1번째: analyzer 호출
                sample_rubric_result,            # 2번째: 루브릭 평가
                sample_feedback_content          # 3번째: 피드백 생성
            ]
        )

        response = client.post("/ai/interview/feedback/request", json=sample_feedback_request_dict)

        assert response.status_code == 200
        body = response.json()

        assert body["message"] == "generate_feedback_success"
        assert body["data"]["user_id"] == sample_feedback_request_dict["user_id"]
        assert body["data"]["question_id"] == sample_feedback_request_dict["question_id"]
        assert body["data"]["weakness"] is False

        # metrics / feedback 구조 검증
        assert isinstance(body["data"]["metrics"], list)
        assert isinstance(body["data"]["feedback"], dict)
        assert len(body["data"]["metrics"]) == 5

        # 외부 호출 횟수 검증 (analyzer + rubric + feedback = 3회)
        assert feedback_service.llm.generate_structured.call_count == 3

    def test_약점_있는_답변_피드백_생성(
        self,
        client,
        sample_feedback_request_dict,
        sample_analyzer_result_with_weakness,
        sample_rubric_result,
        sample_feedback_content,
    ):
        """약점이 있는 답변 → weakness=True 응답"""

        # feedback_service.llm과 feedback_service.analyzer.llm은 동일한 객체
        feedback_service.llm.generate_structured = AsyncMock(
            side_effect=[
                sample_analyzer_result_with_weakness,  # 1번째: analyzer 호출
                sample_rubric_result,                  # 2번째: 루브릭 평가
                sample_feedback_content                # 3번째: 피드백 생성
            ]
        )

        response = client.post("/ai/interview/feedback/request", json=sample_feedback_request_dict)

        assert response.status_code == 200
        body = response.json()

        assert body["message"] == "generate_feedback_success"
        assert body["data"]["weakness"] is True
        assert body["data"]["metrics"] is not None
        assert body["data"]["feedback"] is not None


class TestFeedbackAPIBadCase:
    """Feedback API Bad Case 조기 반환 테스트"""

    def test_bad_case_답변_거부(
        self,
        client,
        sample_feedback_request_dict,
        sample_analyzer_result_bad_case_refuse,
    ):
        """Bad Case(답변 거부) → 루브릭/피드백 생성 없이 조기 반환"""

        # feedback_service.llm과 feedback_service.analyzer.llm은 동일한 객체
        # Bad case면 analyzer 호출 1회 후 조기 반환 (rubric/feedback 호출 없음)
        feedback_service.llm.generate_structured = AsyncMock(
            return_value=sample_analyzer_result_bad_case_refuse
        )

        response = client.post("/ai/interview/feedback/request", json=sample_feedback_request_dict)

        assert response.status_code == 200
        body = response.json()

        assert body["message"] == "bad_case_detected"
        assert body["data"]["bad_case_feedback"]["type"] == "REFUSE_TO_ANSWER"
        assert body["data"]["metrics"] is None
        assert body["data"]["feedback"] is None
        assert body["data"]["weakness"] is None


class TestFeedbackAPIValidation:
    """Feedback API 요청 검증 테스트"""

    def test_필수_필드_누락_user_id(self, client, sample_feedback_request_dict):
        """user_id 누락 → 422"""
        invalid = dict(sample_feedback_request_dict)
        invalid.pop("user_id")

        response = client.post("/ai/interview/feedback/request", json=invalid)
        assert response.status_code == 422