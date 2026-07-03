from app.models.chat import Message
from app.services.intent_detector import IntentDetector


def test_detects_initial_request_intent() -> None:
    detector = IntentDetector()
    conversation = [
        Message(role="user", content="I need a senior software engineer for our finance team."),
    ]

    intent = detector.detect_intent(conversation)

    assert intent == "initial_request"


def test_detects_refinement_intent() -> None:
    detector = IntentDetector()
    conversation = [
        Message(role="user", content="We need a product manager."),
        Message(role="assistant", content="I can help with that."),
        Message(role="user", content="Actually, make it junior instead."),
    ]

    intent = detector.detect_intent(conversation)

    assert intent == "refine_request"


def test_detects_comparison_intent() -> None:
    detector = IntentDetector()
    conversation = [
        Message(role="user", content="Please compare the top two assessments for this role."),
    ]

    intent = detector.detect_intent(conversation)

    assert intent == "compare_options"


def test_detects_clarification_intent() -> None:
    detector = IntentDetector()
    conversation = [
        Message(role="user", content="I am not sure which industry or experience level to choose."),
    ]

    intent = detector.detect_intent(conversation)

    assert intent == "clarify_requirements"
