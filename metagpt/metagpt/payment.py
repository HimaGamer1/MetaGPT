#!/usr/bin/env python3
"""
Stub Stripe payment endpoint integration.
Switch to real stripe with environment variables and webhook signature verification.
"""
from typing import Optional

try:
    from fastapi import FastAPI, HTTPException, Header, Request
except Exception:
    FastAPI = None  # type: ignore
    HTTPException = Exception  # type: ignore
    Header = lambda *a, **k: None  # type: ignore
    Request = object  # type: ignore

# Optional FastAPI app
if FastAPI:
    app = FastAPI(title="Payments")

    @app.post("/stripe/webhook")
    async def stripe_webhook(request: Request, stripe_signature: Optional[str] = Header(None)):
        # NOTE: Replace with real verification using stripe.Webhook.construct_event
        payload = await request.body()
        if not stripe_signature:
            raise HTTPException(status_code=400, detail="Missing Stripe-Signature header")
        # Simulate minimal success path
        return {"received": True, "len": len(payload)}

    @app.post("/stripe/checkout/session")
    async def create_checkout_session():
        # NOTE: Replace with stripe.checkout.Session.create
        return {"id": "cs_test_stub", "url": "https://checkout.stripe.com/pay/cs_test_stub"}

if __name__ == "__main__":
    print("payment.py stub loaded. Use FastAPI to run endpoints.")
