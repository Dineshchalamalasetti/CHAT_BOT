from __future__ import annotations

import hmac
import hashlib
import uuid
from razorpay import Client

import razorpay 
from sqlalchemy.orm import Session

from app.config import (
    PREMIUM_PLAN_AMOUNT_PAISE,
    PREMIUM_PLAN_DAYS,
    RAZORPAY_KEY_ID,
    RAZORPAY_KEY_SECRET,
)
from app.models import Payment, User


class PaymentServiceError(Exception):
    pass


def _get_client() -> razorpay.Client:
    if not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET:
        raise PaymentServiceError(
            "Razorpay is not configured. Add RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET to .env. "
            "Sign up at https://dashboard.razorpay.com/"
        )
    return razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))


def create_payment_order(db: Session, user: User, method: str) -> dict:
    if method not in {"upi", "netbanking", "google_pay"}:
        raise PaymentServiceError("Invalid payment method.")

    client = _get_client()
    receipt = f"chat_{user.id}_{uuid.uuid4().hex[:10]}"

    order = client.order.create(
        {
            "amount": PREMIUM_PLAN_AMOUNT_PAISE,
            "currency": "INR",
            "receipt": receipt,
            "payment_capture": 1,
            "notes": {
                "user_id": str(user.id),
                "plan": "premium_monthly",
                "method": method,
            },
        }
    )

    payment = Payment(
        user_id=user.id,
        amount=PREMIUM_PLAN_AMOUNT_PAISE,
        currency="INR",
        method=method,
        razorpay_order_id=order["id"],
        status="created",
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)

    return {
        "order_id": order["id"],
        "amount": order["amount"],
        "currency": order["currency"],
        "key_id": RAZORPAY_KEY_ID,
        "payment_id": payment.id,
        "plan_days": PREMIUM_PLAN_DAYS,
        "user_name": user.full_name,
        "user_email": user.email,
        "method": method,
    }


def verify_payment_signature(order_id: str, payment_id: str, signature: str) -> bool:
    if not RAZORPAY_KEY_SECRET:
        return False

    body = f"{order_id}|{payment_id}".encode()
    expected = hmac.new(RAZORPAY_KEY_SECRET.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def complete_payment(
    db: Session,
    user: User,
    order_id: str,
    razorpay_payment_id: str,
    signature: str,
) -> Payment:
    if not verify_payment_signature(order_id, razorpay_payment_id, signature):
        raise PaymentServiceError("Payment verification failed. Invalid signature.")

    payment = (
        db.query(Payment)
        .filter(Payment.razorpay_order_id == order_id, Payment.user_id == user.id)
        .first()
    )
    if payment is None:
        raise PaymentServiceError("Payment order not found.")

    if payment.status == "paid":
        return payment

    payment.razorpay_payment_id = razorpay_payment_id
    payment.status = "paid"

    from app.auth import activate_premium

    activate_premium(user, PREMIUM_PLAN_DAYS)
    db.commit()
    db.refresh(payment)
    return payment
