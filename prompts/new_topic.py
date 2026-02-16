# prompts/new_topic.py

"""새 토픽 질문 생성 프롬프트"""

from schemas.question import QuestionType

NEW_TOPIC_SYSTEM_PROMPT = {
    "gemini": """\
당신은 기술 면접 진행자입니다. 새로운 토픽에 대한 메인 질문을 생성해야 합니다.

## 질문 생성 원칙

### 질문 유형별 가이드

#### CS 기본 지식
- 운영체제, 네트워크, 데이터베이스, 자료구조, 알고리즘, 컴퓨터 아키텍처 등 핵심 개념
- 이론적 이해와 실무 적용 능력을 함께 평가
- 면접에서 자주 나오는 중요 개념 위주

#### 시스템 설계
- 확장성, 가용성, 성능을 고려한 설계 능력 평가
- 트레이드오프를 이해하고 설명하는 능력
- 실제 서비스 사례를 활용한 질문

#### 포트폴리오
- 지원자의 프로젝트 경험을 기반으로 질문
- 기술 선택 이유, 문제 해결 과정, 성과를 중심으로
- 프로젝트에서 사용한 기술의 깊이 있는 이해 확인

### 좋은 메인 질문의 특징
- 명확하고 구체적
- 다양한 깊이의 답변이 가능
- 꼬리질문으로 확장 가능
- 실무 연관성이 높음

### 피해야 할 질문
- 이미 다룬 토픽과 중복되는 질문
- 너무 쉽거나 너무 어려운 질문
- 단순 정의만 묻는 질문

### 출력 형식
- question_text: 생성된 메인 질문
- topic_summary: 토픽 요약 (한 줄)
""",
    "vllm": """\
당신은 기술 면접 진행자입니다. 새로운 토픽에 대한 메인 질문을 생성해야 합니다.

## 질문 생성 원칙

### 질문 유형별 가이드

#### CS 기본 지식
- 운영체제, 네트워크, 데이터베이스, 자료구조, 알고리즘, 컴퓨터 아키텍처 등 핵심 개념
- 이론적 이해와 실무 적용 능력을 함께 평가
- 면접에서 자주 나오는 중요 개념 위주

#### 시스템 설계
- 확장성, 가용성, 성능을 고려한 설계 능력 평가
- 트레이드오프를 이해하고 설명하는 능력
- 실제 서비스 사례를 활용한 질문

#### 포트폴리오
- 지원자의 프로젝트 경험을 기반으로 질문
- 기술 선택 이유, 문제 해결 과정, 성과를 중심으로
- 프로젝트에서 사용한 기술의 깊이 있는 이해 확인

### 좋은 메인 질문의 특징
- 명확하고 구체적
- 다양한 깊이의 답변이 가능
- 꼬리질문으로 확장 가능
- 실무 연관성이 높음

### 피해야 할 질문
- 이미 다룬 토픽과 중복되는 질문
- 너무 쉽거나 너무 어려운 질문
- 단순 정의만 묻는 질문

### 출력 형식
- question_text: 생성된 메인 질문
- topic_summary: 토픽 요약 (한 줄)
""",
}


def get_new_topic_system_prompt(provider: str) -> str:
    """Provider에 맞는 시스템 프롬프트 반환"""
    return NEW_TOPIC_SYSTEM_PROMPT.get(provider, NEW_TOPIC_SYSTEM_PROMPT["gemini"])


def build_new_topic_prompt(
    question_type: QuestionType,
    category: str | None,
    interview_history: list,
    portfolio=None,
) -> str:
    """새 토픽 질문 생성용 프롬프트 생성"""
    
    covered_topics = _format_covered_topics(interview_history)
    portfolio_info = _format_portfolio_info(portfolio)
    additional_instruction = _get_additional_instruction(question_type, portfolio)
    
    return f"""\
## 면접 설정
- 질문 유형: {question_type.value if hasattr(question_type, 'value') else question_type}
- 카테고리: {category or "일반"}

## 이미 다룬 토픽 질문들
{covered_topics}

## 포트폴리오 정보
{portfolio_info}

## 지시사항
아직 다루지 않은 새로운 토픽에 대한 메인 질문을 생성하세요.
{additional_instruction}
"""


def _format_covered_topics(history: list) -> str:
    """이미 다룬 토픽들을 요약"""
    if not history:
        return "(없음)"
    
    topics = {}
    for turn in history:
        if turn.topic_id not in topics:
            topics[turn.topic_id] = turn.question
    
    return "\n".join(
        f"- Topic {tid}: {q}" for tid, q in topics.items()
    )


def _format_portfolio_info(portfolio) -> str:
    """포트폴리오 정보를 문자열로 포매팅"""
    if not portfolio or not portfolio.projects:
        return "(포트폴리오 정보 없음)"
    
    formatted = []
    for proj in portfolio.projects:
        lines = [f"### {proj.project_name}"]
        if proj.tech_stack:
            lines.append(f"- 기술 스택: {', '.join(proj.tech_stack)}")
        if proj.problem_solved:
            lines.append(f"- 해결한 문제: {proj.problem_solved}")
        if proj.achievements:
            lines.append(f"- 성과: {proj.achievements}")
        if proj.role:
            lines.append(f"- 역할: {proj.role}")
        formatted.append("\n".join(lines))
    
    return "\n\n".join(formatted)


def _get_additional_instruction(question_type: QuestionType, portfolio) -> str:
    """질문 유형별 추가 지시사항"""
    
    if question_type == QuestionType.CS:
        return (
            "운영체제, 네트워크, 데이터베이스, 자료구조, 알고리즘 중 "
            "아직 다루지 않은 영역에서 질문을 생성하세요."
        )
    
    elif question_type == QuestionType.SYSTEM_DESIGN:
        return (
            "확장성, 가용성, 데이터 일관성, 캐싱, 로드밸런싱 등 "
            "시스템 설계의 핵심 개념을 다루는 질문을 생성하세요."
        )
    
    elif question_type == QuestionType.PORTFOLIO:
        if portfolio and portfolio.projects:
            project_names = [p.project_name for p in portfolio.projects]
            return (
                f"포트폴리오 프로젝트({', '.join(project_names)}) 중 "
                "아직 다루지 않은 프로젝트나 기술에 대해 질문하세요."
            )
    
    return ""