"""
PayPal billing provider implementation.

Uses the PayPal REST API v2 via httpx.
No external SDK required — communicates directly with the PayPal API.
"""

from typing import Optional, Dict, Any
import httpx
from src.billing.base import (
    BillingProvider,
    BillingPlan,
    BillingCustomer,
    BillingSubscription,
    BillingProviderError,
)
from src.billing.registry import BillingProviderRegistry


PAYPAL_API_BASE_SANDBOX = "https://api-m.sandbox.paypal.com"
PAYPAL_API_BASE_LIVE = "https://api-m.paypal.com"


class PayPalBillingProvider(BillingProvider):
    """PayPal billing integration using the REST API v2."""

    @property
    def provider_name(self) -> str:
        return "paypal"

    def __init__(self, config: dict):
        self.client_id = config.get("client_id", "")
        self.client_secret = config.get("client_secret", "")
        self.webhook_id = config.get("webhook_id", "")
        sandbox = config.get("sandbox", True)
        self.api_base = PAYPAL_API_BASE_SANDBOX if sandbox else PAYPAL_API_BASE_LIVE
        self._access_token: Optional[str] = None

    async def _get_access_token(self) -> str:
        if self._access_token:
            return self._access_token
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.api_base}/v1/oauth2/token",
                auth=(self.client_id, self.client_secret),
                data={"grant_type": "client_credentials"},
                headers={"Accept": "application/json"},
            )
            if resp.status_code != 200:
                raise BillingProviderError(
                    "Failed to get PayPal access token",
                    provider="paypal",
                    code="auth_failed",
                )
            data = resp.json()
            self._access_token = data.get("access_token", "")
            return self._access_token

    async def _request(
        self, method: str, path: str, json_data: Optional[dict] = None
    ) -> dict:
        token = await self._get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        async with httpx.AsyncClient() as client:
            resp = await client.request(
                method,
                f"{self.api_base}{path}",
                headers=headers,
                json=json_data,
            )
            if resp.status_code >= 400:
                try:
                    detail = resp.json()
                    message = detail.get("message", str(resp.text))
                except Exception:
                    message = resp.text
                raise BillingProviderError(
                    message, provider="paypal", code=str(resp.status_code)
                )
            if resp.status_code == 204:
                return {}
            return resp.json()

    # ── Plan / Product Management ──────────────────────────────────────────

    async def create_plan(self, plan: BillingPlan) -> BillingPlan:
        product = await self._request("POST", "/v1/catalogs/products", {
            "name": plan.name,
            "description": plan.description or "",
            "type": "DIGITAL",
            "category": "SOFTWARE",
        })

        plan_def = {
            "product_id": product["id"],
            "name": plan.name,
            "description": plan.description or "",
            "status": "ACTIVE",
        }

        if plan.interval == "one_time":
            plan_def["billing_cycles"] = [{
                "frequency": {"interval_unit": "MONTH", "interval_count": 1},
                "tenure_type": "REGULAR",
                "sequence": 1,
                "total_cycles": 1,
                "pricing_scheme": {
                    "fixed_price": {
                        "value": f"{plan.amount:.2f}",
                        "currency_code": plan.currency.upper(),
                    }
                },
            }]
            plan_def["payment_preferences"] = {
                "auto_bill_outstanding": False,
                "setup_fee_failure_action": "CANCEL",
            }
        else:
            interval_unit = "MONTH" if plan.interval == "monthly" else "YEAR"
            plan_def["billing_cycles"] = [{
                "frequency": {"interval_unit": interval_unit, "interval_count": 1},
                "tenure_type": "REGULAR",
                "sequence": 1,
                "total_cycles": 0,
                "pricing_scheme": {
                    "fixed_price": {
                        "value": f"{plan.amount:.2f}",
                        "currency_code": plan.currency.upper(),
                    }
                },
            }]
            plan_def["payment_preferences"] = {
                "auto_bill_outstanding": True,
                "setup_fee": {"value": "0", "currency_code": plan.currency.upper()},
                "setup_fee_failure_action": "CANCEL",
                "payment_failure_threshold": 3,
            }

        result = await self._request("POST", "/v1/billing/plans", plan_def)
        return BillingPlan(
            provider_plan_id=result["id"],
            name=plan.name,
            description=plan.description,
            amount=plan.amount,
            currency=plan.currency,
            interval=plan.interval,
            trial_days=plan.trial_days,
            metadata={"product_id": product["id"]},
        )

    async def update_plan(self, provider_plan_id: str, plan: BillingPlan) -> BillingPlan:
        patch = []
        if plan.name:
            patch.append({"op": "replace", "path": "/name", "value": plan.name})
        if plan.description:
            patch.append({"op": "replace", "path": "/description", "value": plan.description})

        if patch:
            await self._request("PATCH", f"/v1/billing/plans/{provider_plan_id}", patch)

        return BillingPlan(
            provider_plan_id=provider_plan_id,
            name=plan.name,
            description=plan.description,
            amount=plan.amount,
            currency=plan.currency,
            interval=plan.interval,
            trial_days=plan.trial_days,
            metadata=plan.metadata,
        )

    async def delete_plan(self, provider_plan_id: str) -> None:
        await self._request("PATCH", f"/v1/billing/plans/{provider_plan_id}", [
            {"op": "replace", "path": "/status", "value": "INACTIVE"}
        ])

    # ── Customer Management ────────────────────────────────────────────────

    async def create_customer(self, customer: BillingCustomer) -> BillingCustomer:
        body: dict = {"email_address": customer.email}
        if customer.name:
            body["name"] = {"given_name": customer.name, "surname": ""}
        result = await self._request("POST", "/v2/customer/partner-referrals", body)
        return BillingCustomer(
            provider_customer_id=result.get("id", ""),
            email=customer.email,
            name=customer.name,
            metadata=customer.metadata,
        )

    async def get_customer(self, provider_customer_id: str) -> Optional[BillingCustomer]:
        try:
            result = await self._request("GET", f"/v2/customer/partner-referrals/{provider_customer_id}")
            return BillingCustomer(
                provider_customer_id=result.get("id", ""),
                email="",
                name=result.get("name", {}).get("given_name") if result.get("name") else None,
            )
        except BillingProviderError:
            return None

    # ── Subscription Management ────────────────────────────────────────────

    async def create_subscription(
        self,
        provider_customer_id: str,
        provider_plan_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> BillingSubscription:
        body: dict = {
            "plan_id": provider_plan_id,
            "subscriber": {"email_address": metadata.get("email", "")} if metadata else {},
            "application_context": {
                "user_action": "SUBSCRIBE_NOW",
                "payment_method": {"payer_selected": "PAYPAL", "payee_preferred": "IMMEDIATE_PAYMENT_REQUIRED"},
            },
        }
        if metadata and "return_url" in metadata:
            body["application_context"]["return_url"] = metadata["return_url"]
        if metadata and "cancel_url" in metadata:
            body["application_context"]["cancel_url"] = metadata["cancel_url"]

        result = await self._request("POST", "/v1/billing/subscriptions", body)
        return BillingSubscription(
            provider_subscription_id=result["id"],
            provider_customer_id=provider_customer_id,
            provider_plan_id=provider_plan_id,
            status=result.get("status", "APPROVAL_PENDING"),
            metadata=metadata,
        )

    async def cancel_subscription(
        self,
        provider_subscription_id: str,
        at_period_end: bool = True,
    ) -> BillingSubscription:
        reason = "Cancelled by user" if at_period_end else "Immediate cancellation"
        if not at_period_end:
            await self._request("POST", f"/v1/billing/subscriptions/{provider_subscription_id}/cancel", {
                "reason": reason,
            })
        else:
            await self._request("POST", f"/v1/billing/subscriptions/{provider_subscription_id}/suspend", {
                "reason": reason,
            })

        status = "CANCELLED" if not at_period_end else "SUSPENDED"
        return BillingSubscription(
            provider_subscription_id=provider_subscription_id,
            provider_customer_id="",
            provider_plan_id="",
            status=status,
        )

    async def get_subscription(self, provider_subscription_id: str) -> Optional[BillingSubscription]:
        try:
            result = await self._request("GET", f"/v1/billing/subscriptions/{provider_subscription_id}")
            plan_id = ""
            if result.get("plan_id"):
                plan_id = result["plan_id"]

            return BillingSubscription(
                provider_subscription_id=result["id"],
                provider_customer_id="",
                provider_plan_id=plan_id,
                status=result.get("status", "UNKNOWN"),
                current_period_start=str(result.get("start_time", "")),
                current_period_end=str(result.get("next_billing_time", "")),
                cancel_at_period_end=result.get("status") == "SUSPENDED",
            )
        except BillingProviderError:
            return None

    async def update_subscription_plan(
        self,
        provider_subscription_id: str,
        new_provider_plan_id: str,
    ) -> BillingSubscription:
        result = await self._request("POST", f"/v1/billing/subscriptions/{provider_subscription_id}/revise", {
            "plan_id": new_provider_plan_id,
        })
        return BillingSubscription(
            provider_subscription_id=result["id"],
            provider_customer_id="",
            provider_plan_id=new_provider_plan_id,
            status=result.get("status", "APPROVAL_PENDING"),
        )

    # ── Webhook Handling ───────────────────────────────────────────────────

    async def verify_webhook_signature(
        self,
        raw_body: bytes,
        webhook_headers: dict,
    ) -> bool:
        """Verify the webhook signature via PayPal's verification API.

        Required headers (from PayPal webhook POST):
          - auth_algo       (PAYPAL-AUTH-ALGO)
          - cert_url        (PAYPAL-CERT-URL)
          - transmission_id (PAYPAL-TRANSMISSION-ID)
          - transmission_sig (PAYPAL-TRANSMISSION-SIG)
          - transmission_time (PAYPAL-TRANSMISSION-TIME)

        Returns True if verification succeeds, False otherwise.
        """
        if not self.webhook_id:
            return False

        auth_algo = webhook_headers.get("auth_algo", "")
        cert_url = webhook_headers.get("cert_url", "")
        transmission_id = webhook_headers.get("transmission_id", "")
        transmission_sig = webhook_headers.get("transmission_sig", "")
        transmission_time = webhook_headers.get("transmission_time", "")

        if not all([auth_algo, cert_url, transmission_id, transmission_sig, transmission_time]):
            return False

        import json
        raw_body_str = raw_body.decode("utf-8")
        try:
            webhook_event = json.loads(raw_body_str)
        except json.JSONDecodeError:
            return False

        verification_body = {
            "auth_algo": auth_algo,
            "cert_url": cert_url,
            "transmission_id": transmission_id,
            "transmission_sig": transmission_sig,
            "transmission_time": transmission_time,
            "webhook_id": self.webhook_id,
            "webhook_event": webhook_event,
        }

        token = await self._get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.api_base}/v1/notifications/verify-webhook-signature",
                headers=headers,
                json=verification_body,
            )

        if resp.status_code != 200:
            return False

        result = resp.json()
        return result.get("verification_status") == "SUCCESS"

    async def handle_webhook(
        self,
        raw_body: bytes,
        signature_header: Optional[str] = None,
    ) -> Dict[str, Any]:
        import json as _json

        if not self.webhook_id:
            raise BillingProviderError(
                "PayPal webhook_id not configured",
                provider="paypal",
                code="webhook_not_configured",
            )

        if not signature_header:
            raise BillingProviderError(
                "Missing PayPal webhook signature headers",
                provider="paypal",
                code="webhook_signature_missing",
            )

        webhook_headers = _json.loads(signature_header)

        verified = await self.verify_webhook_signature(raw_body, webhook_headers)
        if not verified:
            raise BillingProviderError(
                "PayPal webhook signature verification failed",
                provider="paypal",
                code="webhook_signature_invalid",
            )

        body_str = raw_body.decode("utf-8")
        body = _json.loads(body_str)

        event_type = body.get("event_type", "unknown")
        resource = body.get("resource", {})

        mapped_type = event_type
        if event_type == "BILLING.SUBSCRIPTION.CREATED":
            mapped_type = "checkout.session.completed"
        elif event_type == "BILLING.SUBSCRIPTION.UPDATED":
            mapped_type = "customer.subscription.updated"
        elif event_type == "BILLING.SUBSCRIPTION.CANCELLED":
            mapped_type = "customer.subscription.deleted"
        elif event_type == "PAYMENT.SALE.COMPLETED":
            mapped_type = "invoice.paid"

        return {
            "event_type": mapped_type,
            "event_id": body.get("id", ""),
            "data": resource,
        }

    # ── Checkout / Hosted Pages ───────────────────────────────────────────

    async def create_checkout_session(
        self,
        provider_customer_id: str,
        provider_plan_id: str,
        success_url: str,
        cancel_url: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        body = {
            "plan_id": provider_plan_id,
            "application_context": {
                "return_url": success_url,
                "cancel_url": cancel_url,
                "user_action": "SUBSCRIBE_NOW",
                "brand_name": (metadata or {}).get("brand_name", ""),
            },
        }

        result = await self._request("POST", "/v1/billing/subscriptions", body)

        for link in result.get("links", []):
            if link.get("rel") == "approve":
                return link["href"]

        raise BillingProviderError(
            "No approval URL in PayPal response",
            provider="paypal",
            code="no_approval_url",
        )


BillingProviderRegistry.register("paypal", PayPalBillingProvider)
