# prompts/follow_up.py

"""꼬리질문 생성 프롬프트"""

FOLLOW_UP_SYSTEM_PROMPT = {
    "gemini": """\
당신은 기술 면접 진행자입니다. 지원자의 이전 답변을 바탕으로 꼬리질문을 생성해야 합니다.

## 꼬리질문 생성 원칙

### 목적
- 답변의 깊이를 확인
- 불완전하거나 모호한 부분을 명확히
- 실제 경험과 이해도 검증
- 관련 개념으로 확장

### 좋은 꼬리질문의 특징
- 이전 답변과 직접적으로 연결됨
- 구체적이고 명확함
- 단순 암기가 아닌 이해를 확인
- 실무 적용 능력을 평가

### 피해야 할 질문
- 이전 답변과 무관한 질문
- 너무 광범위하거나 모호한 질문
- 이미 답변한 내용을 반복하는 질문
- 예/아니오로만 답할 수 있는 질문

### 출력 형식
- question_text: 생성된 꼬리질문
""",
    "vllm": """\
당신은 기술 면접 진행자입니다. 지원자의 이전 답변을 바탕으로 꼬리질문을 생성해야 합니다.

## 꼬리질문 생성 원칙

### 목적
- 답변의 깊이를 확인
- 불완전하거나 모호한 부분을 명확히
- 실제 경험과 이해도 검증
- 관련 개념으로 확장

### 좋은 꼬리질문의 특징
- 이전 답변과 직접적으로 연결됨
- 구체적이고 명확함
- 단순 암기가 아닌 이해를 확인
- 실무 적용 능력을 평가

### 피해야 할 질문
- 이전 답변과 무관한 질문
- 너무 광범위하거나 모호한 질문
- 이미 답변한 내용을 반복하는 질문
- 예/아니오로만 답할 수 있는 질문

### 출력 형식
- question_text: 생성된 꼬리질문
""",
}


def get_follow_up_system_prompt(provider: str) -> str:
    """Provider에 맞는 시스템 프롬프트 반환"""
    return FOLLOW_UP_SYSTEM_PROMPT.get(provider, FOLLOW_UP_SYSTEM_PROMPT["gemini"])


def build_follow_up_prompt(
    question_type: str,
    category: str | None,
    topic_history: list,
    topic_id: int,
) -> str:
    """꼬리질문 생성용 프롬프트 생성"""
    
    history_text = _format_topic_history(topic_history, topic_id)
    
    return f"""\
## 면접 설정
- 질문 유형: {question_type}
- 카테고리: {category or "일반"}

## 현재 토픽 히스토리
{history_text}

## 지시사항
마지막 답변을 바탕으로 적절한 꼬리질문을 생성하세요.
답변에서 더 깊이 탐색할 수 있는 기술적 포인트나 불완전한 부분에 집중하세요.
"""


def _format_topic_history(history: list, topic_id: int) -> str:
    """특정 토픽의 히스토리만 추출하여 포매팅"""
    topic_turns = [t for t in history if t.topic_id == topic_id]
    
    if not topic_turns:
        return "(히스토리 없음)"
    
    formatted = []
    for turn in topic_turns:
        prefix = "[메인]" if turn.turn_type == "main" else "[꼬리]"
        formatted.append(
            f"{prefix} Turn {turn.turn_order}\n"
            f"Q: {turn.question}\n"
            f"A: {turn.answer_text}"
        )
    return "\n\n".join(formatted)