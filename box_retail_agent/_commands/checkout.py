"""Checkout command - send order to factory for pricing."""
import fastworkflow
from fastworkflow.train.generate_synthetic import generate_diverse_utterances
from pydantic import BaseModel, Field
from typing import List, Optional
from ..appliation.notifications import WhatsAppService


class ProductSelection(BaseModel):
    """A single product selection."""
    product_name: str = Field(description="Name of the product (e.g., 'Top Window Box', 'MDF Board', 'Drum Board', 'Cutlery Kit')")
    size: Optional[str] = Field(
        default=None,
        description=(
            "Size of the product. "
            "Top Window Box sizes: 8x8x5 inch, 10x10x5 inch, 12x12x5 inch. "
            "L Window Box sizes: 10x10x5, 8x8x8, 10x10x8, 12x12x8. "
            "MDF Board sizes: 6 inch, 7 inch, 8 inch, 9 inch, 10 inch, 12 inch, 14 inch, 16 inch, 18 inch, 20 inch, 14x19 inch. "
            "Drum Board sizes: 10x10, 12x12, 14x14. "
            "If the customer says '12 inch' or '12\"' for a drum board, use '12x12'. "
            "If the customer says '10 inch' or '10\"' for a drum board, use '10x10'. "
            "If the customer says '14 inch' or '14\"' for a drum board, use '14x14'. "
            "IMPORTANT — AMBIGUOUS SIZE RULE: If the customer says only '10 inch' or '10' for a window box (L or Top), "
            "you MUST ask: 'Which 10 inch size do you need? Reply:\n1. 10x10x5 inch\n2. 10x10x8 inch' "
            "Do NOT guess or default to either. Wait for their reply (1 or 2) before filling this field. "
            "Same rule applies to any size where multiple depth options exist for the same width."
        )
    )
    color: Optional[str] = Field(
        default=None,
        description="Color if applicable. Drum Board colors: Black, White, Golden. MDF Board colors: White, Black, Golden, Pastel colours."
    )
    quantity: Optional[int] = Field(
        default=None,
        description=(
            "Quantity of this product required. "
            "Leave as null/None if the customer has NOT explicitly stated a number. "
            "Do NOT guess, assume, or default to any number. "
            "Only populate this after the customer says an actual number like '100', '500 pieces', etc."
        ),
        examples=[100, 250, 500]
    )
    customization: Optional[str] = Field(default=None, description="Any customization details (e.g., 'Foil stamping with logo')")


class Signature:
    """
    Submit the customer's order to the factory for pricing.

    ONLY invoke this command when the customer has explicitly shown purchase intent using phrases like:
    "checkout", "place order", "I want to order", "I'm ready to order", "confirm order",
    "send my order", "get pricing", "this is what I want", "I'll take", "I want to buy".

    Do NOT invoke this command — and do NOT ask for name, phone, or order details — just because
    the customer asked a product question (e.g. "tell me more", "what sizes", "what colors").
    Only ask for checkout information after the customer has clearly signalled they want to order.

    STRICT OUTPUT RULES:
    - Return the command output EXACTLY as provided. Do NOT add, rephrase, or expand anything.
    - Do NOT append "Next Steps", "To Order", suggestions, follow-up questions, or any extra text.
    - Do NOT add formatting, bullet summaries, or closing remarks beyond what the command returns.

    Once the customer signals purchase intent, collect in this order:
    1. ALWAYS ask for customer_name first if not already provided — "May I have your name or business name?"
    2. customer_phone — extract from the [Customer's WhatsApp number: ...] context prefix. NEVER ask for it.
    3. For each product — if the size is ambiguous (e.g. customer said '10 inch' for a window box that has
       both 10x10x5 and 10x10x8), ask: 'Which 10 inch size do you need?\n1. 10x10x5 inch\n2. 10x10x8 inch'
       Do NOT assume a size. Wait for the customer to reply 1 or 2.
    4. ALWAYS ask for quantity for each product — 'How many pieces do you need?' — if not already stated.
    5. products — extract from the conversation history only after size and quantity are confirmed.

    Do NOT submit the order until you have: customer_name, confirmed size (not ambiguous), and quantity for every product.
    Extract product details (name, size, color, quantity) from the full conversation history.
    Use the phone number the customer messages from if they do not provide one.
    Do NOT invoke this for cutlery kits or MDF boards unless the customer specifically asked for them.
    """
    
    class Input(BaseModel):
        customer_name: str = Field(
            description="Name of the customer or business. ALWAYS ask the customer for this before submitting — 'May I have your name or business name?'. Do not proceed without it.",
            examples=["Sharma Bakery", "Sweet Delights Cafe"]
        )
        customer_phone: str = Field(
            description=(
                "Customer's WhatsApp phone number. "
                "Every message includes '[Customer\'s WhatsApp number: <phone>]' at the top — "
                "extract the phone from there. NEVER ask the customer to provide their phone number."
            ),
            examples=["919876543210", "9876543210"]
        )
        products: List[ProductSelection] = Field(
            description="List of selected products with their details extracted from the conversation",
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
        "my name is John and my number is 919876543210",
        "John Doe, 919876543210",
        "yes confirm the order",
        "yes go ahead",
        "please send the order",
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
        
        # Hard guard: always ask for quantity if missing
        # B2B packaging orders are never 1 unit — quantity=1 means the LLM guessed
        missing_qty = [p["product_name"] for p in products if not p.get("quantity") or p["quantity"] <= 1]
        if missing_qty:
            items = ", ".join(missing_qty)
            return f"How many pieces/units do you need for: {items}? Please share the quantity so I can send your order."
        
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
