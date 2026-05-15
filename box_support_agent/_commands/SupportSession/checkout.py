"""Checkout and complete the order"""

import json
import urllib.request
import fastworkflow
from fastworkflow.train.generate_synthetic import generate_diverse_utterances
from pydantic import BaseModel, Field

from ...application.support_session import SupportSession

# Cloud app runs on port 8080 in the same container
_CLOUD_APP_URL = "http://localhost:8080"


class Signature:
    """Complete the order and generate order summary"""

    class Input(BaseModel):
        customer_name: str = Field(
            description="Full name of the customer for the order",
            examples=['Raj Patel', 'Anita Shah', 'John Smith'],
        )

    class Output(BaseModel):
        success: bool = Field(description="Whether checkout was successful")
        order_summary: str = Field(description="Complete order summary")

    plain_utterances = [
        "I'm ready to checkout",
        "proceed with my order",
        "complete my order",
        "I want to finalize this",
        "checkout please",
        "ready to place order",
    ]

    @staticmethod
    def generate_utterances(workflow: fastworkflow.Workflow, command_name: str) -> list[str]:
        """Generate training utterances for LLM-based intent matching"""
        return [
            command_name.split('/')[-1].lower().replace('_', ' ')
        ] + generate_diverse_utterances(Signature.plain_utterances, command_name)


class ResponseGenerator:
    """Process checkout and generate order summary. IMPORTANT: Never mention or estimate delivery time, shipping timeline, lead time, or dispatch schedule — these are not defined and will be communicated separately by the Kavacch team after the order is confirmed."""

    def _process_command(self, workflow: fastworkflow.Workflow, input: Signature.Input) -> Signature.Output:
        session: SupportSession = workflow.command_context_for_response_generation

        if not session.cart:
            return Signature.Output(
                success=False,
                order_summary="❌ Your cart is empty. Please add items before checking out."
            )

        # Set the customer name on the session before generating the summary
        session.customer_name = input.customer_name

        # Generate the order summary
        order_summary = session.get_checkout_summary()

        # Notify cloud_app to forward the order to the factory for pricing.
        # Done here (before LLM reformats the response) so the factory always receives
        # the structured order data regardless of how the LLM rewrites the reply.
        try:
            products = [
                {
                    "product_type": item.product_type,
                    "product_name": item.product_name,
                    "quantity": item.quantity,
                    "notes": item.notes,
                }
                for item in session.cart
            ]
            payload = json.dumps({
                "customer_phone": session.customer_phone,
                "customer_name": input.customer_name,
                "order_summary": order_summary,
                "products": products,
            }).encode()
            req = urllib.request.Request(
                f"{_CLOUD_APP_URL}/api/checkout_complete",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            urllib.request.urlopen(req, timeout=5)
        except Exception:
            pass  # Never fail the checkout if cloud_app notification fails

        # Clear the cart after checkout
        session.clear_cart()

        return Signature.Output(
            success=True,
            order_summary=order_summary
        )

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
                fastworkflow.CommandResponse(response=output.order_summary)
            ]
        )
