from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from razorpay import Client

from app.auth import get_current_user
from app.database import get_db
from app.models import Payment, User
from app.payment_service import PaymentServiceError, complete_payment, create_payment_order
from app.schemas import CreateOrderRequest, PaymentResponse, VerifyPaymentRequest

router = APIRouter(prefix="/api/payments", tags=["payments"])


@router.post("/create-order")
def create_order(
    payload: CreateOrderRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    try:
        return create_payment_order(db, user, payload.method)
    except PaymentServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/verify", response_model=PaymentResponse)
def verify_payment(
    payload: VerifyPaymentRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PaymentResponse:
    try:
        payment = complete_payment(
            db,
            user,
            payload.razorpay_order_id,
            payload.razorpay_payment_id,
            payload.razorpay_signature,
        )
        return PaymentResponse.model_validate(payment)
    except PaymentServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/history", response_model=list[PaymentResponse])
def payment_history(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[PaymentResponse]:
    payments = (
        db.query(Payment)
        .filter(Payment.user_id == user.id)
        .order_by(Payment.created_at.desc())
        .limit(20)
        .all()
    )
    return [PaymentResponse.model_validate(payment) for payment in payments]
