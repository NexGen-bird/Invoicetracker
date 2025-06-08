import os
import logging
from typing import Optional, List
from supabase import create_client, Client
from models import Receipt

logger = logging.getLogger(__name__)

class ReceiptDatabase:
    """Database interface for receipt operations"""
    
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL", "")
        self.supabase_key = os.getenv("SUPABASE_KEY", "")
        
        if not self.supabase_url or not self.supabase_key:
            logger.warning("Supabase credentials not found in environment variables")
            self.client: Optional[Client] = None
        else:
            self.client: Client = create_client(self.supabase_url, self.supabase_key)
    
    def get_receipt_by_id(self, receipt_id: str) -> Optional[Receipt]:
        """Get receipt by ID"""
        if not self.client:
            return None
        
        try:
            response = self.client.table("receipts").select("*").eq("receipt_id", receipt_id).execute()
            
            if response.data:
                return Receipt.from_dict(response.data[0])
            return None
            
        except Exception as e:
            logger.error(f"Error fetching receipt {receipt_id}: {str(e)}")
            return None
    
    def verify_receipt_phone(self, receipt_id: str, phone_number: str) -> Optional[Receipt]:
        """Verify receipt ID and phone number combination"""
        receipt = self.get_receipt_by_id(receipt_id)
        
        if not receipt:
            return None
        
        # Clean both phone numbers for comparison
        cleaned_input_phone = ''.join(filter(str.isdigit, phone_number))
        cleaned_stored_phone = ''.join(filter(str.isdigit, receipt.customer_phone))
        
        if cleaned_input_phone == cleaned_stored_phone:
            return receipt
        
        return None
    
    def create_receipt(self, receipt: Receipt) -> bool:
        """Create a new receipt (for testing purposes)"""
        if not self.client:
            return False
        
        try:
            response = self.client.table("receipts").insert(receipt.to_dict()).execute()
            return len(response.data) > 0
            
        except Exception as e:
            logger.error(f"Error creating receipt: {str(e)}")
            return False
    
    def is_connected(self) -> bool:
        """Check if database connection is available"""
        return self.client is not None
