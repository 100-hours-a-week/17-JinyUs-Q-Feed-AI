from langgraph.graph import StateGraph, END

from .state import FeedbackGraphState
from graphs.nodes.rubric_evaluator import rubric_evaluator
from graphs.nodes.keyword_checker import keyword_checker
from graphs.nodes.feedback_generator import feedback_generator
# from nodes.send_callback import send_callback # 추후 비동기 도입 시 사용

def build_feedback_graph():
    graph = StateGraph(FeedbackGraphState)

    graph.add_node("keyword_checker", keyword_checker)
    graph.add_node("rubric_evaluator", rubric_evaluator)
    graph.add_node("feedback_generator", feedback_generator)

    # 엣지 연결 (순차 실행)
    graph.set_entry_point("keyword_checker")
    graph.add_edge("keyword_checker", "rubric_evaluator")
    graph.add_edge("rubric_evaluator", "feedback_generator")
    graph.add_edge("feedback_generator", END)

    return graph.compile()


async def run_feedback_pipeline(initial_state: FeedbackGraphState) -> FeedbackGraphState:
    """피드백 파이프라인 실행"""
    graph = build_feedback_graph()
    result = await graph.ainvoke(initial_state)
    return result