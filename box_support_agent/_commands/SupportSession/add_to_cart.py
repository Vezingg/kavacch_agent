"""Add items to the shopping cart"""

from typing import Optional
import fastworkflow
from fastworkflow.train.generate_synthetic import generate_diverse_utterances
from pydantic import BaseModel, Field

from ...application.support_session import SupportSession


class Signature:
    """Add product items to the customer's cart"""

    class Input(BaseModel):
        product_type: str = Field(
            description="Type of product (Window Box, MDF Board, Drum Board, or Cutlery Kit)",
            examples=['Window Box', 'MDF Board', 'Drum Board', 'Cutlery Kit'],
        )
        product_name: str = Field(
            description="Specific product name/size/specification",
            examples=['8x8x5 Top Window', '10x10x5 L Window', '12 inch Black MDF', '10x10 White Drum Board', 'Standard Cutlery Kit'],
        )
        quantity: Optional[int] = Field(
            description="Quantity to order - REQUIRED field. If customer doesn't specify quantity, ASK them for it. Do not assume a default quantity.",
            examples=[100, 500, 1000, 250, 2000],
            default=None,
            gt=0
        )
        notes: str = Field(
            description="Any additional notes or customization requirements",
            examples=['with foil stamping', 'need branding', 'pastel pink color', 'rush delivery needed'],
            default=""
        )

    class Output(BaseModel):
        success: bool = Field(description="Whether the item was added successfully")
        message: str = Field(description="Response message")

    plain_utterances = [
        "I want to order 100 window boxes 8x8x5",
        "add 500 MDF boards 12 inch black to my cart",
        "I need 1000 cutlery kits with custom branding",
        "add to cart 200 drum boards 10x10 white",
        "I'd like 300 top window boxes 10x10x5 in pastel colors",
        "order 250 L window boxes 12x12x8",
        "I want window boxes 8x8x5",
        "add MDF boards to cart",
        "I need some cutlery kits",
        "can I order drum boards 10x10",
    ]

    @staticmethod
    def generate_utterances(workflow: fastworkflow.Workflow, command_name: str) -> list[str]:
        """Generate training utterances for LLM-based intent matching"""
        return [
            command_name.split('/')[-1].lower().replace('_', ' ')
        ] + generate_diverse_utterances(Signature.plain_utterances, command_name)


class ResponseGenerator:
    """Add items to the customer's cart"""

    def _process_command(self, workflow: fastworkflow.Workflow, input: Signature.Input) -> Signature.Output:
        session: SupportSession = workflow.command_context_for_response_generation

        # Check if quantity is missing
        if input.quantity is None or input.quantity <= 0:
            message = f"I'd be happy to add **{input.product_type} ({input.product_name})** to your cart!\n\n"
            message += "📦 **How many would you like to order?**\n\n"
            message += "Please let me know the quantity, and I'll add it to your cart right away."
            return Signature.Output(success=False, message=message)

        success = session.add_to_cart(
            product_type=input.product_type,
            product_name=input.product_name,
            quantity=input.quantity,
            notes=input.notes
        )

        if success:
            message = f"✅ Added {input.quantity} x {input.product_type} ({input.product_name}) to your cart!"
            if input.notes:
                message += f"\n   📝 Notes: {input.notes}"
            message += f"\n\nYou now have {len(session.cart)} item(s) in your cart."
            message += "\n\n**What would you like to do next?**\n• Continue browsing and add more items\n• Ask questions about products\n• View your cart\n• Proceed to checkout when ready"
        else:
            message = "❌ Sorry, there was an error adding the item to your cart. Please try again."

        return Signature.Output(success=success, message=message)

    def __call__(
        self,
        workflow: fastworkflow.Workflow,
        command: str,
        command_parameters: Signature.Input
    ) -> fastworkflow.CommandOutput:
        """The framework will call this function to process the command"""
        output = self._process_command(workflow, command_parameters)

        return fastworkflow.CommandOutput(
            workflow_id=workflow.id,
            command_responses=[
                fastworkflow.CommandResponse(response=output.message)
            ]
        )
