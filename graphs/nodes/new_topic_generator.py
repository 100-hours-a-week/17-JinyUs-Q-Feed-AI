# graphs/nodes/new_topic_generator.py

"""새 토픽 질문 생성 노드"""

from langsmith import traceable

from schemas.question import QuestionOutput, GeneratedQuestion, QuestionType
from prompts.new_topic import get_new_topic_system_prompt, build_new_topic_prompt
from graphs.question.state import QuestionState
from core.dependencies import get_llm_provider
from core.logging import get_logger

logger = get_logger(__name__)


@traceable(run_type="chain", name="new_topic_generator")
async def new_topic_generator(state: QuestionState) -> dict:
    """새 토픽 질문 생성 노드"""
    
    current_topic_id = state.get("current_topic_id", 0)
    current_topic_count = state.get("current_topic_count", 0)
    new_topic_id = current_topic_id + 1
    
    logger.debug(f"새 토픽 질문 생성 시작 | new_topic_id={new_topic_id}")
    
    question_output = await _generate_new_topic_llm(state)
    
    generated_question = GeneratedQuestion(
        user_id = state.get("user_id"),
        session_id = state.get("session_id"),
        question_text=question_output.question_text,
        topic_id=new_topic_id,
        turn_type="main",
        is_session_ended=False,
        end_reason=None,
        is_bad_case=False,
        bad_case_feedback=None,
    )
    
    logger.info(
        f"새 토픽 질문 생성 완료 | topic_id={new_topic_id}",
        extra={
            "user_id": state.get("user_id"),
            "session_id": state.get("session_id"),
            "topic_id": new_topic_id,
            "topic_summary": question_output.topic_summary,
            "question_preview": question_output.question_text[:50],
        }
    )
    
    return {
        "generated_question": generated_question,
        "current_topic_id": new_topic_id,
        "current_topic_count": current_topic_count + 1,
        "current_follow_up_count": 0,
    }
        

@traceable(run_type="llm", name="new_topic_llm")
async def _generate_new_topic_llm(state: QuestionState) -> QuestionOutput:
    """LLM 호출하여 새 토픽 질문 생성"""
    
    llm = get_llm_provider()
    
    system_prompt = get_new_topic_system_prompt(llm.provider_name)
    user_prompt = build_new_topic_prompt(
        question_type=state.get("question_type", QuestionType.CS),
        category=state.get("category"),
        interview_history=state.get("interview_history", []),
        portfolio=state.get("portfolio"),
    )

    question_output = await llm.generate_structured(
            prompt=user_prompt,
            response_model=QuestionOutput,
            system_prompt=system_prompt,
            temperature=0.7,
        )
    
    return question_output