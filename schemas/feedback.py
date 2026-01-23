from pydantic import BaseModel, Field
from enum import Enum
from schemas.common import BaseResponse

class InterviewType(str, Enum):
    PRACTICE_INTERVIEW = "PRACTICE_INTERVIEW"
    REAL_INTERVIEW = "REAL_INTERVIEW"

class QuestionType(str, Enum):
    CS = "CS"
    SYSTEM_DESIGN = "SYSTEM_DESIGN"
    PORTFOLIO = "PORTFOLIO"

class QuestionCategory(str, Enum):
    OS = "OS"
    NETWORK = "NETWORK"
    DB = "DB"
    ALGORITHM_DATA_STRUCTURE = "ALGORITHM/DATA_STRUCTURE"
    COMPUTER_STRUCTURE = "COMPUTER_STRUCTURE"

    #----------------------------- 시스템 디자인 카테고리 ----------------------------#
    NOTIFICATION_ENGAGEMENT = "NOTIFICATION/ENGAGEMENT"
    MESSAGING_REALTIME_COMMUNICATION = "MESSAGING/REALTIME_COMMUNICATION"
    SEARHCH_DELIVERY = "SEARCH/DELIVERY"
    MEDIA_STREAMING_PROCESSING = "MEDIA_STREAMING_PROCESSING"
    STORAGE_FILE_COLLABORATION = "STORAGE/FILE_COLLABORATION"
    WEB_PLATRORM_INFRASTRUCTURE = "WEB_PLATFORM_INFRSTRUCTURE"
    LOCATION_MAKETPLACE_TRANSACTION = "LOCATION/MARKETPLACE/TRANSACTION"


class BadCaseType(str, Enum):
    '''Bad Case 유형'''
    REFUSE_TO_ANSWER = "REFUSE_TO_ANSWER"  # 답변 거부
    TOO_SHORT = "TOO_SHORT"   # 너무 짧은 답변
    INAPPROPRIATE = "INAPPROPRIATE"        # 부적절한 내용            

class BadCaseFeedback(BaseModel):
    """Bad Case 전용 피드백"""
    message: str  # "답변이 너무 짧습니다"
    guidance: str  # "더 자세하게 설명해주세요..."    

BAD_CASE_MESSAGES = {
    BadCaseType.REFUSE_TO_ANSWER: {
        "message": "답변이 감지되지 않았습니다.",
        "guidance": "질문에 대한 답변을 입력해주세요. 음성이 제대로 녹음되지 않았다면 다시 시도해주세요."
    },
    BadCaseType.TOO_SHORT: {
        "message": "답변이 너무 짧습니다.",
        "guidance": "면접관이 이해할 수 있도록 더 자세하게 설명해주세요. 구체적인 예시나 근거를 포함하면 좋습니다."
    },
    BadCaseType.INAPPROPRIATE: {
        "message": "부적절한 답변이 감지되었습니다.",
        "guidance": "질문과 관련된 기술적인 내용으로 답변해주세요."
    }
}

class BadCaseFeedback(BaseModel):
    """Bad Case 전용 피드백"""
    type: BadCaseType = Field(..., description="Bad case 유형")
    message: str = Field(..., description="Bad case 메시지")
    guidance: str = Field(..., description="재답변 가이드")
    
    @classmethod
    def from_type(cls, bad_case_type: BadCaseType) -> "BadCaseFeedback":
        """Bad case 타입으로부터 피드백 생성"""
        info = BAD_CASE_MESSAGES[bad_case_type]
        return cls(
            type=bad_case_type,
            message=info["message"],
            guidance=info["guidance"]
        )

class AnalyzerMessageType(str, Enum):
    """V2 Answer Analyzer 응답 메시지 타입"""
    BADCASE_REFUSE = "BADCASE_REFUSE"
    BADCASE_TOO_SHORT = "BADCASE_TOO_SHORT"
    NORMAL_ANSWER = "NORMAL_ANSWER"
    PRACTICE_MODE_FEEDBACK = "practice_mode_feedback_generate"


class AnswerAnalyzerResult(BaseModel):
    '''answer analyzer 출력 스키마'''
    is_bad_case : bool
    bad_case_type : BadCaseType | None = None
    short_advice : str = Field(..., description="짧은 조언 (1문장)")

    # 정상 답변인 경우의 분석 
    # 1. 취약하게 답변한 질문인지 아닌지 일단 boolean 
    has_weakness: bool = Field(default=False, description="보완이 필요한 약점 존재 여부")

    # V2 꼬리질문 판단용
    needs_followup: bool = Field(default=False, description="꼬리질문 필요 여부")
    followup_reason: str | None = Field(None, description="꼬리질문 필요 사유")


class FeedbackRequest(BaseModel):
    user_id: int = Field(..., description="사용자 ID")
    question_id: int = Field(..., description="문제 ID")
    interview_type : InterviewType = Field(
        default=InterviewType.PRACTICE_INTERVIEW,
        description="면접 유형"
    )
    question_type: QuestionType = Field(
        default=QuestionType.CS,
        description="질문 유형"
    )
    category: QuestionCategory | None = Field(None, description="문제 카테고리")
    question: str = Field(..., description="문제 질문 텍스트")
    answer_text: str = Field(..., description="사용자의 답변 텍스트")

class RubricScore(BaseModel):
    '''개별 루브릭 항목 점수'''
    name : str
    score: int = Field(..., description="루브릭 점수 (1-5)")
    comment: str = Field(..., description="점수 부여 근거")

class RubricEvaluationResult(BaseModel):
    """Rubric Evaluator 내부 출력 - LLM structured output"""
    accuracy: int = Field(..., ge=1, le=5, description="정확도")
    logic: int = Field(..., ge=1, le=5, description="논리력")
    specificity: int = Field(..., ge=1, le=5, description="구체성")
    completeness: int = Field(..., ge=1, le=5, description="완성도")
    delivery: int = Field(..., ge=1, le=5, description="전달력")
    
    # 내부용 근거 (피드백 생성에 활용)
    accuracy_rationale: str = ""
    logic_rationale: str = ""
    specificity_rationale: str = ""
    completeness_rationale: str = ""
    delivery_rationale: str = ""
    
    def to_metrics_list(self) -> list[RubricScore]:
        """API 응답용 metrics 리스트로 변환"""
        return [
            RubricScore(name="정확도", score=self.accuracy, comment=self.accuracy_rationale),
            RubricScore(name="논리력", score=self.logic, comment=self.logic_rationale),
            RubricScore(name="구체성", score=self.specificity, comment=self.specificity_rationale),
            RubricScore(name="완성도", score=self.completeness, comment=self.completeness_rationale),
            RubricScore(name="전달력", score=self.delivery, comment=self.delivery_rationale),
        ]
    

# Response schema
class FeedbackContent(BaseModel):
    """피드백 텍스트 내용"""
    strengths: str = Field(..., description="잘한 점")
    improvements: str = Field(..., description="개선할 점")


class FeedbackData(BaseModel):
    """V1 피드백 응답 데이터"""
    user_id : int
    question_id : int

    # Bad case 응답 (bad_case일 때만 사용)
    bad_case_feedback: BadCaseFeedback | None = None
    
    # 정상 응답 (bad_case가 아닐 때만 사용)
    metrics: list[RubricScore] | None = None
    weakness: bool | None = None
    feedback: FeedbackContent | None = None


class FeedbackResponse(BaseResponse):
    """V1 동기 피드백 응답 - AI 서버 → Java 백엔드"""
    data: FeedbackData | None = None

class FeedbackResult(BaseModel):
    '''최종 피드백 결과 - 백엔드 Callback 전송용'''
    user_id : int
    question_id : int

    #루브릭 평가 점수
    metrics : RubricEvaluationResult
    

# ============================================================
# V2 Schemas
# ============================================================

class AnalyzerResponseData(BaseModel):
    """V2 Answer Analyzer 중간 응답 데이터"""
    bad_case: BadCaseType | None = None
    weakness: bool | None = None
    tail_question: bool | None = None
    short_advice: str | None = None


class AnalyzerResponse(BaseResponse):
    """V2 중간 응답 - AI 서버 → Java 백엔드"""
    message: AnalyzerMessageType
    data: AnalyzerResponseData | None = None


class FeedbackCallbackPayload(BaseModel):
    """V2 Callback 페이로드 - AI 서버 → Java 백엔드"""
    user_id: int
    question_id: int
    metrics: list[RubricScore]
    bad_case: BadCaseType | None = None
    feedback: FeedbackContent | None = None
    