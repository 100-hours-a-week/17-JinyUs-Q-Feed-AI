# graphs/nodes/follow_up_generator.py

"""꼬리질문 생성 노드"""

from langsmith import traceable

from schemas.question import QuestionOutput, GeneratedQuestion
from prompts.follow_up import get_follow_up_system_prompt, build_follow_up_prompt
from graphs.question.state import QuestionState
from core.dependencies import get_llm_provider
from core.logging import get_logger

logger = get_logger(__name__)


@traceable(run_type="chain", name="follow_up_generator")
async def follow_up_generator(state: QuestionState) -> dict:
    """꼬리질문 생성 노드"""
    
    current_topic_id = state.get("current_topic_id", 0)
    current_follow_up_count = state.get("current_follow_up_count", 0)
    
    logger.debug(f"꼬리질문 생성 시작 | topic_id={current_topic_id}")
    
    question_output = await _generate_follow_up_llm(state, current_topic_id)
    
    generated_question = GeneratedQuestion(
        user_id = state.get("user_id"),
        session_id = state.get("session_id"),
        question_text=question_output.question_text,
        topic_id=current_topic_id,
        turn_type="follow_up",
        is_session_ended=False,
        end_reason=None,
        is_bad_case=False,
        bad_case_feedback=None,
    )
    
    logger.info(
        f"꼬리질문 생성 완료 | topic_id={current_topic_id}",
        extra={
            "user_id": state.get("user_id"),
            "session_id": state.get("session_id"),
            "topic_id": current_topic_id,
            "question_preview": question_output.question_text[:50],
        }
    )
    
    return {
        "generated_question": generated_question,
        "current_follow_up_count": current_follow_up_count + 1,
    }


@traceable(run_type="llm", name="follow_up_llm")
async def _generate_follow_up_llm(
    state: QuestionState,
    topic_id: int,
) -> QuestionOutput:
    """LLM 호출하여 꼬리질문 생성"""
    
    llm = get_llm_provider()
    
    system_prompt = get_follow_up_system_prompt(llm.provider_name)
    user_prompt = build_follow_up_prompt(
        question_type=state.get("question_type", "CS"),
        category=state.get("category"),
        topic_history=state.get("interview_history", []),
        topic_id=topic_id,
    )
    
    question_output = await llm.generate_structured(
        prompt=user_prompt,
        response_model=QuestionOutput,
        system_prompt=system_prompt,
        temperature=0.7,
    )
    
    
    return question_output
        