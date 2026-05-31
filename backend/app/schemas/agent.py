"""Pydantic schemas for agent run + evaluation resources."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Agent Step
# ---------------------------------------------------------------------------


class AgentStepCreate(BaseModel):
    step_index: int = 0
    step_type: str = "tool_call"
    tool_name: str = ""
    tool_input: dict[str, Any] = Field(default_factory=dict)
    tool_output: str = ""
    reasoning_text: str = ""


class AgentStepOut(BaseModel):
    id: uuid.UUID
    agent_run_id: uuid.UUID
    step_index: int
    step_type: str
    tool_name: str
    tool_input: dict[str, Any]
    tool_output: str
    reasoning_text: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Agent Run
# ---------------------------------------------------------------------------


class AgentRunCreate(BaseModel):
    agent_name: str
    query: str
    final_answer: str = ""
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    status: str = "completed"
    # Optional inline steps; creates AgentStep rows
    steps: list[AgentStepCreate] = Field(default_factory=list)


class AgentRunOut(BaseModel):
    id: uuid.UUID
    agent_name: str
    query: str
    final_answer: str
    tool_calls: list[Any]
    step_count: int
    status: str
    created_at: datetime
    created_by: str

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Agent Eval
# ---------------------------------------------------------------------------


class AgentEvalCreate(BaseModel):
    dataset_key: uuid.UUID
    agent_name: str


class AgentEvalOut(BaseModel):
    id: uuid.UUID
    dataset_key: uuid.UUID
    agent_name: str
    query_count: int
    mean_tool_accuracy: float
    mean_trajectory_score: float
    mean_task_completion: float
    status: str
    created_at: datetime
    created_by: str

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Agent Eval Result
# ---------------------------------------------------------------------------


class AgentEvalResultOut(BaseModel):
    id: uuid.UUID
    agent_eval_id: uuid.UUID
    query_text: str
    expected_answer: str
    actual_answer: str
    expected_tools: list[Any]
    actual_tools: list[Any]
    tool_call_accuracy: float
    trajectory_score: float
    task_completion_score: float
    created_at: datetime

    model_config = {"from_attributes": True}
