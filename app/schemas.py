from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class SignUpRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    is_premium: bool
    premium_until: datetime | None
    free_messages_used: int
    free_messages_remaining: int
    can_chat: bool

    class Config:
        from_attributes = True


class CreateOrderRequest(BaseModel):
    method: str = Field(..., pattern="^(upi|netbanking|google_pay)$")


class VerifyPaymentRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class PaymentResponse(BaseModel):
    id: int
    amount: int
    currency: str
    method: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
