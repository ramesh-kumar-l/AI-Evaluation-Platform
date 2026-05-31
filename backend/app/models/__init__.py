"""SQLAlchemy ORM models (one entity per file).

Importing this package registers all models on ``Base.metadata`` so Alembic autogeneration and
``create_all`` see them. Add new entity modules to the imports below as their phases land.
"""

from app.models.audit_event import AuditEvent
from app.models.base import Base
from app.models.dataset import Dataset
from app.models.evaluation import Evaluation
from app.models.evaluation_result import EvaluationResult
from app.models.metric import Metric
from app.models.prompt import Prompt
from app.models.provider import Model, Provider
from app.models.run import InferenceRun

__all__ = [
    "AuditEvent",
    "Base",
    "Dataset",
    "Evaluation",
    "EvaluationResult",
    "InferenceRun",
    "Metric",
    "Model",
    "Prompt",
    "Provider",
]
