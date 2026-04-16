"""Clear all items from the shopping cart"""

import fastworkflow
from fastworkflow.train.generate_synthetic import generate_diverse_utterances
from pydantic import BaseModel, Field

from ...application.support_session import SupportSession


class Signature:
    """Clear all items from the cart and start fresh"""

    class Input(BaseModel):
        pass  # No input parameters needed

    plain_utterances = [
        "clear my cart",
        "empty my cart",
        "remove all items",
        "start over with my cart",
        "delete everything from cart",
        "clear all items",
    ]

    @staticmethod
    def generate_utterances(workflow: fastworkflow.Workflow, command_name: str) -> list[str]:
        """Generate training utterances for LLM-based intent matching"""
        return [
            command_name.split('/')[-1].lower().replace('_', ' ')
        ] + generate_diverse_utterances(Signature.plain_utterances, command_name)


class ResponseGenerator:
    """Clear all items from the cart"""

    def _process_command(self, workflow: fastworkflow.Workflow) -> str:
        session: SupportSession = workflow.command_context_for_response_generation

        if not session.cart:
            return "ℹ️ Your cart is already empty."

        item_count = len(session.cart)
        session.clear_cart()

        return f"✅ Cart cleared! Removed {item_count} item(s).\n\nYour cart is now empty. Feel free to browse our products and add new items whenever you're ready!"

    def __call__(
        self,
        workflow: fastworkflow.Workflow,
        command: str,
        command_parameters: Signature.Input
    ) -> fastworkflow.CommandOutput:
        """The framework will call this function to process the command"""
        message = self._process_command(workflow)

        return fastworkflow.CommandOutput(
            workflow_id=workflow.id,
            command_responses=[
                fastworkflow.CommandResponse(response=message)
            ]
        )
