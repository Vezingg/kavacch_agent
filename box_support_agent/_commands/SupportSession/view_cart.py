"""View items in the shopping cart"""

import fastworkflow
from fastworkflow.train.generate_synthetic import generate_diverse_utterances
from pydantic import BaseModel

from ...application.support_session import SupportSession


class Signature:
    """View all items currently in the customer's cart"""

    class Input(BaseModel):
        pass  # No input parameters needed

    plain_utterances = [
        "show me my cart",
        "what's in my cart",
        "view my order",
        "what have I added",
        "show my items",
        "let me see what I've ordered",
    ]

    @staticmethod
    def generate_utterances(workflow: fastworkflow.Workflow, command_name: str) -> list[str]:
        """Generate training utterances for LLM-based intent matching"""
        return [
            command_name.split('/')[-1].lower().replace('_', ' ')
        ] + generate_diverse_utterances(Signature.plain_utterances, command_name)


class ResponseGenerator:
    """Display the current cart contents"""

    def _process_command(self, workflow: fastworkflow.Workflow) -> str:
        session: SupportSession = workflow.command_context_for_response_generation
        return session.view_cart()

    def __call__(
        self,
        workflow: fastworkflow.Workflow,
        command: str,
        command_parameters: Signature.Input
    ) -> fastworkflow.CommandOutput:
        """The framework will call this function to process the command"""
        cart_view = self._process_command(workflow)

        additional_message = ""
        session: SupportSession = workflow.command_context_for_response_generation

        if session.cart:
            additional_message = "\n\n**What would you like to do next?**\n• Add more items\n• Proceed to checkout"

        response = cart_view + additional_message

        return fastworkflow.CommandOutput(
            workflow_id=workflow.id,
            command_responses=[
                fastworkflow.CommandResponse(response=response)
            ]
        )
