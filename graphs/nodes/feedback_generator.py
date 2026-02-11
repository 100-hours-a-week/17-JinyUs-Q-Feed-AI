# graphs/nodes/feedback_generator.py
from graphs.feedback.state import FeedbackGraphState
from schemas.feedback import FeedbackContent
from prompts.feedback import build_feedback_prompt, get_feedback_system_prompt
from core.dependencies import get_llm_provider

async def feedback_generator(
    state: FeedbackGraphState
) -> dict:
    """피드백 텍스트 생성 노드"""
    
    llm = get_llm_provider()
    
    interview_text = "\n\n".join(
        f"Q: {turn.question}\nA: {turn.answer_text}"
        for turn in state["interview_history"]
    )
    
    system_prompt = get_feedback_system_prompt(llm.provider_name)
    
    result = await llm.generate_structured(
        prompt=build_feedback_prompt(
            question_type=state["question_type"].value,
            category=state["category"].value if state["category"] else None,
            interview_text=interview_text,
            rubric_result=state["rubric_result"],
        ),
        response_model=FeedbackContent,
        system_prompt=system_prompt,
        temperature=0.3,
        max_tokens=4000,
    )
    
    return {
        "feedback": [result],
        "current_step": "feedback_generator",
    }