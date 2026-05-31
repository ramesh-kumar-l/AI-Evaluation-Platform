"""SQLAlchemy ORM models (one entity per file).

Importing this package registers all models on ``Base.metadata`` so Alembic autogeneration and
``create_all`` see them. Add new entity modules to the imports below as their phases land.
"""

from app.models.agent_eval import AgentEval
from app.models.agent_eval_result import AgentEvalResult
from app.models.agent_run import AgentRun
from app.models.agent_step import AgentStep
from app.models.approval import Approval
from app.models.audit_event import AuditEvent
from app.models.base import Base
from app.models.benchmark import Benchmark
from app.models.comparison import Comparison
from app.models.dataset import Dataset
from app.models.dataset_policy import DatasetPolicy
from app.models.eval_job import EvalJob
from app.models.eval_schedule import EvalSchedule
from app.models.evaluation import Evaluation
from app.models.evaluation_result import EvaluationResult
from app.models.experiment import Experiment
from app.models.gate_decision import GateDecision
from app.models.metric import Metric
from app.models.prompt import Prompt
from app.models.provider import Model, Provider
from app.models.rag_corpus import RagCorpus
from app.models.rag_document import RagDocument
from app.models.rag_eval import RagEval
from app.models.rag_eval_result import RagEvalResult
from app.models.release_gate import ReleaseGate
from app.models.run import InferenceRun

__all__ = [
    "AgentEval",
    "EvalJob",
    "EvalSchedule",
    "Experiment",
    "AgentEvalResult",
    "AgentRun",
    "AgentStep",
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
    "RagCorpus",
    "RagDocument",
    "RagEval",
    "RagEvalResult",
    "ReleaseGate",
]
