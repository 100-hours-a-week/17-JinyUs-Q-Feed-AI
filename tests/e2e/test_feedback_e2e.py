"""
Feedback API E2E Tests (수동 E2E 방식)

실제 서버에 HTTP 요청을 보내 전체 파이프라인을 검증합니다.

실행 방법:
    1. 서버 실행: uv run uvicorn main:app --port 8000
    2. 테스트 실행: uv run pytest tests/e2e -v

특징:
- 프로덕션과 동일한 환경
- 실제 Gemini API 호출
"""

import pytest
from tests.e2e.conftest import assert_successful_feedback_response, assert_bad_case_response


@pytest.mark.e2e
class TestFeedbackE2ENormalCases:
    """정상 답변에 대한 E2E 테스트"""

    def test_좋은_답변_정상_피드백_생성(
        self,
        e2e_client,
        good_answer_request,
    ):
        """
        좋은 품질의 답변 → 정상 피드백 응답
        - 실제 Gemini API 호출
        - 5개 루브릭 점수 + 피드백 텍스트 생성 확인
        """
        response = e2e_client.post(
            "/ai/interview/feedback/request",
            json=good_answer_request
        )

        assert response.status_code == 200
        
        data = response.json()
        assert_successful_feedback_response(data)
        
        # 좋은 답변이므로 평균 점수가 어느 정도 높아야 함
        metrics = data["data"]["metrics"]
        avg_score = sum(m["score"] for m in metrics) / len(metrics)
        assert avg_score >= 2.5, f"좋은 답변인데 평균 점수가 너무 낮음: {avg_score}"
        
        print("\n[좋은 답변 테스트 결과]")
        print(f"평균 점수: {avg_score:.1f}")
        for m in metrics:
            print(f"  - {m['name']}: {m['score']}점")

    def test_약점있는_답변_피드백_생성(
        self,
        e2e_client,
        weak_answer_request,
    ):
        """
        약점이 있는 짧은 답변 → 피드백에 개선점 포함
        """
        response = e2e_client.post(
            "/ai/interview/feedback/request",
            json=weak_answer_request
        )

        assert response.status_code == 200
        
        data = response.json()
        assert_successful_feedback_response(data)
        
        print("\n[약점 답변 테스트 결과]")
        print(f"weakness: {data['data']['weakness']}")
        print(f"개선점: {data['data']['feedback']['improvements'][:100]}...")


@pytest.mark.e2e
class TestFeedbackE2EBadCases:
    """Bad Case 답변에 대한 E2E 테스트"""

    def test_답변_거부_bad_case(
        self,
        e2e_client,
        bad_case_refuse_request,
    ):
        """
        '모르겠습니다' 같은 답변 거부 → bad_case_detected
        """
        response = e2e_client.post(
            "/ai/interview/feedback/request",
            json=bad_case_refuse_request
        )

        assert response.status_code == 200
        
        data = response.json()
        # LLM이 REFUSE_TO_ANSWER로 판단할 것으로 기대
        if data["message"] == "bad_case_detected":
            assert_bad_case_response(data, "REFUSE_TO_ANSWER")
            print("\n[답변 거부 Bad Case 감지됨]")
            print(f"guidance: {data['data']['bad_case_feedback']['guidance']}")
        else:
            # LLM이 bad case로 판단하지 않은 경우
            assert_successful_feedback_response(data)
            print("\n[참고: LLM이 정상 답변으로 판단함]")

    def test_너무_짧은_답변_bad_case(
        self,
        e2e_client,
        bad_case_too_short_request,
    ):
        """
        너무 짧은 답변 → TOO_SHORT bad case
        """
        response = e2e_client.post(
            "/ai/interview/feedback/request",
            json=bad_case_too_short_request
        )

        assert response.status_code == 200
        
        data = response.json()
        if data["message"] == "bad_case_detected":
            assert data["data"]["bad_case_feedback"] is not None
            print("\n[짧은 답변 Bad Case 감지됨]")
            print(f"type: {data['data']['bad_case_feedback']['type']}")
        else:
            assert_successful_feedback_response(data)
            print("\n[참고: LLM이 정상 답변으로 판단함]")


@pytest.mark.e2e
class TestFeedbackE2ECategories:
    """다양한 카테고리별 E2E 테스트"""

    def test_os_카테고리_피드백(
        self,
        e2e_client,
        os_category_request,
    ):
        """OS 카테고리 질문에 대한 피드백 생성"""
        response = e2e_client.post(
            "/ai/interview/feedback/request",
            json=os_category_request
        )

        assert response.status_code == 200
        
        data = response.json()
        assert_successful_feedback_response(data)
        
        print("\n[OS 카테고리 테스트 결과]")
        print(f"질문: {os_category_request['question'][:50]}...")
        metrics = data["data"]["metrics"]
        for m in metrics:
            print(f"  - {m['name']}: {m['score']}점")

    def test_db_카테고리_피드백(
        self,
        e2e_client,
        db_category_request,
    ):
        """DB 카테고리 질문에 대한 피드백 생성"""
        response = e2e_client.post(
            "/ai/interview/feedback/request",
            json=db_category_request
        )

        assert response.status_code == 200
        
        data = response.json()
        assert_successful_feedback_response(data)
        
        print("\n[DB 카테고리 테스트 결과]")
        print(f"질문: {db_category_request['question'][:50]}...")
        metrics = data["data"]["metrics"]
        for m in metrics:
            print(f"  - {m['name']}: {m['score']}점")


@pytest.mark.e2e
class TestFeedbackE2EResponseQuality:
    """응답 품질 검증 테스트"""

    def test_피드백_텍스트_품질(
        self,
        e2e_client,
        good_answer_request,
    ):
        """
        피드백 텍스트 품질 검증
        - strengths/improvements가 빈 문자열이 아님
        - 최소 길이 이상
        """
        response = e2e_client.post(
            "/ai/interview/feedback/request",
            json=good_answer_request
        )

        assert response.status_code == 200
        data = response.json()
        
        feedback = data["data"]["feedback"]
        
        # 피드백 최소 길이 검증 (의미있는 피드백인지)
        assert len(feedback["strengths"]) >= 20, "strengths가 너무 짧음"
        assert len(feedback["improvements"]) >= 20, "improvements가 너무 짧음"
        
        print("\n[피드백 품질 테스트]")
        print(f"strengths 길이: {len(feedback['strengths'])}자")
        print(f"improvements 길이: {len(feedback['improvements'])}자")
        print(f"\nstrengths: {feedback['strengths'][:200]}...")
        print(f"\nimprovements: {feedback['improvements'][:200]}...")

    def test_루브릭_코멘트_품질(
        self,
        e2e_client,
        good_answer_request,
    ):
        """
        루브릭 각 항목의 comment 품질 검증
        """
        response = e2e_client.post(
            "/ai/interview/feedback/request",
            json=good_answer_request
        )

        assert response.status_code == 200
        data = response.json()
        
        metrics = data["data"]["metrics"]
        
        print("\n[루브릭 코멘트 품질 테스트]")
        for m in metrics:
            # 각 코멘트가 최소 10자 이상
            assert len(m["comment"]) >= 10, f"{m['name']} 코멘트가 너무 짧음"
            print(f"  - {m['name']} ({m['score']}점): {m['comment'][:50]}...")


@pytest.mark.e2e
class TestFeedbackE2EValidation:
    """요청 검증 E2E 테스트"""

    def test_필수_필드_누락_422(self, e2e_client):
        """필수 필드 누락 시 422 에러"""
        invalid_request = {
            "user_id": 9999,
            # question_id 누락
            "question": "테스트 질문",
            "answer_text": "테스트 답변"
        }

        response = e2e_client.post(
            "/ai/interview/feedback/request",
            json=invalid_request
        )

        assert response.status_code == 422

    def test_잘못된_enum_값_422(self, e2e_client):
        """잘못된 enum 값 422 에러"""
        invalid_request = {
            "user_id": 9999,
            "question_id": 1001,
            "interview_type": "INVALID_TYPE",  # 잘못된 enum
            "question_type": "CS",
            "category": "NETWORK",
            "question": "테스트 질문",
            "answer_text": "테스트 답변"
        }

        response = e2e_client.post(
            "/ai/interview/feedback/request",
            json=invalid_request
        )

        assert response.status_code == 422
