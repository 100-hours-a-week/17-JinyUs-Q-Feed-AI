# prompts/feedback_practice.py

"""
연습모드 피드백 생성 프롬프트

연습모드 전용. 단일 Q&A에 대한 종합 피드백을 생성.
질문 유형별(CS) 특화 프롬프트.
시스템디자인은 현재 미지원.
"""

from collections import defaultdict

from schemas.feedback_v2 import QuestionType, QuestionCategory, KeywordCheckResult
from schemas.feedback_v2 import RouterAnalysisTurn


# ============================================================
# System Prompt
# ============================================================

def get_practice_feedback_system_prompt(question_type: QuestionType) -> str:
    if question_type == QuestionType.CS:
        return CS_PRACTICE_FEEDBACK_SYSTEM_PROMPT
    # fallback
    return CS_PRACTICE_FEEDBACK_SYSTEM_PROMPT


CS_PRACTICE_FEEDBACK_SYSTEM_PROMPT = """\
당신은 CS 기초 기술면접의 피드백을 작성하는 시니어 면접관입니다.
지원자의 단일 답변을 분석하여 종합 피드백을 작성합니다.

아래에 제공된 키워드 체크 결과와 답변 분석 결과를 우선 근거로 활용하세요.
원문 Q&A와 충돌하는 경우에는 원문 Q&A를 우선합니다.

## 작성 원칙

### 톤
- 면접관이 지원자에게 직접 1:1로 조언하는 2인칭 대화체를 사용하세요.
- "~해 주신 점이 좋습니다", "~를 보완해 보시길 권장합니다"
- 감정적 수식어(대단합니다, 훌륭합니다, 인상적입니다) 금지
- 관찰자/3인칭 시점(지원자는 ~를 보여주었습니다) 금지

**[중요] 리스트 형식 지정:**
- 모든 항목은 반드시 **검은 동그라미 기호(●)**로 시작해야 합니다.
- 하이픈(-), 별표(*), 숫자(1.) 등 다른 기호는 절대 사용하지 마십시오.

### 강점 (strengths) 작성 기준
막연한 칭찬이 아닌, 구체적인 채점 포인트를 명시하세요:
- 핵심 개념을 정확하게 설명한 부분
- 본인의 언어로 원리를 명확히 이해하고 있는 부분
- 논리적 흐름과 구조(두괄식, 비교/대조)를 효과적으로 사용한 부분
- 실무 환경이나 장애 상황과 연결한 통찰

### 개선할 점 (improvements) 작성 우선순위
가장 시급한 순서대로 작성하세요:
1. **치명적 오개념**: 기술적으로 완전히 틀린 개념이 있다면 가장 먼저 교정
2. **핵심 논리 누락**: 개념은 맞으나 "왜 그런지(Why)", 시간/공간 복잡도, 트레이드오프가 빠진 경우
3. **전문 용어 정제**: 구어체나 모호한 비유를 정확한 기술 용어로 업그레이드
4. **심화 지식**: 1-3이 모두 충족된 경우에만, 해당 주제에 고유한 심화 포인트 제시

상위 문제(1-2)가 있는데 4를 포함하지 마세요.
우선순위 라벨(1순위, [오개념 수정] 등)은 출력에 포함하지 마세요. 자연스럽게 서술하세요.

## CS 피드백 평가 축
다음 5가지 관점에서 답변을 평가하세요:
- **정확성**: 개념 설명에 사실적 오류가 없는가
- **완성도**: 반드시 언급해야 할 핵심 개념이 빠지지 않았는가
- **논리적 추론**: "왜 그런지"를 설명할 수 있는가, 원리를 이해하고 있는가
- **깊이**: 정의만 나열하지 않고 동작 원리, 내부 구현까지 설명하는가
- **전달력**: 논리적 순서로 구조화하여 명확하게 전달하는가

## 제약 사항
- strengths: 150자 이상 800자 이하
- improvements: 150자 이상 800자 이하
- 리스트는 ● 기호 사용 (하이픈, 별표, 숫자 금지)
- 한국어 경어체(합니다/습니다), 2인칭 대화형
- 전문 용어는 원어를 병기 (예: 컨텍스트 스위칭(Context Switching))"""


# ============================================================
# User Prompt Builder
# ============================================================

def build_practice_feedback_prompt(
    question_type: QuestionType,
    category: QuestionCategory | None,
    grouped_interview: dict[int, dict],
    keyword_result: KeywordCheckResult | None = None,
    router_analyses: list[RouterAnalysisTurn] | None = None,
) -> str:
    """연습모드 피드백 user prompt 생성

    단일 토픽의 Q&A를 기반으로 피드백을 요청.
    """

    topic_data = list(grouped_interview.values())[0]
    category_str = _format_category(category or topic_data.get("category"))

    return f"""\
## 질문 정보
- 질문 유형: {question_type.value}
- 카테고리: {category_str}

## 키워드 체크
{_format_keyword_result(keyword_result)}

## 답변 분석 결과
{_format_router_analyses(router_analyses)}

## 면접 Q&A
{topic_data["qa_text"]}

위 답변을 분석하여 강점과 개선할 점을 작성하세요."""


def _format_category(category: QuestionCategory | None) -> str:
    if category is None:
        return "N/A"
    return category.value if hasattr(category, "value") else str(category)


def _format_keyword_result(keyword_result: KeywordCheckResult | None) -> str:
    if keyword_result is None:
        return "키워드 체크 결과 없음"

    covered = ", ".join(keyword_result.covered_keywords) or "없음"
    missing = ", ".join(keyword_result.missing_keywords) or "없음"
    coverage = round(keyword_result.coverage_ratio * 100)

    return (
        f"- 커버리지: {coverage}%\n"
        f"- 포함 키워드: {covered}\n"
        f"- 누락 키워드: {missing}"
    )


def _format_router_analyses(
    router_analyses: list[RouterAnalysisTurn] | None,
) -> str:
    if not router_analyses:
        return "답변 분석 결과 없음"

    by_topic: dict[int, list[RouterAnalysisTurn]] = defaultdict(list)
    for analysis in router_analyses:
        by_topic[analysis.topic_id].append(analysis)

    sections = []
    for topic_id, analyses in sorted(by_topic.items()):
        turn_lines = []
        for analysis in sorted(analyses, key=lambda item: item.turn_order):
            details = []

            if analysis.correctness_detail:
                details.append(f"정확성: {analysis.correctness_detail}")
            if analysis.completeness_cs_detail:
                details.append(f"완성도: {analysis.completeness_cs_detail}")
            if analysis.completeness_detail:
                details.append(f"완성도: {analysis.completeness_detail}")
            if analysis.depth_detail:
                details.append(f"깊이: {analysis.depth_detail}")

            flags = []
            if analysis.has_error is not None:
                flags.append(f"오류={'있음' if analysis.has_error else '없음'}")
            if analysis.has_missing_concepts is not None:
                flags.append(f"핵심개념누락={'있음' if analysis.has_missing_concepts else '없음'}")
            if analysis.is_superficial is not None:
                flags.append(f"표면적={'예' if analysis.is_superficial else '아니오'}")
            if analysis.has_evidence is not None:
                flags.append(f"근거={'있음' if analysis.has_evidence else '없음'}")
            if analysis.has_tradeoff is not None:
                flags.append(f"트레이드오프={'있음' if analysis.has_tradeoff else '없음'}")
            if analysis.has_problem_solving is not None:
                flags.append(f"문제해결={'있음' if analysis.has_problem_solving else '없음'}")
            if analysis.is_well_structured is not None:
                flags.append(f"구조화={'예' if analysis.is_well_structured else '아니오'}")
            if analysis.follow_up_direction:
                flags.append(f"꼬리질문방향={analysis.follow_up_direction}")

            line_parts = [part for part in [", ".join(details), ", ".join(flags)] if part]
            turn_label = "메인" if analysis.turn_type == "new_topic" else "꼬리"
            turn_lines.append(
                f"- {turn_label} 턴 {analysis.turn_order}: " + " | ".join(line_parts)
            )

        sections.append(f"토픽 {topic_id}\n" + "\n".join(turn_lines))

    return "\n\n".join(sections)
