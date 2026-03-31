"""
WhatsApp notification service for checkout flow.
Uses WhatsApp Cloud API (Meta Business API).
Integrates with cloud_app for pending order tracking.
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Optional
import httpx

logger = logging.getLogger("box_retail_notifications")
logger.setLevel(logging.INFO)  # Explicitly set level (basicConfig may already be called)

# Ensure logs go to stderr (captured by Cloud Run)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


# --- LOAD ENV FILES ---
def load_env_files():
    """Load environment variables from fastworkflow env files."""
    base_dir = Path(__file__).parent.parent  # box_retail_agent/
    env_files = [
        base_dir / "fastworkflow.env",
        base_dir / "fastworkflow.passwords.env"
    ]
    
    for env_file in env_files:
        if env_file.exists():
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, _, value = line.partition("=")
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        if key not in os.environ:
                            os.environ[key] = value

load_env_files()


# Cloud App URL for pending order management
CLOUD_APP_URL = os.getenv("CLOUD_APP_URL", "http://localhost:8080")


class WhatsAppService:
    """Send WhatsApp notifications using Meta Cloud API."""
    
    def __init__(self):
        self.phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
        self.access_token = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
        self.factory_number = os.getenv("FACTORY_WHATSAPP", "919725201616")  # Without +
    
    def send_message(self, to_number: str, message: str) -> bool:
        """Send a WhatsApp message to a phone number (synchronous)."""
        url = f"https://graph.facebook.com/v18.0/{self.phone_number_id}/messages"
        
        payload = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "text",
            "text": {"body": message}
        }
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        try:
            with httpx.Client(timeout=30) as client:
                response = client.post(url, headers=headers, json=payload)
                if response.status_code == 200:
                    logger.info(f"Notification sent to {to_number}")
                    return True
                else:
                    logger.error(f"WhatsApp API error ({response.status_code}): {response.text}")
                    return False
        except Exception as e:
            logger.error(f"WhatsApp send error: {e}")
            return False
    
    def send_order_to_factory(
        self,
        customer_name: str,
        customer_phone: str,
        products: List[Dict]
    ) -> bool:
        """Send order details to factory for pricing (synchronous)."""
        message = self._format_order_for_factory(customer_name, customer_phone, products)
        order_summary = self.format_order_summary(products)
        
        # First, register the pending order with cloud_app
        self._register_pending_order(customer_phone, order_summary, products)
        
        # Then send to factory
        return self.send_message(self.factory_number, message)
    
    def _register_pending_order(
        self,
        customer_phone: str,
        order_summary: str,
        products: List[Dict]
    ) -> bool:
        """Register pending order with cloud_app for pricing flow tracking (synchronous)."""
        try:
            with httpx.Client(timeout=10) as client:
                response = client.post(
                    f"{CLOUD_APP_URL}/api/add_pending_order",
                    json={
                        "customer_phone": customer_phone,
                        "order_summary": order_summary,
                        "products": products
                    }
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Error registering pending order: {e}")
            # Continue even if registration fails - order will still be sent
            return False
    
    def _format_order_for_factory(
        self,
        customer_name: str,
        customer_phone: str,
        products: List[Dict]
    ) -> str:
        """Format order details for factory WhatsApp."""
        lines = [
            "📦 New Pricing Request",
            "",
            f"👤 Customer: {customer_name}",
            f"📞 Phone: {customer_phone}",
            "",
            "Selected Products:",
            "-" * 20,
        ]
        
        for i, product in enumerate(products, 1):
            lines.append(f"{i}. {product.get('product_name', 'Product')}")
            details = []
            if product.get('size'):
                details.append(f"Size: {product['size']}")
            if product.get('color'):
                details.append(f"Color: {product['color']}")
            if product.get('quantity'):
                details.append(f"Qty: {product['quantity']}")
            if product.get('customization'):
                details.append(f"Custom: {product['customization']}")
            if details:
                lines.append(f"   {', '.join(details)}")
        
        lines.extend([
            "",
            "-" * 20,
            "⚡ Reply with the TOTAL PRICE for this order.",
            "(Your reply will be automatically sent to the customer)",
            f"",
            f"Customer phone: {customer_phone}"
        ])
        
        return "\n".join(lines)
    
    def format_order_summary(self, products: List[Dict]) -> str:
        """Format order summary for customer."""
        lines = ["📋 Your Order Summary:", ""]
        
        for i, product in enumerate(products, 1):
            lines.append(f"{i}. {product.get('product_name', 'Product')}")
            details = []
            if product.get('size'):
                details.append(f"Size: {product['size']}")
            if product.get('color'):
                details.append(f"Color: {product['color']}")
            if product.get('quantity'):
                details.append(f"Qty: {product['quantity']}")
            if product.get('customization'):
                details.append(f"Custom: {product['customization']}")
            if details:
                lines.append(f"   {', '.join(details)}")
        
        return "\n".join(lines)
    
    @classmethod
    def get_factory_number(cls) -> str:
        """Get the factory WhatsApp number."""
        return os.getenv("FACTORY_WHATSAPP", "919725201616")
