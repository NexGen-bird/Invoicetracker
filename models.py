from typing import Optional
from datetime import datetime

class Receipt:
    """Receipt model for type hinting and validation"""
    
    def __init__(
        self,
        receipt_id: str,
        customer_name: str,
        customer_phone: str,
        customer_email: Optional[str] = None,
        payment_amount: int = 0,
        description: Optional[str] = None,
        payment_method: Optional[str] = None,
        status: str = "completed",
        created_at: Optional[datetime] = None
    ):
        self.receipt_id = receipt_id
        self.customer_name = customer_name
        self.customer_phone = customer_phone
        self.customer_email = customer_email
        self.payment_amount = payment_amount
        self.description = description
        self.payment_method = payment_method
        self.status = status
        self.created_at = created_at or datetime.now()
    
    def to_dict(self):
        """Convert receipt to dictionary"""
        return {
            "receipt_id": self.receipt_id,
            "customer_name": self.customer_name,
            "customer_phone": self.customer_phone,
            "customer_email": self.customer_email,
            "payment_amount": self.amount,
            "description": self.description,
            "payment_method": self.payment_method,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        """Create receipt from dictionary"""
        return cls(
            receipt_id=data.get("receipt_id", ""),
            customer_name=data.get("customer_name", ""),
            customer_phone=data.get("customer_phone", ""),
            customer_email=data.get("customer_email"),
            payment_amount=int(data.get("payment_amount", 0)),
            description=data.get("description"),
            payment_method=data.get("payment_mode"),
            status=data.get("status", "completed"),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None
        )
