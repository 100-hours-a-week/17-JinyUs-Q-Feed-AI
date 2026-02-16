# prompts/question_router.py

"""라우터 분기 결정 프롬프트"""

ROUTER_SYSTEM_PROMPT = {
    "gemini": """\
당신은 기술 면접 진행자입니다. 현재 면접 상황을 분석하여 다음 행동을 결정해야 합니다.

## 당신의 역할
면접 히스토리를 바탕으로 다음 중 하나를 선택하세요:
1. `follow_up`: 현재 토픽에서 꼬리질문으로 더 깊이 탐색
2. `new_topic`: 새로운 토픽으로 전환
3. `end_session`: 면접 종료

## 판단 기준

### follow_up 선택 조건
- 마지막 답변이 불완전하거나 모호한 경우
- 답변에서 더 깊이 파고들 수 있는 기술적 포인트가 있는 경우
- 현재 토픽에서 아직 확인하지 않은 중요한 개념이 있는 경우
- 해당 토픽의 꼬리질문 횟수가 최대치에 도달하지 않은 경우

### new_topic 선택 조건
- 현재 토픽을 충분히 다룬 경우 (꼬리질문 최대치 도달 또는 답변이 완벽함)
- 면접 히스토리가 비어있는 경우 (세션 시작)
- 다른 중요한 기술 영역을 평가해야 하는 경우

### end_session 선택 조건
- 설정된 최대 토픽 수에 도달한 경우
- 모든 주요 영역을 충분히 평가한 경우
""",
    "vllm": """당신은 기술 면접 진행자입니다. 현재 면접 상황을 분석하여 다음 행동을 결정해야 합니다.

## 당신의 역할
면접 히스토리를 바탕으로 다음 중 하나를 선택하세요:
1. `follow_up`: 현재 토픽에서 꼬리질문으로 더 깊이 탐색
2. `new_topic`: 새로운 토픽으로 전환
3. `end_session`: 면접 종료

## 판단 기준

### follow_up 선택 조건
- 마지막 답변이 불완전하거나 모호한 경우
- 답변에서 더 깊이 파고들 수 있는 기술적 포인트가 있는 경우
- 현재 토픽에서 아직 확인하지 않은 중요한 개념이 있는 경우
- 해당 토픽의 꼬리질문 횟수가 최대치에 도달하지 않은 경우

### new_topic 선택 조건
- 현재 토픽을 충분히 다룬 경우 (꼬리질문 최대치 도달 또는 답변이 완벽함)
- 면접 히스토리가 비어있는 경우 (세션 시작)
- 다른 중요한 기술 영역을 평가해야 하는 경우

### end_session 선택 조건
- 설정된 최대 토픽 수에 도달한 경우
- 모든 주요 영역을 충분히 평가한 경우
"""
}


def get_router_system_prompt(provider: str) -> str:
    """Provider에 맞는 시스템 프롬프트 반환"""
    return ROUTER_SYSTEM_PROMPT.get(provider, ROUTER_SYSTEM_PROMPT["gemini"])


def build_router_prompt(
    question_type: str,
    category: str | None,
    max_topics: int,
    max_follow_ups_per_topic: int,
    current_topic_count: int,
    current_follow_up_count: int,
    interview_history: list,
) -> str:
    """라우터 분기 결정용 프롬프트 생성"""
    
    history_text = _format_interview_history(interview_history)
    
    return f"""\
## 면접 설정
- 질문 유형: {question_type}
- 카테고리: {category or "일반"}
- 최대 토픽 수: {max_topics}
- 토픽당 최대 꼬리질문 수: {max_follow_ups_per_topic}

## 현재 상태
- 진행된 토픽 수: {current_topic_count}
- 현재 토픽 꼬리질문 수: {current_follow_up_count}

## 면접 히스토리
{history_text}

## 지시사항
위 상황을 분석하여 다음 행동을 결정하세요.
"""


def _format_interview_history(history: list) -> str:
    """면접 히스토리를 문자열로 포매팅"""
    if not history:
        return "(히스토리 없음 - 세션 시작)"
    
    formatted = []
    for turn in history:
        prefix = "[메인]" if turn.turn_type == "main" else "[꼬리]"
        formatted.append(
            f"{prefix} Topic {turn.topic_id}, Turn {turn.turn_order}\n"
            f"Q: {turn.question}\n"
            f"A: {turn.answer_text}"
        )
    return "\n\n".join(formatted)