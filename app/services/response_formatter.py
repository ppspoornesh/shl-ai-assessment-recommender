from __future__ import annotations

from app.models.chat import Recommendation


class ResponseFormatter:
    """Formats a response payload into a consistent response shape.

    This component is intentionally limited to presentation formatting. It does not
    retrieve, rank, or generate recommendations.
    """

    def format(self, *, reply: str, recommendations: list[Recommendation], end_of_conversation: bool = False) -> dict[str, object]:
        return {
            "reply": reply,
            "recommendations": [recommendation.model_dump() for recommendation in recommendations],
            "end_of_conversation": end_of_conversation,
        }
