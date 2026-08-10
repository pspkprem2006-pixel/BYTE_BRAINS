"""Models package.

Importing every model here registers its table metadata on ``Base``,
which is what Alembic uses for autogenerate.
"""

from app.core.database import Base
from app.models.material import Material, ProcessingStatus
from app.models.progress import UserProgress
from app.models.quiz_attempt import QuizAttempt
from app.models.study_plan import StudyPlan
from app.models.study_task import StudyTask
from app.models.subject import Subject
from app.models.topic import Topic
from app.models.user import User

__all__ = [
    "Base",
    "Material",
    "ProcessingStatus",
    "QuizAttempt",
    "StudyPlan",
    "StudyTask",
    "Subject",
    "Topic",
    "User",
    "UserProgress",
]