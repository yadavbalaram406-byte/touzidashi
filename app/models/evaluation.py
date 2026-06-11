import json
from datetime import datetime
from sqlalchemy import Integer, String, Float, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Evaluation(Base):
    __tablename__ = "evaluations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_name: Mapped[str] = mapped_column(String(200), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(20), nullable=False)

    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    text_length: Mapped[int | None] = mapped_column(Integer, nullable=True)

    llm_provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    llm_model: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # JSON fields stored as TEXT
    project_intro: Mapped[str | None] = mapped_column(Text, nullable=True)
    scores_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    suggestions_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Denormalized score columns for easy querying
    score_team: Mapped[float | None] = mapped_column(Float, nullable=True)
    score_pain_point: Mapped[float | None] = mapped_column(Float, nullable=True)
    score_traction: Mapped[float | None] = mapped_column(Float, nullable=True)
    score_moat: Mapped[float | None] = mapped_column(Float, nullable=True)
    final_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    decision: Mapped[str | None] = mapped_column(String(30), nullable=True)

    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def get_project_intro(self) -> dict | None:
        if self.project_intro:
            return json.loads(self.project_intro)
        return None

    def get_scores(self) -> dict | None:
        if self.scores_json:
            return json.loads(self.scores_json)
        return None

    def get_suggestions(self) -> dict | None:
        if self.suggestions_json:
            return json.loads(self.suggestions_json)
        return None
