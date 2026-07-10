"""
Billing-specific database models for payments, invoices, and webhook event logging.

Not to be confused with the abstract BillingPlan/BillingSubscription/BillingCustomer
dataclasses in src/billing/base.py — these are SQLModel tables for persistence.
"""

from decimal import Decimal
from typing import Optional, Dict, Any
from sqlalchemy import Column, ForeignKey, Integer, String, Text, JSON, Float, DateTime, Index, Numeric
from sqlmodel import Field, SQLModel


# ── Webhook Event Log (TASK 6) ────────────────────────────────────────────


WEBHOOK_EVENT_STATUSES = ["received", "processed", "failed", "skipped"]


class WebhookEventLog(SQLModel, table=True):
    """Persistent log of every incoming billing webhook event."""
    id: Optional[int] = Field(default=None, primary_key=True)
    provider: str = Field(sa_column=Column(String(20)))
    event_id: str = Field(sa_column=Column(String(255), index=True))
    event_type: str = Field(sa_column=Column(String(100)))
    status: str = "received"
    idempotency_key: Optional[str] = Field(default=None, sa_column=Column(String(255), index=True))
    raw_body: Optional[str] = Field(default=None, sa_column=Column(Text))
    error_message: Optional[str] = Field(default=None, sa_column=Column(Text))
    retry_count: int = 0
    created_at: str = ""
    processed_at: Optional[str] = None


# ── Payment / Invoice Records (TASK 5) ────────────────────────────────────


PAYMENT_STATUSES = ["succeeded", "failed", "refunded", "pending"]


class Payment(SQLModel, table=True):
    __table_args__ = (
        Index("ix_payment_org_status", "org_id", "status"),
    )
    """A single payment or invoice received from a billing provider."""
    id: Optional[int] = Field(default=None, primary_key=True)
    org_id: int = Field(
        sa_column=Column(Integer, ForeignKey("organization.id", ondelete="CASCADE"), index=True)
    )
    community_id: int = Field(
        sa_column=Column(Integer, ForeignKey("community.id", ondelete="CASCADE"), index=True)
    )
    member_id: int = Field(
        sa_column=Column(Integer, ForeignKey("communitymember.id", ondelete="SET NULL"), nullable=True, index=True)
    )
    user_id: int = Field(
        sa_column=Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), index=True)
    )
    plan_id: int = Field(
        sa_column=Column(Integer, ForeignKey("membershipplan.id", ondelete="SET NULL"), nullable=True, index=True)
    )
    provider: str = Field(sa_column=Column(String(20)))
    provider_payment_id: str = Field(sa_column=Column(String(255), index=True))
    provider_invoice_id: Optional[str] = Field(default=None, sa_column=Column(String(255)))
    amount: Decimal = Field(default=Decimal("0.00"), sa_column=Column(Numeric(10, 2)))
    currency: str = "usd"
    status: str = "succeeded"
    billing_period_start: Optional[str] = None
    billing_period_end: Optional[str] = None
    invoice_url: Optional[str] = Field(default=None, sa_column=Column(String(1024)))
    invoice_pdf: Optional[str] = Field(default=None, sa_column=Column(String(1024)))
    metadata: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON, nullable=True))
    created_at: str = ""
    updated_at: str = ""


class PaymentRead(SQLModel):
    id: int
    amount: Decimal
    currency: str
    status: str
    provider: str
    provider_payment_id: str
    provider_invoice_id: Optional[str] = None
    billing_period_start: Optional[str] = None
    billing_period_end: Optional[str] = None
    invoice_url: Optional[str] = None
    invoice_pdf: Optional[str] = None
    created_at: str
