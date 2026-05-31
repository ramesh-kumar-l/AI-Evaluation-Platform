"""SQLAlchemy ORM models (one entity per file).

Importing this package registers all models on ``Base.metadata`` so Alembic autogeneration and
``create_all`` see them. Add new entity modules to the imports below as their phases land.
"""

from app.models.approval import Approval
from app.models.audit_event import AuditEvent
from app.models.base import Base
from app.models.benchmark import Benchmark
from app.models.comparison import Comparison
from app.models.dataset import Dataset
from app.models.dataset_policy import DatasetPolicy
from app.models.evaluation import Evaluation
from app.models.evaluation_result import EvaluationResult
from app.models.gate_decision import GateDecision
from app.models.metric import Metric
from app.models.prompt import Prompt
from app.models.provider import Model, Provider
from app.models.release_gate import ReleaseGate
from app.models.run import InferenceRun

__all__ = [
    "Approval",
    "AuditEvent",
    "Base",
    "Benchmark",
    "Comparison",
    "Dataset",
    "DatasetPolicy",
    "Evaluation",
    "EvaluationResult",
    "GateDecision",
    "InferenceRun",
    "Metric",
    "Model",
    "Prompt",
    "Provider",
    "ReleaseGate",
]
