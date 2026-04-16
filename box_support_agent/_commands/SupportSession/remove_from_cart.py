"""Remove items from the shopping cart"""

import fastworkflow
from fastworkflow.train.generate_synthetic import generate_diverse_utterances
from pydantic import BaseModel, Field

from ...application.support_session import SupportSession


class Signature:
    """Remove a specific item from the customer's cart by position"""

    class Input(BaseModel):
        item_number: int = Field(
            description="The position/number of the item to remove from cart (starting from 1)",
            examples=[1, 2, 3],
            ge=1
        )

    class Output(BaseModel):
        success: bool = Field(description="Whether the item was removed successfully")
        message: str = Field(description="Response message")

    plain_utterances = [
        "remove item 1 from cart",
        "delete the first item",
        "remove the second item from my cart",
        "take out item number 3",
        "delete item 1",
    ]

    @staticmethod
    def generate_utterances(workflow: fastworkflow.Workflow, command_name: str) -> list[str]:
        """Generate training utterances for LLM-based intent matching"""
        return [
            command_name.split('/')[-1].lower().replace('_', ' ')
        ] + generate_diverse_utterances(Signature.plain_utterances, command_name)


class ResponseGenerator:
    """Remove items from the customer's cart"""

    def _process_command(self, workflow: fastworkflow.Workflow, input: Signature.Input) -> Signature.Output:
        session: SupportSession = workflow.command_context_for_response_generation

        if not session.cart:
            return Signature.Output(
                success=False,
                message="❌ Your cart is empty. There's nothing to remove."
            )

        if input.item_number > len(session.cart):
            return Signature.Output(
                success=False,
                message=f"❌ Item number {input.item_number} doesn't exist. You only have {len(session.cart)} item(s) in your cart."
            )

        removed_item = session.cart[input.item_number - 1]
        success = session.remove_from_cart(input.item_number)

        if success:
            message = f"✅ Removed: {removed_item.product_type} - {removed_item.product_name} (x{removed_item.quantity})"

            if session.cart:
                message += f"\n\nYou now have {len(session.cart)} item(s) remaining in your cart."
            else:
                message += "\n\nYour cart is now empty."
        else:
            message = "❌ Sorry, there was an error removing the item. Please try again."

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
