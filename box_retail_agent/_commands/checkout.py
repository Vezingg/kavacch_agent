"""Checkout command - send order to factory for pricing."""
import fastworkflow
from fastworkflow.train.generate_synthetic import generate_diverse_utterances
from pydantic import BaseModel, Field
from typing import List, Optional
from ..appliation.notifications import WhatsAppService


class ProductSelection(BaseModel):
    """A single product selection."""
    product_name: str = Field(description="Name of the product (e.g., 'Top Window Box', 'MDF Board')")
    size: Optional[str] = Field(default=None, description="Size of the product (e.g., '10x10x5 inch')")
    color: Optional[str] = Field(default=None, description="Color if applicable (e.g., 'White', 'Golden')")
    quantity: Optional[int] = Field(default=None, description="Quantity required")
    customization: Optional[str] = Field(default=None, description="Any customization details (e.g., 'Foil stamping with logo')")


class Signature:
    """Process checkout with pricing options."""
    
    class Input(BaseModel):
        customer_name: str = Field(
            description="Name of the customer or business",
            examples=["Sharma Bakery", "Sweet Delights Cafe"]
        )
        customer_phone: str = Field(
            description="Customer's WhatsApp phone number",
            examples=["919876543210", "9876543210"]
        )
        products: List[ProductSelection] = Field(
            description="List of selected products with their details",
            examples=[[
                {"product_name": "Top Window Box", "size": "10x10x5 inch", "quantity": 500},
                {"product_name": "MDF Board", "size": "12 inch", "color": "Golden", "quantity": 200}
            ]]
        )

    
    plain_utterances = [
        "checkout",
        "place order",
        "finalize order",
        "submit order",
        "I want to order",
        "send my order",
        "confirm order",
        "proceed to checkout",
        "I'm ready to order",
        "complete my order",
        "get pricing",
        "send pricing request",
    ]
    
    @staticmethod
    def generate_utterances(
        workflow: fastworkflow.Workflow, 
        command_name: str
    ) -> list[str]:
        return [
            command_name.split("/")[-1].lower().replace("_", " ")
        ] + generate_diverse_utterances(
            Signature.plain_utterances, 
            command_name
        )


class ResponseGenerator:
    """Process checkout - send order to factory for pricing."""
    
    def process_command(
        self,
        workflow: fastworkflow.Workflow,
        input: Signature.Input
    ) -> str:
        whatsapp_service = WhatsAppService()
        
        # Convert products to dict format
        products = [p.model_dump() for p in input.products]
        
        if not products:
            return (
                "No products selected for checkout. Please tell me which products "
                "you'd like to order with their sizes, colors, and quantities."
            )
        
        # Get order summary
        order_summary = whatsapp_service.format_order_summary(products)
        
        # Send order to factory for pricing (synchronous)
        sent = whatsapp_service.send_order_to_factory(
            customer_name=input.customer_name,
            customer_phone=input.customer_phone,
            products=products
        )
        
        if sent:
            return (
                f"{order_summary}\n\n"
                "✅ Your order has been sent to our team!\n\n"
                "We'll discuss the pricing and get back to you shortly on WhatsApp "
                "with the best quote for your order.\n\n"
                "Thank you for choosing Kalash Packaging! 🙏"
            )
        else:
            return (
                f"{order_summary}\n\n"
                "⚠️ There was an issue sending your request. "
                f"Please contact us directly at: {whatsapp_service.get_factory_number()}"
            )
    
    def __call__(
        self,
        workflow: fastworkflow.Workflow,
        command: str,
        command_parameters: Signature.Input,
    ) -> fastworkflow.CommandOutput:
        response = self.process_command(workflow, command_parameters)
        
        return fastworkflow.CommandOutput(
            workflow_id=workflow.id,
            command_responses=[
                fastworkflow.CommandResponse(response=response)
            ]
        )
