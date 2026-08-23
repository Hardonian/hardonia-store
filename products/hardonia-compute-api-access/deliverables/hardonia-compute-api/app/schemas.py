"""Pydantic schemas for the Hardonia Compute API."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class JobType(str, Enum):
    chat = "chat"
    image = "image"
    workflow = "workflow"


class JobStatus(str, Enum):
    pending = "pending"
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"
    timeout = "timeout"


class CreditStatus(str, Enum):
    active = "active"
    exhausted = "exhausted"
    expired = "expired"
    refunded = "refunded"


# ── Jobs ──────────────────────────────────────────────────────────────────────


class JobCreate(BaseModel):
    job_type: JobType = Field(..., description="Type of compute job")
    model: Optional[str] = Field(None, description="Model name for chat jobs")
    prompt: Optional[str] = Field(None, description="Prompt text for chat/image jobs")
    workflow: Optional[Dict[str, Any]] = Field(None, description="ComfyUI workflow JSON for image/workflow jobs")
    params: Dict[str, Any] = Field(default_factory=dict, description="Extra job parameters")
    callback_url: Optional[str] = Field(None, description="Optional webhook URL for completion notification")

    @field_validator("prompt")
    @classmethod
    def prompt_not_empty_if_required(cls, v, info):
        if info.data.get("job_type") in (JobType.chat,) and not v:
            raise ValueError("prompt is required for chat jobs")
        return v

    @field_validator("workflow")
    @classmethod
    def workflow_not_empty_if_required(cls, v, info):
        if info.data.get("job_type") in (JobType.image, JobType.workflow) and not v:
            raise ValueError("workflow is required for image/workflow jobs")
        return v


class Job(BaseModel):
    job_id: str
    api_key: str
    job_type: JobType
    status: JobStatus
    model: Optional[str] = None
    prompt: str = ""
    workflow: Dict[str, Any] = Field(default_factory=dict)
    params: Dict[str, Any] = Field(default_factory=dict)
    callback_url: Optional[str] = None
    result: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    cost_credits: int = 0
    credits_before: int = 0
    credits_after: int = 0
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    external_prompt_id: Optional[str] = None


class JobList(BaseModel):
    jobs: List[Job]
    count: int
    page: int
    page_size: int


# ── Credits ───────────────────────────────────────────────────────────────────


class CreditPackage(str, Enum):
    starter = "starter"
    growth = "growth"
    scale = "scale"
    enterprise = "enterprise"


class CreditTransactionType(str, Enum):
    purchase = "purchase"
    consumption = "consumption"
    refund = "refund"
    bonus = "bonus"
    adjustment = "adjustment"


class CreditPurchase(BaseModel):
    package: CreditPackage = Field(..., description="Prepaid credit package")
    payment_method_id: Optional[str] = Field(None, description="Stripe payment method ID")
    idempotency_key: Optional[str] = Field(None, description="Idempotency key for duplicate prevention")


class CreditTopUp(BaseModel):
    amount_cents: int = Field(..., ge=100, description="Top-up amount in cents, minimum $1")
    idempotency_key: Optional[str] = Field(None, description="Idempotency key")


class CreditAdjustment(BaseModel):
    amount: int = Field(..., description="Positive or negative credit adjustment")
    reason: str = Field(..., description="Reason for adjustment")
    ref_id: Optional[str] = Field(None, description="External reference ID")


class CreditTransaction(BaseModel):
    transaction_id: str
    api_key: str
    type: CreditTransactionType
    amount: int
    balance_after: int
    ref_type: Optional[str] = None
    ref_id: Optional[str] = None
    reason: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class CreditBalance(BaseModel):
    api_key: str
    balance: int
    total_purchased: int
    total_consumed: int
    last_transaction_at: Optional[datetime] = None


# ── Webhooks ──────────────────────────────────────────────────────────────────


class WebhookEventType(str, Enum):
    checkout_completed = "checkout.session.completed"
    invoice_paid = "invoice.paid"
    subscription_updated = "customer.subscription.updated"
    subscription_deleted = "customer.subscription.deleted"


class WebhookEvent(BaseModel):
    event_id: str
    event_type: WebhookEventType
    api_key: str
    amount_cents: int
    currency: str = "cad"
    metadata: Dict[str, Any] = Field(default_factory=dict)
    processed: bool = False
    error: Optional[str] = None
    created_at: datetime
    processed_at: Optional[datetime] = None


# ── Delivery ──────────────────────────────────────────────────────────────────


class DeliveryToken(BaseModel):
    token: str
    job_id: str
    api_key: str
    expires_at: datetime
    download_url: str
    created_at: datetime


class DeliveryRequest(BaseModel):
    job_id: str = Field(..., description="Job ID to deliver results for")


# ── Admin ─────────────────────────────────────────────────────────────────────


class ApiKeyCreate(BaseModel):
    email: str = Field(..., description="Customer email")
    plan: str = Field("free", description="Plan name")
    initial_credits: int = Field(0, ge=0, description="Initial credit balance")
    quota_tokens: int = Field(100000, ge=0, description="Token quota")
    rate_per_min: int = Field(30, ge=1, description="Rate limit per minute")


class ApiKeyUpdate(BaseModel):
    plan: Optional[str] = None
    active: Optional[bool] = None
    quota_tokens: Optional[int] = Field(None, ge=0)
    rate_per_min: Optional[int] = Field(None, ge=1)


# ── Health ────────────────────────────────────────────────────────────────────


class HealthCheck(BaseModel):
    service: str
    status: str
    detail: Optional[str] = None
    ts: datetime


class HealthResponse(BaseModel):
    status: str
    checks: List[HealthCheck]
    ts: datetime
