# # services/feedback_service.py

# services/feedback_service.py

from schemas.feedback import (
    FeedbackRequest,
    FeedbackResponse,
    FeedbackData,
    FeedbackContent,
    AnswerAnalyzerResult,
    RubricEvaluationResult,
    BadCaseFeedback
)
from providers.llm.gemini import GeminiProvider
from services.answer_analyzer import AnswerAnalyzerService
from prompts.feedback import build_feedback_prompt, FEEDBACK_SYSTEM_PROMPT
from prompts.rubric import  build_rubric_prompt, RUBRIC_SYSTEM_PROMPT


class FeedbackService:
    """피드백 생성 서비스"""

    def __init__(
        self,
        llm_provider: GeminiProvider | None = None,
        analyzer: AnswerAnalyzerService | None = None,
    ):
        self.llm = llm_provider or GeminiProvider()
        self.analyzer = analyzer or AnswerAnalyzerService(llm_provider=self.llm)
    
    async def generate_feedback(
        self,
        request: FeedbackRequest,
        analysis: AnswerAnalyzerResult | None = None,
    ) -> FeedbackResponse:
        """
        피드백 생성 파이프라인
        
        Args:
            request: 피드백 요청
            analysis: 이미 수행된 답변 분석 결과 (없으면 새로 분석)
        """
        print("\n=== 피드백 생성 시작 ===")
        print(f"[요청 정보] category: {request.category}, question: {request.question[:50]}...")
        
        # Step 1: 답변 분석 (전달받지 않은 경우에만 수행)
        try:
            if analysis is None:
                print("[Step 1] 답변 분석 시작...")
                analysis = await self.analyzer.analyze(request)
                print(f"[Step 1] 답변 분석 완료 - is_bad_case: {analysis}")
            else:
                print("[Step 1] 기존 분석 결과 사용")
        except Exception as e:
            print(f"[Step 1 ERROR] 답변 분석 실패: {type(e).__name__}: {str(e)}")
            raise
        
        # Bad Case인 경우 조기 반환
        if analysis.is_bad_case:
            print(f"[조기 반환] Bad case 감지 - type: {analysis.bad_case_type}")
            return self._build_bad_case_response(request,analysis)
        
        # Step 2: 루브릭 평가
        try:
            print("[Step 2] 루브릭 평가 시작...")
            rubric_result = await self._evaluate_rubrics(request)
            print(f"[Step 2] 루브릭 평가 완료 - {rubric_result}")
        except Exception as e:
            print(f"[Step 2 ERROR] 루브릭 평가 실패: {type(e).__name__}: {str(e)}")
            raise
        
        # Step 3: 피드백 텍스트 생성
        try:
            print("[Step 3] 피드백 텍스트 생성 시작...")
            feedback_content = await self._generate_feedback_content(
                request=request,
                rubric_result=rubric_result,
            )
            print(f"[Step 3] 피드백 텍스트 생성 완료")
        except Exception as e:
            print(f"[Step 3 ERROR] 피드백 텍스트 생성 실패: {type(e).__name__}: {str(e)}")
            raise
        
        print("[최종 응답 생성] 성공")
        print("=== 피드백 생성 완료 ===\n")
        
        return FeedbackResponse(
            message="success",
            data=FeedbackData(
                user_id=request.user_id,
                question_id=request.question_id,
                metrics=rubric_result.to_metrics_list(),
                bad_case=None,
                weakness=analysis.has_weakness,
                feedback=feedback_content,
            )
        )
    
    def _build_bad_case_response(self, request: FeedbackRequest, analysis: AnswerAnalyzerResult) -> FeedbackResponse:
        """Bad Case 응답 생성 - 미리 정의된 메시지 사용"""
        return FeedbackResponse(
            message="bad_case_detected",
            data=FeedbackData(
                user_id=request.user_id,
                question_id=request.question_id,

                bad_case_feedback=BadCaseFeedback.from_type(analysis.bad_case_type),
                # 정상 응답 필드는 None
                metrics=None,
                weakness=None,
                feedback=None
            )
        )
        
    async def _evaluate_rubrics(self, request: FeedbackRequest) -> RubricEvaluationResult:
        """루브릭 기반 평가"""
        print(f"[루브릭 평가] LLM 호출 준비 - category: {request.category.value}")
    

        print(f"[루브릭 평가] LLM generate_structured 호출 중...")
        result = await self.llm.generate_structured(
            prompt=build_rubric_prompt(
                question_type=request.question_type.value,
                category=request.category.value,
                question=request.question,
                answer=request.answer_text,
            ),
            response_model=RubricEvaluationResult,
            system_prompt=RUBRIC_SYSTEM_PROMPT,
            temperature=0.0,
            max_tokens=4000
        )
        print(f"[루브릭 평가] LLM 응답 수신 완료")
        return result
    
    async def _generate_feedback_content(
        self,
        request: FeedbackRequest,
        rubric_result: RubricEvaluationResult,
    ) -> FeedbackContent:
        """피드백 텍스트 생성"""
        print(f"[피드백 생성] LLM 호출 준비")

        print(f"[피드백 생성] LLM generate_structured 호출 중...")
        result = await self.llm.generate_structured(
            prompt=build_feedback_prompt(
                question_type=request.question_type.value,
                category=request.category.value,
                question=request.question,
                answer=request.answer_text,
                rubric_result=rubric_result,
            ),
            response_model=FeedbackContent,
            system_prompt=FEEDBACK_SYSTEM_PROMPT,
            temperature=0.3,
            max_tokens=4000,
        )
        print(result)
        print(f"[피드백 생성] LLM 응답 수신 완료")
        return result


# 싱글톤 인스턴스
feedback_service = FeedbackService()
