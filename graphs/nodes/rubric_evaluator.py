from graphs.feedback.state import FeedbackGraphState
from schemas.feedback import RubricEvaluationResult
from prompts.rubric import get_rubric_system_prompt, build_rubric_prompt
from core.dependencies import get_llm_provider

async def rubric_evaluator(state: FeedbackGraphState) -> dict:
    """루브릭 기반 평가 노드"""

    llm = get_llm_provider()
    
    interview_text = "\n\n".join(
        f"Q: {turn.question}\nA: {turn.answer_text}"
        for turn in state["interview_history"]
    )
    
    system_prompt = get_rubric_system_prompt(llm.provider_name)

    result = await llm.generate_structured(
        prompt = build_rubric_prompt(
            question_type=state['question_type'],
            category=state['category'],
            interview_text=interview_text
        ),
        response_model=RubricEvaluationResult,
        system_prompt=system_prompt,
        temperature=0.3,
        max_tokens=4000
    )

    return {
        "rubric_result": result,
        "current_step": "rubric_evaluator",
    }